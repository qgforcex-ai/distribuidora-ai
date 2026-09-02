from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import bindparam, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file(PROJECT_ROOT / ".env")

from app.database import SessionLocal  # noqa: E402


REQUIRED_COLUMNS = {
    "codigo": ["cod", "codigo", "codigo produto", "codigo_produto", "cod produto", "cod_produto", "sku"],
    "cv_nab": ["cv/nab", "cv nab", "cv_nab", "cesta a", "cesta_a"],
    "cesta": ["cesta", "cesta b", "cesta_b"],
}

DESCRIPTION_ALIASES = [
    "descricao",
    "descricao produto",
    "descricao_produto",
    "produto",
    "item",
    "nome produto",
    "nome_produto",
]

EMPTY_MARKERS = {"", "nan", "none", "null", "nat"}


@dataclass
class Report:
    produtos_encontrados: int = 0
    produtos_criados: int = 0
    cestas_encontradas: int = 0
    cestas_criadas: int = 0
    relacionamentos_criados: int = 0
    relacionamentos_existentes: int = 0
    linhas_ignoradas: int = 0
    erros: int = 0
    produtos_que_seriam_criados: list[dict[str, str]] = field(default_factory=list)
    cestas_que_seriam_criadas: list[dict[str, str]] = field(default_factory=list)
    inconsistencias: list[str] = field(default_factory=list)


def normalize_header(value: Any) -> str:
    text_value = str(value or "").strip().lower()
    text_value = re.sub(r"[_\-]+", " ", text_value)
    text_value = re.sub(r"\s+", " ", text_value)
    return text_value


def find_column(columns: list[str], aliases: list[str]) -> str | None:
    normalized = {normalize_header(column): column for column in columns}
    for alias in aliases:
        found = normalized.get(normalize_header(alias))
        if found is not None:
            return found
    return None


def normalize_code(value: Any) -> str:
    if pd.isna(value):
        return ""

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    if isinstance(value, int):
        return str(value)

    text_value = str(value).strip()
    if not text_value:
        return ""

    decimal_match = re.fullmatch(r"(\d+)\.0+", text_value)
    if decimal_match:
        return decimal_match.group(1)

    return text_value


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""

    text_value = str(value).strip()
    if text_value.lower() in EMPTY_MARKERS:
        return ""

    return re.sub(r"\s+", " ", text_value)


