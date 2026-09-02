from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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


ORIGEM = "BASE_VENDA"
DEFAULT_SHEET = "Planilha1"

REQUIRED_COLUMNS = {
    "codigo_pdv": ["cliente", "codigo cliente", "codigo_cliente", "cod cliente", "cod_pdv"],
    "operacao": ["operacao", "operação"],
    "codigo_produto": ["cod.produto", "cod produto", "codigo produto", "codigo_produto", "cod. produto"],
    "descricao_produto": ["desc.produto", "desc produto", "descricao produto", "descricao_produto"],
    "quantidade": ["quantidade", "qtde", "qtd"],
    "total_venda": ["total venda", "total_venda", "valor venda", "valor_venda"],
    "periodo": ["periodo", "período"],
    "fator_hl": ["fator_hl", "fator hl", "fator"],
    "volume_hl": ["volume_hl", "volume hl", "vol hl"],
}

MONTHS_PT = {
    "JAN": 1,
    "FEV": 2,
    "MAR": 3,
    "ABR": 4,
    "MAI": 5,
    "JUN": 6,
    "JUL": 7,
    "AGO": 8,
    "SET": 9,
    "OUT": 10,
    "NOV": 11,
    "DEZ": 12,
}

EMPTY_MARKERS = {"", "nan", "none", "null", "nat"}
CENT = Decimal("0.01")
QTY_PRECISION = Decimal("0.0001")
PRICE_PRECISION = Decimal("0.000001")
FACTOR_PRECISION = Decimal("0.000001")
VOLUME_HL_PRECISION = Decimal("0.000001")
HL_PRECISION = Decimal("0.01")
HL_TOLERANCE = Decimal("0.01")


@dataclass
class SaleRow:
    row_number: int
    codigo_pdv: str
    operacao: int
    codigo_produto: str
    descricao_produto: str
    quantidade: Decimal
    fator_hl: Decimal | None
    volume_hl: Decimal | None
    total_venda: Decimal
    periodo: date


@dataclass
class ProductSummary:
    codigo: str
    descricao: str
    linhas: int = 0
    valor: Decimal = Decimal("0.00")
    volume: Decimal = Decimal("0.0000")


@dataclass
class Report:
    arquivo: Path
    planilha: str
    periodo_encontrado: date | None = None
    periodos_encontrados: set[date] = field(default_factory=set)
    total_linhas_excel: int = 0
    linhas_periodo: int = 0
    operacoes: Counter[int] = field(default_factory=Counter)
    valor_por_operacao: defaultdict[int, Decimal] = field(
        default_factory=lambda: defaultdict(lambda: Decimal("0.00"))
    )
    volume_por_operacao: defaultdict[int, Decimal] = field(
        default_factory=lambda: defaultdict(lambda: Decimal("0.0000"))
    )
    quantidade_total: Decimal = Decimal("0.0000")
    volume_hl_total: Decimal = Decimal("0.00")
    volume_hl_calculado_total: Decimal = Decimal("0.00")
    diferenca_volume_hl: Decimal = Decimal("0.00")
    linhas_divergencia_volume_hl: int = 0
    linhas_sem_fator_hl: int = 0
    linhas_sem_volume_hl: int = 0
    clientes_distintos: int = 0
    clientes_base_pdv_atual: int = 0
    clientes_historicos_fora_base: int = 0
    novos_clientes_historicos: int = 0
    tamanho_base_pdv_atual: int = 0
    produtos_distintos: int = 0
    produtos_existentes: int = 0
    produtos_novos: int = 0
    produtos_sem_cesta: int = 0
    produtos_sem_fator: int = 0
    consolidacoes_venda: int = 0
    consolidacoes_item: int = 0
    linhas_quantidade_zero: int = 0
    valor_quantidade_zero: Decimal = Decimal("0.00")
    linhas_quantidade_negativa: int = 0
    valor_quantidade_negativa: Decimal = Decimal("0.00")
    linhas_valor_negativo: int = 0
    valor_negativo: Decimal = Decimal("0.00")
    codigos_cliente_vazios: int = 0
    codigos_produto_vazios: int = 0
    operacoes_invalidas: int = 0
    periodos_invalidos: int = 0
    erros: int = 0
    inconsistencias: list[str] = field(default_factory=list)
    produtos_novos_lista: dict[str, ProductSummary] = field(default_factory=dict)
    produtos_duplicados_db: dict[str, int] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)


