from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
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
    "rn": ["cod. setor", "cod setor", "rn", "setor"],
    "codigo_pdv": ["codigo cliente", "codigo_cliente", "cod cliente", "cod_pdv", "codigo pdv"],
    "bairro": ["bairro"],
    "status_cliente": ["status do cliente", "status cliente", "status_cliente", "status"],
    "nome_fantasia": ["nome fantasia", "nome_fantasia", "fantasia", "nome"],
    "proxima_visita": ["proxima visita", "próxima visita", "proxima_visita"],
    "cidade": ["cidade"],
}

EMPTY_MARKERS = {"", "nan", "none", "null", "nat"}


@dataclass
class PdvRow:
    linha: int
    codigo_pdv: str
    nome: str
    cidade: str
    bairro: str
    status_cliente: str
    rn: str
    proxima_visita: date | None


@dataclass
class Report:
    linhas_lidas: int = 0
    codigos_unicos: int = 0
    novos_clientes: int = 0
    clientes_existentes: int = 0
    clientes_atualizados: int = 0
    clientes_sem_mudanca: int = 0
    pdvs_ausentes: int = 0
    pdvs_entrariam_na_base: int = 0
    pdvs_sairiam_da_base: int = 0
    linhas_importadas: int = 0
    erros: int = 0
    pdvs_por_rn: Counter[str] = field(default_factory=Counter)
    inconsistencias: list[str] = field(default_factory=list)
    exemplos_pdvs_ausentes: list[str] = field(default_factory=list)


def normalize_header(value: Any) -> str:
    value = str(value or "").strip().lower()
    value = value.replace("_", " ")
    return re.sub(r"\s+", " ", value)


def find_column(columns: list[str], aliases: list[str]) -> str | None:
    normalized = {normalize_header(column): column for column in columns}
    for alias in aliases:
        found = normalized.get(normalize_header(alias))
        if found is not None:
            return found
    return None


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""

    value = str(value).strip()
    if value.lower() in EMPTY_MARKERS:
        return ""

    return re.sub(r"\s+", " ", value)


def normalize_code(value: Any) -> str:
    value = clean_text(value)
    if not value:
        return ""

    if re.fullmatch(r"\d+(\.\d{3})+", value):
        return value.replace(".", "")

    decimal_match = re.fullmatch(r"(\d+)\.0+", value)
    if decimal_match:
        return decimal_match.group(1)

    return value


def parse_date(value: Any, row_number: int, report: Report) -> date | None:
    value = clean_text(value)
    if not value:
        return None

    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        report.inconsistencias.append(
            f"Linha {row_number}: Proxima Visita invalida: {value}"
        )
        return None

    return parsed.date()


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


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    dataframe = pd.read_csv(
        path,
        sep=None,
        engine="python",
        dtype=object,
        encoding="utf-8-sig",
    )
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    columns = list(dataframe.columns)

    mapping = {}
    for canonical, aliases in REQUIRED_COLUMNS.items():
        column = find_column(columns, aliases)
        if column is None:
            raise RuntimeError(
                f"Coluna obrigatoria nao encontrada para {canonical}. "
                f"Colunas lidas: {', '.join(columns)}"
            )
        mapping[canonical] = column

    return dataframe, mapping


def build_rows(dataframe: pd.DataFrame, mapping: dict[str, str], report: Report) -> list[PdvRow]:
    rows = []
    codes = []

    for index, row in dataframe.iterrows():
        row_number = index + 2
        codigo_pdv = normalize_code(row[mapping["codigo_pdv"]])
        rn = clean_text(row[mapping["rn"]])

        if not codigo_pdv:
            report.erros += 1
            report.inconsistencias.append(f"Linha {row_number}: codigo_pdv vazio.")
            continue

        if not rn:
            report.erros += 1
            report.inconsistencias.append(f"Linha {row_number}: RN vazio.")
            continue

        codes.append(codigo_pdv)
        rows.append(
            PdvRow(
                linha=row_number,
                codigo_pdv=codigo_pdv,
                nome=clean_text(row[mapping["nome_fantasia"]]),
                cidade=clean_text(row[mapping["cidade"]]),
                bairro=clean_text(row[mapping["bairro"]]),
                status_cliente=clean_text(row[mapping["status_cliente"]]),
                rn=rn,
                proxima_visita=parse_date(
                    row[mapping["proxima_visita"]],
                    row_number,
                    report,
                ),
            )
        )

    duplicates = [
        codigo
        for codigo, count in Counter(codes).items()
        if count > 1
    ]
    for codigo in sorted(duplicates):
        report.erros += 1
        report.inconsistencias.append(
            f"codigo_pdv duplicado no arquivo: {codigo}"
        )

    if duplicates:
        return []

    return rows