def resolve_file(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_file():
        return path.resolve()

    candidates = [
        Path.cwd() / path_value,
        PROJECT_ROOT / path_value,
        Path.home() / "Downloads" / path_value,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    raise FileNotFoundError(f"Arquivo nao encontrado: {path_value}")


def read_excel_rows(path: Path) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    workbook = pd.ExcelFile(path)
    if not workbook.sheet_names:
        raise RuntimeError("A planilha nao possui abas.")

    sheet_name = workbook.sheet_names[0]
    dataframe = pd.read_excel(path, sheet_name=sheet_name, dtype=object)
    columns = [str(column).strip() for column in dataframe.columns]
    dataframe.columns = columns

    mapping: dict[str, str] = {}
    for canonical, aliases in REQUIRED_COLUMNS.items():
        column = find_column(columns, aliases)
        if column is None:
            raise RuntimeError(
                f"Coluna obrigatoria nao encontrada para {canonical}. "
                f"Colunas lidas: {', '.join(columns)}"
            )
        mapping[canonical] = column

    description_column = find_column(columns, DESCRIPTION_ALIASES)
    if description_column is not None:
        mapping["descricao"] = description_column

    return dataframe, mapping, workbook.sheet_names


def query_existing_products(session, codes: set[str]) -> dict[str, int]:
    if not codes:
        return {}

    rows = session.execute(
        text("SELECT id, codigo FROM produtos WHERE codigo IN :codes").bindparams(
            bindparam("codes", expanding=True)
        ),
        {"codes": tuple(codes)},
    ).mappings()
    return {str(row["codigo"]): int(row["id"]) for row in rows}


def query_existing_cestas(session, names: set[str]) -> dict[str, int]:
    if not names:
        return {}

    rows = session.execute(
        text("SELECT id, nome FROM cestas WHERE nome IN :names").bindparams(
            bindparam("names", expanding=True)
        ),
        {"names": tuple(names)},
    ).mappings()
    return {str(row["nome"]): int(row["id"]) for row in rows}


def query_existing_relationships(session, pairs: set[tuple[int, int]]) -> set[tuple[int, int]]:
    if not pairs:
        return set()

    cesta_ids = tuple({pair[0] for pair in pairs})
    produto_ids = tuple({pair[1] for pair in pairs})
    rows = session.execute(
        text(
            """
            SELECT cesta_id, produto_id
            FROM cesta_produto_itens
            WHERE cesta_id IN :cesta_ids
              AND produto_id IN :produto_ids
            """
        ).bindparams(
            bindparam("cesta_ids", expanding=True),
            bindparam("produto_ids", expanding=True),
        ),
        {"cesta_ids": cesta_ids, "produto_ids": produto_ids},
    ).mappings()
    existing = {(int(row["cesta_id"]), int(row["produto_id"])) for row in rows}
    return existing.intersection(pairs)


def build_excel_payload(dataframe: pd.DataFrame, mapping: dict[str, str], report: Report) -> tuple[dict[str, str], dict[str, str], set[tuple[str, str]]]:
    products: dict[str, str] = {}
    baskets: dict[str, str] = {}
    relationships: set[tuple[str, str]] = set()

    if "descricao" not in mapping:
        report.inconsistencias.append(
            "A planilha nao possui coluna de descricao; produtos novos usarao descricao tecnica 'Produto {codigo}'."
        )

    for index, row in dataframe.iterrows():
        codigo = normalize_code(row[mapping["codigo"]])
        if not codigo:
            report.linhas_ignoradas += 1
            report.inconsistencias.append(f"Linha {index + 2}: codigo vazio.")
            continue

        descricao = clean_text(row[mapping["descricao"]]) if "descricao" in mapping else ""
        products.setdefault(codigo, descricao or f"Produto {codigo}")

        valid_classifications = 0
        for canonical, tipo in [("cv_nab", "CV/NAB"), ("cesta", "CESTA")]:
            nome = clean_text(row[mapping[canonical]])
            if not nome:
                continue
            valid_classifications += 1
            baskets.setdefault(nome, tipo)
            relationships.add((codigo, nome))

        if valid_classifications == 0:
            report.linhas_ignoradas += 1
            report.inconsistencias.append(f"Linha {index + 2}: sem classificacao CV/NAB/CESTA_A ou CESTA/CESTA_B valida.")

    return products, baskets, relationships


def insert_product(session, codigo: str, descricao: str) -> int:
    session.execute(
        text(
            """
            INSERT INTO produtos (codigo, descricao, categoria, preco)
            VALUES (:codigo, :descricao, :categoria, :preco)
            """
        ),
        {
            "codigo": codigo,
            "descricao": descricao,
            "categoria": "IMPORTADO",
            "preco": Decimal("0.00"),
        },
    )
    return int(session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one())


def insert_cesta(session, nome: str, tipo: str) -> int:
    session.execute(
        text("INSERT INTO cestas (nome, tipo) VALUES (:nome, :tipo)"),
        {"nome": nome, "tipo": tipo},
    )
    return int(session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one())


def run_import(path: Path, dry_run: bool) -> Report:
    dataframe, mapping, sheet_names = read_excel_rows(path)
    report = Report()
    products, baskets, relationships = build_excel_payload(dataframe, mapping, report)

    print("Arquivo Excel interpretado")
    print(f"Arquivo: {path}")
    print(f"Abas: {', '.join(sheet_names)}")
    print(f"Linhas lidas: {len(dataframe)}")
    print(f"Colunas identificadas: {', '.join(dataframe.columns)}")
    print(f"Coluna codigo: {mapping['codigo']}")
    print(f"Coluna CV/NAB/CESTA_A: {mapping['cv_nab']}")
    print(f"Coluna CESTA/CESTA_B: {mapping['cesta']}")
    print(f"Coluna descricao: {mapping.get('descricao', 'nao encontrada')}")
    print("")

    mysql_user = os.getenv("MYSQL_USER", "")
    if mysql_user.strip().lower() == "agente_readonly":
        raise RuntimeError("MYSQL_USER esta configurado como agente_readonly. Use o usuario normal da aplicacao.")

    session = SessionLocal()
    try:
        existing_products = query_existing_products(session, set(products))
        existing_baskets = query_existing_cestas(session, set(baskets))

        new_products = {
            codigo: descricao
            for codigo, descricao in products.items()
            if codigo not in existing_products
        }
        new_baskets = {
            nome: tipo
            for nome, tipo in baskets.items()
            if nome not in existing_baskets
        }

        report.produtos_encontrados = len(existing_products)
        report.produtos_criados = len(new_products)
        report.cestas_encontradas = len(existing_baskets)
        report.cestas_criadas = len(new_baskets)
        report.produtos_que_seriam_criados = [
            {"codigo": codigo, "descricao": descricao}
            for codigo, descricao in sorted(new_products.items())
        ]
        report.cestas_que_seriam_criadas = [
            {"nome": nome, "tipo": tipo}
            for nome, tipo in sorted(new_baskets.items())
        ]

        if dry_run:
            report.relacionamentos_criados = len(relationships)
            report.relacionamentos_existentes = 0

            known_product_ids = existing_products
            known_basket_ids = existing_baskets
            checkable_pairs = {
                (known_basket_ids[cesta], known_product_ids[codigo])
                for codigo, cesta in relationships
                if codigo in known_product_ids and cesta in known_basket_ids
            }
            existing_pairs = query_existing_relationships(session, checkable_pairs)
            report.relacionamentos_existentes = len(existing_pairs)
            report.relacionamentos_criados = len(relationships) - len(existing_pairs)
            session.rollback()
            return report

        for codigo, descricao in new_products.items():
            existing_products[codigo] = insert_product(session, codigo, descricao)

        for nome, tipo in new_baskets.items():
            existing_baskets[nome] = insert_cesta(session, nome, tipo)

        relationship_ids = {
            (existing_baskets[cesta], existing_products[codigo])
            for codigo, cesta in relationships
        }
        existing_relationships = query_existing_relationships(session, relationship_ids)
        new_relationships = relationship_ids - existing_relationships

        for cesta_id, produto_id in sorted(new_relationships):
            session.execute(
                text(
                    """
                    INSERT INTO cesta_produto_itens (cesta_id, produto_id)
                    VALUES (:cesta_id, :produto_id)
                    """
                ),
                {"cesta_id": cesta_id, "produto_id": produto_id},
            )

        report.relacionamentos_existentes = len(existing_relationships)
        report.relacionamentos_criados = len(new_relationships)
        session.commit()
        return report
    except Exception:
        report.erros += 1
        session.rollback()
        raise
    finally:
        session.close()


def print_report(report: Report, dry_run: bool) -> None:
    mode = "DRY RUN - nenhuma alteracao foi gravada" if dry_run else "IMPORTACAO REAL"
    print(mode)
    print("")
    print(f"Produtos encontrados: {report.produtos_encontrados}")
    print(f"Produtos criados: {report.produtos_criados}")
    print(f"Cestas encontradas: {report.cestas_encontradas}")
    print(f"Cestas criadas: {report.cestas_criadas}")
    print(f"Relacionamentos criados: {report.relacionamentos_criados}")
    print(f"Relacionamentos ja existentes: {report.relacionamentos_existentes}")
    print(f"Linhas ignoradas: {report.linhas_ignoradas}")
    print(f"Erros: {report.erros}")

    if dry_run:
        print("")
        print("Produtos que seriam criados:")
        for product in report.produtos_que_seriam_criados[:50]:
            print(f"- {product['codigo']}: {product['descricao']}")
        if len(report.produtos_que_seriam_criados) > 50:
            print(f"... mais {len(report.produtos_que_seriam_criados) - 50} produtos")

        print("")
        print("Cestas que seriam criadas:")
        for basket in report.cestas_que_seriam_criadas:
            print(f"- {basket['nome']} ({basket['tipo']})")

    if report.inconsistencias:
        print("")
        print("Possiveis inconsistencias:")
        for inconsistency in report.inconsistencias[:50]:
            print(f"- {inconsistency}")
        if len(report.inconsistencias) > 50:
            print(f"... mais {len(report.inconsistencias) - 50} inconsistencias")


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa cestas de produtos a partir de Excel.")
    parser.add_argument("--arquivo", required=True, help="Caminho do arquivo .xlsx")
    parser.add_argument("--dry-run", action="store_true", help="Simula a importacao sem gravar no banco")
    args = parser.parse_args()

    path = resolve_file(args.arquivo)
    try:
        report = run_import(path, args.dry_run)
    except Exception as exc:
        print(f"Erro critico durante a importacao: {exc}", file=sys.stderr)
        return 1

    print_report(report, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