def money(value: Decimal) -> str:
    value = value.quantize(CENT, rounding=ROUND_HALF_UP)
    if value == Decimal("-0.00"):
        value = Decimal("0.00")
    return f"R$ {value}"


def qty(value: Decimal) -> str:
    return str(value.quantize(QTY_PRECISION, rounding=ROUND_HALF_UP))


def hl(value: Decimal) -> str:
    value = value.quantize(HL_PRECISION, rounding=ROUND_HALF_UP)
    if value == Decimal("-0.00"):
        value = Decimal("0.00")
    return str(value)


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


def parse_decimal(value: Any, row_number: int, column_name: str, report: Report) -> Decimal:
    value = clean_text(value)
    if not value:
        return Decimal("0")

    normalized = value.replace("R$", "").replace(" ", "")
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")

    try:
        return Decimal(normalized)
    except InvalidOperation:
        report.erros += 1
        report.inconsistencias.append(
            f"Linha {row_number}: valor numerico invalido em {column_name}: {value}"
        )
        return Decimal("0")


def parse_operacao(value: Any, row_number: int, report: Report) -> int | None:
    value = normalize_code(value)
    if not value:
        report.operacoes_invalidas += 1
        report.inconsistencias.append(f"Linha {row_number}: operacao vazia.")
        return None

    try:
        operacao = int(value)
    except ValueError:
        report.operacoes_invalidas += 1
        report.inconsistencias.append(f"Linha {row_number}: operacao invalida: {value}")
        return None

    if operacao not in {1, 2}:
        report.operacoes_invalidas += 1
        report.inconsistencias.append(f"Linha {row_number}: operacao nao reconhecida: {operacao}")
        return None

    return operacao


def parse_period(value: Any, row_number: int, report: Report) -> date | None:
    raw = clean_text(value)
    if not raw:
        report.periodos_invalidos += 1
        report.inconsistencias.append(f"Linha {row_number}: periodo vazio.")
        return None

    normalized = raw.upper().strip()
    normalized = normalized.replace("/", "-").replace("_", "-").replace(" ", "-")

    match = re.fullmatch(r"([A-ZÇ]{3})-(\d{2}|\d{4})", normalized)
    if match:
        month = MONTHS_PT.get(match.group(1))
        year = int(match.group(2))
        if year < 100:
            year += 2000
        if month:
            return date(year, month, 1)

    parsed = pd.to_datetime(raw, dayfirst=True, errors="coerce")
    if not pd.isna(parsed):
        return date(parsed.year, parsed.month, 1)

    report.periodos_invalidos += 1
    report.inconsistencias.append(f"Linha {row_number}: periodo invalido: {raw}")
    return None


def parse_cli_period(value: str) -> date:
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Periodo invalido: {value}")
    return date(parsed.year, parsed.month, 1)


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


def read_excel(path: Path, sheet_name: str) -> tuple[pd.DataFrame, dict[str, str]]:
    workbook = pd.ExcelFile(path)
    if sheet_name not in workbook.sheet_names:
        raise RuntimeError(
            f"Planilha {sheet_name!r} nao encontrada. "
            f"Planilhas disponiveis: {', '.join(workbook.sheet_names)}"
        )

    dataframe = pd.read_excel(path, sheet_name=sheet_name, dtype=object)
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