def query_existing_clients(session, codes: set[str]) -> dict[str, dict[str, Any]]:
    if not codes:
        return {}

    result = session.execute(
        text(
            """
            SELECT
                id,
                codigo_pdv,
                nome,
                cidade,
                bairro,
                status_cliente,
                rn,
                proxima_visita,
                base_pdv_atual
            FROM clientes
            WHERE codigo_pdv IN :codes
            """
        ).bindparams(bindparam("codes", expanding=True)),
        {"codes": tuple(codes)},
    ).mappings()
    return {
        str(row["codigo_pdv"]): dict(row)
        for row in result
    }


def query_absent_clients(session, current_codes: set[str]) -> list[str]:
    result = session.execute(
        text(
            """
            SELECT codigo_pdv
            FROM clientes
            WHERE codigo_pdv IS NOT NULL
              AND codigo_pdv <> ''
              AND base_pdv_atual = TRUE
            """
        )
    )
    existing_codes = {str(row[0]) for row in result}
    return sorted(existing_codes - current_codes)


def has_changes(row: PdvRow, current: dict[str, Any]) -> bool:
    expected = {
        "nome": row.nome or f"PDV {row.codigo_pdv}",
        "cidade": row.cidade,
        "bairro": row.bairro or None,
        "status_cliente": row.status_cliente or None,
        "rn": row.rn or None,
        "proxima_visita": row.proxima_visita,
        "base_pdv_atual": True,
    }
    for key, expected_value in expected.items():
        current_value = current.get(key)
        if current_value != expected_value:
            return True
    return False


def insert_importacao(session, path: Path, status: str, report: Report) -> int:
    session.execute(
        text(
            """
            INSERT INTO importacoes (
                tipo,
                periodo,
                arquivo_nome,
                arquivo_hash,
                status,
                linhas_lidas,
                linhas_importadas,
                erros
            )
            VALUES (
                :tipo,
                NULL,
                :arquivo_nome,
                :arquivo_hash,
                :status,
                :linhas_lidas,
                :linhas_importadas,
                :erros
            )
            """
        ),
        {
            "tipo": "BASE_PDV",
            "arquivo_nome": path.name,
            "arquivo_hash": file_hash(path),
            "status": status,
            "linhas_lidas": report.linhas_lidas,
            "linhas_importadas": report.linhas_importadas,
            "erros": report.erros,
        },
    )
    return int(session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one())


def upsert_client(session, row: PdvRow) -> None:
    session.execute(
        text(
            """
            INSERT INTO clientes (
                codigo_pdv,
                nome,
                cidade,
                bairro,
                status_cliente,
                rn,
                proxima_visita,
                base_pdv_atual,
                limite_credito
            )
            VALUES (
                :codigo_pdv,
                :nome,
                :cidade,
                :bairro,
                :status_cliente,
                :rn,
                :proxima_visita,
                TRUE,
                :limite_credito
            )
            ON DUPLICATE KEY UPDATE
                nome = VALUES(nome),
                cidade = VALUES(cidade),
                bairro = VALUES(bairro),
                status_cliente = VALUES(status_cliente),
                rn = VALUES(rn),
                proxima_visita = VALUES(proxima_visita),
                base_pdv_atual = TRUE
            """
        ),
        {
            "codigo_pdv": row.codigo_pdv,
            "nome": row.nome or f"PDV {row.codigo_pdv}",
            "cidade": row.cidade,
            "bairro": row.bairro or None,
            "status_cliente": row.status_cliente or None,
            "rn": row.rn or None,
            "proxima_visita": row.proxima_visita,
            "limite_credito": Decimal("0.00"),
        },
    )


