import argparse
import json
import math
import time
import uuid
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL = ROOT / "tests" / "evals" / "commercial_aug_2026.json"


VALUE_ALIASES = {
    "faturamento": ["faturamento", "faturamento_total", "valor_total"],
    "volume_hl": ["volume_hl", "volume", "volume_total_hl", "volume_vendido_hl"],
    "quantidade": ["quantidade", "quantidade_total"],
    "distribuicao": ["distribuicao", "distribuicao_total"],
    "cobertura": ["cobertura", "cobertura_percentual"],
}


SEMANTIC_CHECKS = {
    "uses_BASE_VENDA": lambda sql: "base_venda" in sql,
    "uses_operacao_1": lambda sql: "operacao" in sql and "1" in sql,
    "does_not_filter_base_pdv_atual": lambda sql: "base_pdv_atual" not in sql,
    "filters_base_pdv_atual": lambda sql: "base_pdv_atual" in sql,
    "filters_rn": lambda sql: ".rn" in sql or " rn" in sql,
    "uses_volume_hl": lambda sql: "volume_hl" in sql,
    "uses_cliente_produto_distinct": lambda sql: "distinct" in sql and "cliente_id" in sql and "produto_id" in sql,
    "returns_cobertura_percentual": lambda sql: "cobertura_percentual" in sql,
    "orders_by_cobertura_percentual": lambda sql: "order by" in sql and "cobertura_percentual" in sql,
    "orders_by_faturamento": lambda sql: "order by" in sql and "faturamento" in sql,
    "filters_cesta": lambda sql: "cestas" in sql or "cesta_produto_itens" in sql,
    "interprets_quanto_vendemos_as_faturamento": lambda sql: "subtotal" in sql and "volume_hl" not in sql,
}


def _first_row(dados):
    if isinstance(dados, list):
        return dados[0] if dados else {}
    if isinstance(dados, dict):
        return dados
    return {}


def _find_numeric(row, metric):
    for key in VALUE_ALIASES.get(metric, [metric]):
        if key in row and row[key] is not None:
            return float(row[key])
    return None


def _close(actual, expected, tolerance):
    if actual is None:
        return False
    return math.isclose(float(actual), float(expected), abs_tol=float(tolerance))


def _check_expected(case, response):
    if response.get("status") == "precisa_esclarecimento":
        return False, "PEDIU_ESCLARECIMENTO"

    if response.get("executado") is False or response.get("erro"):
        return False, "ERRO_TECNICO"

    dados = response.get("dados", {})
    metric = case.get("expected_metric")
    tolerance = case.get("tolerance", 0)

    if metric == "comparativo_rn":
        rows = {
            str(row.get("rn")): row
            for row in dados
            if isinstance(row, dict)
        }
        for expected in case["expected_rows"]:
            row = rows.get(expected["rn"])
            if not row:
                return False, "INCORRETO"
            checks = [
                _close(row.get("faturamento"), expected["faturamento"], tolerance),
                _close(_find_numeric(row, "volume_hl"), expected["volume_hl"], tolerance),
                int(row.get("compradores", -1)) == expected["compradores"],
                int(row.get("base_total", row.get("universo_total", -1))) == expected["universo"],
                _close(_find_numeric(row, "cobertura"), expected["cobertura"], tolerance),
            ]
            if not all(checks):
                return False, "INCORRETO"
        return True, "CORRETO"

    row = _first_row(dados)

    if "expected_winner" in case:
        winner = str(row.get("rn", row.get("codigo", row.get("nome", ""))))
        if winner != str(case["expected_winner"]):
            return False, "INCORRETO"

    if "expected_compradores" in case:
        if int(row.get("compradores", -1)) != int(case["expected_compradores"]):
            return False, "INCORRETO"

    if "expected_universo" in case:
        universo = row.get("universo_total", row.get("base_total"))
        if int(universo or -1) != int(case["expected_universo"]):
            return False, "INCORRETO"

    if "expected_value" in case:
        value = _find_numeric(row, metric)
        if not _close(value, case["expected_value"], tolerance):
            return False, "INCORRETO"

    return True, "CORRETO"


def _check_semantics(case, response):
    sql = (
        response.get("sql_executado")
        or response.get("sql_gerado")
        or ""
    ).lower()

    failed = []
    for expectation in case.get("semantic_expectations", []):
        check = SEMANTIC_CHECKS.get(expectation)
        if check and not check(sql):
            failed.append(expectation)

    return failed


def run_eval(base_url, eval_path, session_id):
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    results = []

    for case in data["cases"]:
        started = time.perf_counter()
        response = requests.post(
            f"{base_url.rstrip('/')}/ia/analisar",
            json={
                "session_id": session_id,
                "pergunta": case["pergunta"],
            },
            timeout=180,
        )
        elapsed = time.perf_counter() - started
        response.raise_for_status()
        payload = response.json()

        semantic_failures = _check_semantics(case, payload)
        value_ok, status = _check_expected(case, payload)
        if semantic_failures and status == "CORRETO":
            status = "PARCIAL"
        if not value_ok and semantic_failures:
            status = "INCORRETO"

        results.append({
            "id": case["id"],
            "pergunta": case["pergunta"],
            "status": status,
            "tempo": elapsed,
            "semantic_failures": semantic_failures,
            "sql_gerado": payload.get("sql_gerado"),
            "sql_executado": payload.get("sql_executado"),
            "dados": payload.get("dados"),
            "resposta": payload.get("resposta") or payload.get("pergunta"),
            "esperado": {
                key: value
                for key, value in case.items()
                if key.startswith("expected_")
            },
        })

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Executa a bateria comercial oficial contra /ia/analisar."
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--eval", type=Path, default=DEFAULT_EVAL)
    parser.add_argument("--session-id", default=str(uuid.uuid4()))
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    print(f"session_id: {args.session_id}")
    results = run_eval(args.base_url, args.eval, args.session_id)

    counts = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
        print("=" * 60)
        print(f"{result['id']} | {result['status']} | {result['tempo']:.3f}s")
        print(result["pergunta"])
        if result["semantic_failures"]:
            print("Falhas semanticas: " + ", ".join(result["semantic_failures"]))
        print("SQL: " + str(result["sql_executado"] or result["sql_gerado"]))
        print("Dados: " + json.dumps(result["dados"], ensure_ascii=False, default=str))

    print("=" * 60)
    print("Resumo:")
    for status in ["CORRETO", "PARCIAL", "INCORRETO", "PEDIU_ESCLARECIMENTO", "ERRO_TECNICO"]:
        print(f"{status}: {counts.get(status, 0)}")

    if args.json_output:
        args.json_output.write_text(
            json.dumps(results, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"Resultado JSON: {args.json_output}")


if __name__ == "__main__":
    main()