def build_rows(
    dataframe: pd.DataFrame,
    mapping: dict[str, str],
    report: Report,
    selected_period: date | None,
) -> list[SaleRow]:
    rows = []

    for index, raw_row in dataframe.iterrows():
        row_number = index + 2
        periodo = parse_period(raw_row[mapping["periodo"]], row_number, report)
        if periodo is not None:
            report.periodos_encontrados.add(periodo)

        if selected_period is not None and periodo != selected_period:
            continue
        if periodo is None:
            continue

        report.linhas_periodo += 1
        codigo_pdv = normalize_code(raw_row[mapping["codigo_pdv"]])
        codigo_produto = normalize_code(raw_row[mapping["codigo_produto"]])
        operacao = parse_operacao(raw_row[mapping["operacao"]], row_number, report)

        if not codigo_pdv:
            report.codigos_cliente_vazios += 1
            report.inconsistencias.append(f"Linha {row_number}: codigo de cliente vazio.")
            continue
        if not codigo_produto:
            report.codigos_produto_vazios += 1
            report.inconsistencias.append(f"Linha {row_number}: codigo de produto vazio.")
            continue
        if operacao is None:
            continue

        quantidade = parse_decimal(
            raw_row[mapping["quantidade"]],
            row_number,
            mapping["quantidade"],
            report,
        )
        total_venda = parse_decimal(
            raw_row[mapping["total_venda"]],
            row_number,
            mapping["total_venda"],
            report,
        )
        fator_hl = parse_decimal(
            raw_row[mapping["fator_hl"]],
            row_number,
            mapping["fator_hl"],
            report,
        )
        volume_hl = parse_decimal(
            raw_row[mapping["volume_hl"]],
            row_number,
            mapping["volume_hl"],
            report,
        )

        fator_hl_raw = clean_text(raw_row[mapping["fator_hl"]])
        volume_hl_raw = clean_text(raw_row[mapping["volume_hl"]])
        if not fator_hl_raw:
            report.linhas_sem_fator_hl += 1
            fator_hl_value = None
        else:
            fator_hl_value = fator_hl
        if not volume_hl_raw:
            report.linhas_sem_volume_hl += 1
            volume_hl_value = None
        else:
            volume_hl_value = volume_hl

        calculated_volume_hl = quantidade * (fator_hl_value or Decimal("0"))
        if fator_hl_value is not None and volume_hl_value is not None:
            difference = abs(volume_hl_value - calculated_volume_hl)
            if difference > HL_TOLERANCE:
                report.linhas_divergencia_volume_hl += 1
                if report.linhas_divergencia_volume_hl <= 20:
                    report.inconsistencias.append(
                        "Linha "
                        f"{row_number}: VOLUME_HL {volume_hl_value} difere de "
                        f"Quantidade * FATOR_HL {calculated_volume_hl} "
                        f"em {difference}."
                    )

        if quantidade == 0:
            report.linhas_quantidade_zero += 1
            report.valor_quantidade_zero += total_venda
        if quantidade < 0:
            report.linhas_quantidade_negativa += 1
            report.valor_quantidade_negativa += total_venda
        if total_venda < 0:
            report.linhas_valor_negativo += 1
            report.valor_negativo += total_venda

        report.operacoes[operacao] += 1
        report.valor_por_operacao[operacao] += total_venda
        report.volume_por_operacao[operacao] += volume_hl_value or Decimal("0")
        report.quantidade_total += quantidade
        report.volume_hl_total += volume_hl_value or Decimal("0")
        report.volume_hl_calculado_total += calculated_volume_hl

        rows.append(
            SaleRow(
                row_number=row_number,
                codigo_pdv=codigo_pdv,
                operacao=operacao,
                codigo_produto=codigo_produto,
                descricao_produto=clean_text(raw_row[mapping["descricao_produto"]]),
                quantidade=quantidade,
                fator_hl=fator_hl_value,
                volume_hl=volume_hl_value,
                total_venda=total_venda,
                periodo=periodo,
            )
        )

    return rows


def has_column(session, table_name: str, column_name: str) -> bool:
    return bool(
        session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = :table_name
                  AND COLUMN_NAME = :column_name
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar_one()
    )


def query_clients(session, report: Report) -> dict[str, dict[str, Any]]:
    has_base_flag = has_column(session, "clientes", "base_pdv_atual")
    if has_base_flag:
        sql = """
            SELECT id, codigo_pdv, nome, rn, base_pdv_atual
            FROM clientes
            WHERE codigo_pdv IS NOT NULL
              AND codigo_pdv <> ''
        """
    else:
        report.avisos.append(
            "Coluna clientes.base_pdv_atual ainda nao existe. "
            "Dry-run usando transicao tecnica: RN preenchido indica os 174 PDVs atuais."
        )
        sql = """
            SELECT
                id,
                codigo_pdv,
                nome,
                rn,
                CASE
                    WHEN rn IS NOT NULL AND rn <> '' THEN TRUE
                    ELSE FALSE
                END AS base_pdv_atual
            FROM clientes
            WHERE codigo_pdv IS NOT NULL
              AND codigo_pdv <> ''
        """

    result = session.execute(text(sql)).mappings()
    return {str(row["codigo_pdv"]): dict(row) for row in result}