def run_import(path: Path, dry_run: bool) -> Report:
    dataframe, mapping = read_csv(path)
    report = Report(linhas_lidas=len(dataframe))
    rows = build_rows(dataframe, mapping, report)

    report.codigos_unicos = len({row.codigo_pdv for row in rows})
    report.pdvs_por_rn = Counter(row.rn for row in rows)

    print("Arquivo CSV interpretado")
    print(f"Arquivo: {path}")
    print("Base PDV: estado atual, sem periodo")
    print(f"Linhas lidas: {report.linhas_lidas}")
    print(f"Colunas identificadas: {', '.join(dataframe.columns)}")
    print(f"Coluna codigo_pdv: {mapping['codigo_pdv']}")
    print(f"Coluna RN: {mapping['rn']}")
    print(f"Coluna nome: {mapping['nome_fantasia']}")
    print(f"Coluna cidade: {mapping['cidade']}")
    print(f"Coluna bairro: {mapping['bairro']}")
    print(f"Coluna status_cliente: {mapping['status_cliente']}")
    print(f"Coluna proxima_visita: {mapping['proxima_visita']}")
    print("")

    if report.erros:
        return report

    mysql_user = os.getenv("MYSQL_USER", "")
    if mysql_user.strip().lower() == "agente_readonly":
        raise RuntimeError(
            "MYSQL_USER esta configurado como agente_readonly. "
            "Use o usuario normal da aplicacao."
        )

    session = SessionLocal()
    try:
        codes = {row.codigo_pdv for row in rows}
        existing_clients = query_existing_clients(session, codes)
        absent_clients = query_absent_clients(session, codes)

        report.clientes_existentes = len(existing_clients)
        report.novos_clientes = len(codes) - len(existing_clients)
        report.pdvs_ausentes = len(absent_clients)
        report.pdvs_entrariam_na_base = len(codes)
        report.pdvs_sairiam_da_base = len(absent_clients)
        report.exemplos_pdvs_ausentes = absent_clients[:20]
        report.linhas_importadas = len(rows)

        for row in rows:
            current = existing_clients.get(row.codigo_pdv)
            if current and has_changes(row, current):
                report.clientes_atualizados += 1
            elif current:
                report.clientes_sem_mudanca += 1

        if dry_run:
            session.rollback()
            return report

        for row in rows:
            upsert_client(session, row)

        if absent_clients:
            session.execute(
                text(
                    """
                    UPDATE clientes
                    SET base_pdv_atual = FALSE
                    WHERE codigo_pdv IN :codes
                    """
                ).bindparams(bindparam("codes", expanding=True)),
                {"codes": tuple(absent_clients)},
            )

        insert_importacao(
            session,
            path,
            "CONCLUIDA",
            report,
        )

        session.commit()
        return report
    except Exception:
        report.erros += 1
        session.rollback()
        raise
    finally:
        session.close()


def print_report(report: Report, dry_run: bool) -> None:
    print("DRY RUN - nenhuma alteracao foi gravada" if dry_run else "IMPORTACAO REAL")
    print("")
    print(f"Linhas lidas: {report.linhas_lidas}")
    print(f"Codigos unicos: {report.codigos_unicos}")
    print(f"Novos clientes: {report.novos_clientes}")
    print(f"Clientes existentes: {report.clientes_existentes}")
    print(f"Clientes que seriam atualizados: {report.clientes_atualizados}")
    print(f"Clientes existentes sem mudanca: {report.clientes_sem_mudanca}")
    print(f"PDVs que entrariam/permaneceriam na Base: {report.pdvs_entrariam_na_base}")
    print(f"PDVs que sairiam da Base: {report.pdvs_sairiam_da_base}")
    print(f"PDVs existentes ausentes no novo arquivo: {report.pdvs_ausentes}")
    print("PDVs por RN:")
    for rn, count in sorted(report.pdvs_por_rn.items()):
        print(f"- RN {rn}: {count}")
    print(f"Inconsistencias: {len(report.inconsistencias)}")
    print(f"Erros: {report.erros}")

    if report.exemplos_pdvs_ausentes:
        print("")
        print("Exemplos de PDVs ausentes no novo arquivo:")
        for codigo_pdv in report.exemplos_pdvs_ausentes:
            print(f"- {codigo_pdv}")

    if report.inconsistencias:
        print("")
        print("Detalhes:")
        for inconsistency in report.inconsistencias:
            print(f"- {inconsistency}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Importa a Base PDV atual para clientes."
    )
    parser.add_argument("--arquivo", required=True, help="Caminho do arquivo BASE_2_RN.csv")
    parser.add_argument("--dry-run", action="store_true", help="Simula a importacao sem gravar no banco")
    args = parser.parse_args()

    try:
        path = resolve_file(args.arquivo)
        report = run_import(path, args.dry_run)
    except Exception as exc:
        print(f"Erro critico durante a importacao: {exc}", file=sys.stderr)
        return 1

    print_report(report, args.dry_run)
    return 1 if report.erros else 0


if __name__ == "__main__":
    raise SystemExit(main())