def query_products(session, codes: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    if not codes:
        return {}, {}

    has_factor = has_column(session, "produtos", "fator_hl")
    fator_projection = "fator_hl" if has_factor else "NULL AS fator_hl"
    result = session.execute(
        text(
            f"""
            SELECT id, codigo, descricao, {fator_projection}
            FROM produtos
            WHERE codigo IN :codes
            """
        ).bindparams(bindparam("codes", expanding=True)),
        {"codes": tuple(codes)},
    ).mappings()

    products = defaultdict(list)
    for row in result:
        products[str(row["codigo"])].append(dict(row))

    mapped = {code: rows[0] for code, rows in products.items() if len(rows) == 1}
    duplicated = {code: len(rows) for code, rows in products.items() if len(rows) > 1}
    return mapped, duplicated


def query_products_with_cesta(session, product_codes: set[str]) -> set[str]:
    if not product_codes:
        return set()

    result = session.execute(
        text(
            """
            SELECT DISTINCT p.codigo
            FROM produtos p
            JOIN cesta_produto_itens cpi
              ON cpi.produto_id = p.id
            WHERE p.codigo IN :codes
            """
        ).bindparams(bindparam("codes", expanding=True)),
        {"codes": tuple(product_codes)},
    )
    return {str(row[0]) for row in result}


def ensure_client(session, codigo_pdv: str) -> int:
    client_id = session.execute(
        text("SELECT id FROM clientes WHERE codigo_pdv = :codigo_pdv"),
        {"codigo_pdv": codigo_pdv},
    ).scalar_one_or_none()
    if client_id is not None:
        return int(client_id)

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
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                FALSE,
                0.00
            )
            """
        ),
        {"codigo_pdv": codigo_pdv},
    )
    return int(session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one())


def ensure_product(session, row: SaleRow) -> int:
    product_id = session.execute(
        text("SELECT id FROM produtos WHERE codigo = :codigo"),
        {"codigo": row.codigo_produto},
    ).scalar_one_or_none()
    if product_id is not None:
        return int(product_id)

    session.execute(
        text(
            """
            INSERT INTO produtos (
                codigo,
                descricao,
                categoria,
                preco
            )
            VALUES (
                :codigo,
                :descricao,
                NULL,
                0.00
            )
            """
        ),
        {
            "codigo": row.codigo_produto,
            "descricao": row.descricao_produto or f"Produto {row.codigo_produto}",
        },
    )
    return int(session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one())


def insert_importacao(session, path: Path, period: date, report: Report) -> int:
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
                :periodo,
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
            "tipo": "BASE_VENDA",
            "periodo": period,
            "arquivo_nome": path.name,
            "arquivo_hash": file_hash(path),
            "status": "CONCLUIDA",
            "linhas_lidas": report.total_linhas_excel,
            "linhas_importadas": report.consolidacoes_item,
            "erros": report.erros,
        },
    )
    return int(session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one())


def replace_sales(session, period: date, rows: list[SaleRow], importacao_id: int) -> None:
    existing_sales = session.execute(
        text(
            """
            SELECT id
            FROM vendas
            WHERE periodo = :periodo
              AND origem = :origem
            """
        ),
        {"periodo": period, "origem": ORIGEM},
    )
    venda_ids = [int(row[0]) for row in existing_sales]

    if venda_ids:
        session.execute(
            text("DELETE FROM itens_venda WHERE venda_id IN :venda_ids").bindparams(
                bindparam("venda_ids", expanding=True)
            ),
            {"venda_ids": tuple(venda_ids)},
        )
        session.execute(
            text("DELETE FROM vendas WHERE id IN :venda_ids").bindparams(
                bindparam("venda_ids", expanding=True)
            ),
            {"venda_ids": tuple(venda_ids)},
        )

    client_ids = {row.codigo_pdv: ensure_client(session, row.codigo_pdv) for row in rows}
    product_ids = {row.codigo_produto: ensure_product(session, row) for row in rows}

    sale_totals: dict[tuple[int, date, int], Decimal] = defaultdict(lambda: Decimal("0.00"))
    item_totals: dict[tuple[int, date, int, int], dict[str, Decimal]] = {}

    for row in rows:
        cliente_id = client_ids[row.codigo_pdv]
        produto_id = product_ids[row.codigo_produto]
        sale_key = (cliente_id, row.periodo, row.operacao)
        item_key = (cliente_id, row.periodo, row.operacao, produto_id)
        sale_totals[sale_key] += row.total_venda
        item = item_totals.setdefault(
            item_key,
            {
                "quantidade": Decimal("0.0000"),
                "subtotal": Decimal("0.00"),
                "volume_hl": Decimal("0.00"),
                "fator_hl": row.fator_hl,
            },
        )
        item["quantidade"] += row.quantidade
        item["subtotal"] += row.total_venda
        item["volume_hl"] += row.volume_hl or Decimal("0")
        if item["fator_hl"] is None and row.fator_hl is not None:
            item["fator_hl"] = row.fator_hl

    venda_id_by_key = {}
    for (cliente_id, venda_periodo, operacao), valor_total in sale_totals.items():
        session.execute(
            text(
                """
                INSERT INTO vendas (
                    cliente_id,
                    periodo,
                    data_venda,
                    valor_total,
                    operacao,
                    origem,
                    importacao_id
                )
                VALUES (
                    :cliente_id,
                    :periodo,
                    NULL,
                    :valor_total,
                    :operacao,
                    :origem,
                    :importacao_id
                )
                """
            ),
            {
                "cliente_id": cliente_id,
                "periodo": venda_periodo,
                "valor_total": valor_total.quantize(CENT, rounding=ROUND_HALF_UP),
                "operacao": operacao,
                "origem": ORIGEM,
                "importacao_id": importacao_id,
            },
        )
        venda_id_by_key[(cliente_id, venda_periodo, operacao)] = int(
            session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one()
        )

    for (cliente_id, item_periodo, operacao, produto_id), values in item_totals.items():
        quantidade = values["quantidade"]
        subtotal = values["subtotal"]
        preco_unitario = Decimal("0") if quantidade == 0 else subtotal / quantidade
        session.execute(
            text(
                """
                INSERT INTO itens_venda (
                    venda_id,
                    produto_id,
                    quantidade,
                    fator_hl,
                    volume_hl,
                    preco_unitario,
                    subtotal
                )
                VALUES (
                    :venda_id,
                    :produto_id,
                    :quantidade,
                    :fator_hl,
                    :volume_hl,
                    :preco_unitario,
                    :subtotal
                )
                """
            ),
            {
                "venda_id": venda_id_by_key[(cliente_id, item_periodo, operacao)],
                "produto_id": produto_id,
                "quantidade": quantidade.quantize(QTY_PRECISION, rounding=ROUND_HALF_UP),
                "fator_hl": (
                    values["fator_hl"].quantize(FACTOR_PRECISION, rounding=ROUND_HALF_UP)
                    if values["fator_hl"] is not None
                    else None
                ),
                "volume_hl": values["volume_hl"].quantize(VOLUME_HL_PRECISION, rounding=ROUND_HALF_UP),
                "preco_unitario": preco_unitario.quantize(PRICE_PRECISION, rounding=ROUND_HALF_UP),
                "subtotal": subtotal.quantize(CENT, rounding=ROUND_HALF_UP),
            },
        )


def analyze(path: Path, sheet_name: str, selected_period: date | None, dry_run: bool) -> Report:
    dataframe, mapping = read_excel(path, sheet_name)
    report = Report(arquivo=path, planilha=sheet_name, total_linhas_excel=len(dataframe))
    rows = build_rows(dataframe, mapping, report, selected_period)
    report.diferenca_volume_hl = report.volume_hl_total - report.volume_hl_calculado_total

    if selected_period is None:
        if len(report.periodos_encontrados) != 1:
            report.erros += 1
            report.inconsistencias.append(
                "Informe --periodo quando o arquivo possuir zero ou multiplos periodos validos."
            )
            return report
        report.periodo_encontrado = next(iter(report.periodos_encontrados))
    else:
        report.periodo_encontrado = selected_period

    mysql_user = os.getenv("MYSQL_USER", "")
    if mysql_user.strip().lower() == "agente_readonly":
        raise RuntimeError(
            "MYSQL_USER esta configurado como agente_readonly. "
            "Use o usuario normal da aplicacao."
        )

    session = SessionLocal()
    try:
        clients = query_clients(session, report)
        product_codes = {row.codigo_produto for row in rows}
        products, duplicated_products = query_products(session, product_codes)
        products_with_cesta = query_products_with_cesta(session, product_codes)

        report.produtos_duplicados_db = duplicated_products
        if duplicated_products:
            for code, count in sorted(duplicated_products.items()):
                report.inconsistencias.append(
                    f"Produto {code} mapeado para {count} registros em produtos."
                )

        client_codes = {row.codigo_pdv for row in rows}
        current_base_clients = {
            code
            for code, client in clients.items()
            if bool(client.get("base_pdv_atual"))
        }
        known_clients_in_file = client_codes & set(clients)
        base_clients_in_file = client_codes & current_base_clients

        report.clientes_distintos = len(client_codes)
        report.tamanho_base_pdv_atual = len(current_base_clients)
        report.clientes_base_pdv_atual = len(base_clients_in_file)
        report.clientes_historicos_fora_base = len(client_codes - base_clients_in_file)
        report.novos_clientes_historicos = len(client_codes - set(clients))

        report.produtos_distintos = len(product_codes)
        report.produtos_existentes = len(set(products))
        report.produtos_novos = len(product_codes - set(products) - set(duplicated_products))
        report.produtos_sem_fator = len(
            {
                row.codigo_produto
                for row in rows
                if row.fator_hl is None
            }
        )

        for row in rows:
            if row.codigo_produto not in products and row.codigo_produto not in duplicated_products:
                summary = report.produtos_novos_lista.setdefault(
                    row.codigo_produto,
                    ProductSummary(codigo=row.codigo_produto, descricao=row.descricao_produto),
                )
                summary.linhas += 1
                summary.valor += row.total_venda
                summary.volume += row.quantidade

        product_codes_without_cesta = product_codes - products_with_cesta
        report.produtos_sem_cesta = len(product_codes_without_cesta)

        sale_keys = {(row.codigo_pdv, row.periodo, row.operacao) for row in rows}
        item_keys = {
            (row.codigo_pdv, row.periodo, row.operacao, row.codigo_produto)
            for row in rows
        }
        report.consolidacoes_venda = len(sale_keys)
        report.consolidacoes_item = len(item_keys)

        # Variavel mantida para deixar explicito que clientes conhecidos fora da base
        # e clientes novos historicos sao ambos historico valido da revenda.
        _ = known_clients_in_file

        if dry_run:
            session.rollback()
            return report

        if report.erros or report.produtos_duplicados_db:
            raise RuntimeError("Importacao bloqueada por erros ou produtos ambiguos.")

        importacao_id = insert_importacao(session, path, report.periodo_encontrado, report)
        replace_sales(session, report.periodo_encontrado, rows, importacao_id)
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
    print("ARQUIVO")
    print(f"- arquivo: {report.arquivo}")
    print(f"- planilha utilizada: {report.planilha}")
    print(f"- periodo encontrado: {report.periodo_encontrado}")
    if report.periodos_encontrados:
        periodos = ", ".join(str(period) for period in sorted(report.periodos_encontrados))
        print(f"- periodos validos no arquivo: {periodos}")
    print("")

    print("OPERACOES")
    for operacao, total in sorted(report.operacoes.items()):
        nome = "VENDA" if operacao == 1 else "BONIFICACAO"
        print(
            f"- operacao {operacao} ({nome}): {total} linhas | "
            f"valor {money(report.valor_por_operacao[operacao])} | "
            f"volume HL {hl(report.volume_por_operacao[operacao])}"
        )
    print(f"- faturamento operacao 1: {money(report.valor_por_operacao[1])}")
    print(f"- valor operacao 2: {money(report.valor_por_operacao[2])}")
    print(f"- volume vendido HL: {hl(report.volume_por_operacao[1])}")
    print(f"- volume bonificado HL: {hl(report.volume_por_operacao[2])}")
    print(f"- volume movimentado HL: {hl(report.volume_por_operacao[1] + report.volume_por_operacao[2])}")
    print("")

    print("LINHAS")
    print(f"- total de linhas Excel: {report.total_linhas_excel}")
    print(f"- linhas do periodo: {report.linhas_periodo}")
    print("")

    print("CLIENTES")
    print(f"- clientes distintos na venda: {report.clientes_distintos}")
    print(f"- tamanho da Base PDV atual: {report.tamanho_base_pdv_atual}")
    print(f"- clientes pertencentes a Base PDV atual com venda: {report.clientes_base_pdv_atual}")
    print(f"- clientes historicos/fora da Base com venda: {report.clientes_historicos_fora_base}")
    print(f"- novos clientes historicos que precisariam ser criados: {report.novos_clientes_historicos}")
    print("")

    print("PRODUTOS")
    print(f"- produtos distintos na venda: {report.produtos_distintos}")
    print(f"- produtos existentes: {report.produtos_existentes}")
    print(f"- produtos novos que precisariam ser criados: {report.produtos_novos}")
    print(f"- produtos sem cesta: {report.produtos_sem_cesta}")
    print(f"- produtos sem fator_hl no arquivo: {report.produtos_sem_fator}")
    if report.produtos_novos_lista:
        print("- produtos novos:")
        for item in sorted(report.produtos_novos_lista.values(), key=lambda value: value.codigo):
            print(
                f"  {item.codigo} | {item.descricao} | "
                f"linhas={item.linhas} | valor={money(item.valor)} | volume={qty(item.volume)}"
            )
    print("")

    print("CONSOLIDACAO")
    print(f"- consolidacoes cliente+periodo+operacao: {report.consolidacoes_venda}")
    print(f"- consolidacoes cliente+periodo+operacao+produto: {report.consolidacoes_item}")
    print("")

    print("QUANTIDADE ZERO")
    print(f"- linhas com quantidade zero: {report.linhas_quantidade_zero}")
    print(f"- valor correspondente: {money(report.valor_quantidade_zero)}")
    print("")

    print("QUANTIDADE E VOLUME HL")
    print(f"- quantidade total: {qty(report.quantidade_total)}")
    print(f"- volume HL total informado: {hl(report.volume_hl_total)}")
    print(f"- volume HL calculado por Quantidade * FATOR_HL: {hl(report.volume_hl_calculado_total)}")
    print(f"- diferenca informado - calculado: {hl(report.diferenca_volume_hl)}")
    print(f"- linhas com divergencia relevante: {report.linhas_divergencia_volume_hl}")
    print(f"- linhas sem FATOR_HL: {report.linhas_sem_fator_hl}")
    print(f"- linhas sem VOLUME_HL: {report.linhas_sem_volume_hl}")
    print("")

    print("VALIDACOES ADICIONAIS")
    print(f"- quantidade negativa: {report.linhas_quantidade_negativa} linhas | valor {money(report.valor_quantidade_negativa)}")
    print(f"- valor negativo: {report.linhas_valor_negativo} linhas | valor {money(report.valor_negativo)}")
    print(f"- codigo de cliente vazio: {report.codigos_cliente_vazios}")
    print(f"- codigo de produto vazio: {report.codigos_produto_vazios}")
    print(f"- operacao invalida: {report.operacoes_invalidas}")
    print(f"- periodo invalido: {report.periodos_invalidos}")
    print(f"- produtos mapeados para mais de um registro: {len(report.produtos_duplicados_db)}")
    print("")

    if report.avisos:
        print("AVISOS")
        for warning in report.avisos:
            print(f"- {warning}")
        print("")

    print("INCONSISTENCIAS/ERROS")
    print(f"- inconsistencias: {len(report.inconsistencias)}")
    print(f"- erros: {report.erros}")
    for inconsistency in report.inconsistencias:
        print(f"  {inconsistency}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Importa a Base de Vendas historica consolidada."
    )
    parser.add_argument("--arquivo", required=True, help="Caminho do arquivo BASE_VENDA.xlsx")
    parser.add_argument("--planilha", default=DEFAULT_SHEET, help="Nome da planilha do Excel")
    parser.add_argument("--periodo", help="Periodo desejado, por exemplo 2026-08-01 ou AGO-26")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem gravar no banco")
    args = parser.parse_args()

    try:
        path = resolve_file(args.arquivo)
        selected_period = parse_cli_period(args.periodo) if args.periodo else None
        report = analyze(path, args.planilha, selected_period, args.dry_run)
    except Exception as exc:
        print(f"Erro critico durante a importacao: {exc}", file=sys.stderr)
        return 1

    print_report(report, args.dry_run)
    return 1 if report.erros else 0


if __name__ == "__main__":
    raise SystemExit(main())
