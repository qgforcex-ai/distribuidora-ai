import json
import inspect
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai.business_semantics import BUSINESS_SEMANTICS
from app.ai.schema_catalog import SCHEMA_CATALOG
from app.ai.sql_generator import _extrair_sql, gerar_sql
from app.ai import planner


EVAL_PATH = ROOT / "tests" / "evals" / "commercial_aug_2026.json"


class CommercialSemanticsTest(unittest.TestCase):
    def test_official_metrics_require_base_venda_origin(self):
        combined = f"{BUSINESS_SEMANTICS}\n{SCHEMA_CATALOG}\n{inspect.getsource(gerar_sql)}"

        self.assertIn("vendas.origem = 'BASE_VENDA'", combined)
        self.assertIn("vendas.operacao = 1", combined)

    def test_revenda_total_is_not_base_pdv_current(self):
        combined = f"{BUSINESS_SEMANTICS}\n{SCHEMA_CATALOG}\n{inspect.getsource(gerar_sql)}".lower()

        self.assertIn("revenda total", combined)
        self.assertIn("nao filtre clientes.base_pdv_atual", combined)
        self.assertIn("does_not_filter_base_pdv_atual", EVAL_PATH.read_text(encoding="utf-8"))

    def test_rn_requires_current_base_pdv_filter(self):
        combined = f"{BUSINESS_SEMANTICS}\n{SCHEMA_CATALOG}\n{inspect.getsource(gerar_sql)}"

        self.assertIn("clientes.base_pdv_atual = TRUE", combined)
        self.assertIn("clientes.rn", combined)

    def test_volume_uses_hl_not_quantity(self):
        combined = f"{BUSINESS_SEMANTICS}\n{SCHEMA_CATALOG}\n{inspect.getsource(gerar_sql)}"

        self.assertIn("itens_venda.volume_hl", combined)
        self.assertIn("Não use SUM(itens_venda.quantidade) como volume", combined)

    def test_distribution_is_distinct_customer_product(self):
        combined = f"{BUSINESS_SEMANTICS}\n{SCHEMA_CATALOG}\n{inspect.getsource(gerar_sql)}"

        self.assertIn("COUNT(DISTINCT vendas.cliente_id, itens_venda.produto_id)", combined)
        self.assertIn("vendas.operacao = 1", combined)
        self.assertIn("vendas.origem = 'BASE_VENDA'", combined)

    def test_coverage_requires_buyers_universe_and_percentage(self):
        combined = f"{BUSINESS_SEMANTICS}\n{SCHEMA_CATALOG}\n{inspect.getsource(gerar_sql)}"

        self.assertIn("compradores", combined)
        self.assertIn("universo_total", combined)
        self.assertIn("cobertura_percentual", combined)
        self.assertIn("melhor cobertura", combined)

    def test_basket_is_product_filter_not_customer_filter(self):
        combined = f"{BUSINESS_SEMANTICS}\n{SCHEMA_CATALOG}\n{inspect.getsource(gerar_sql)}".lower()

        self.assertIn("cesta e filtro de produtos", combined)
        self.assertIn("cesta na revenda", combined)
        self.assertIn("nao deve aplicar", combined)

    def test_quanto_vendemos_defaults_to_revenue(self):
        combined = f"{BUSINESS_SEMANTICS}\n{SCHEMA_CATALOG}\n{inspect.getsource(gerar_sql)}".lower()
        planner_source = inspect.getsource(planner)

        self.assertIn("quanto vendemos", combined)
        self.assertIn("faturamento", combined)
        self.assertIn("quanto\\s+vendemos", planner_source)

    def test_sql_extraction_handles_markdown_and_explanatory_text(self):
        raw = """
        **Consulta SQL para obter os clientes**
        ```sql
        SELECT * FROM clientes WHERE base_pdv_atual = TRUE;
        ```
        Texto extra.
        """

        self.assertEqual(
            _extrair_sql(raw),
            "SELECT * FROM clientes WHERE base_pdv_atual = TRUE;"
        )

    def test_eval_fixture_contains_all_official_cases(self):
        data = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        cases = data["cases"]

        self.assertEqual(data["periodo"], "2026-08-01")
        self.assertEqual(data["origem"], "BASE_VENDA")
        self.assertEqual(data["operacao"], 1)
        self.assertEqual(len(cases), 18)
        self.assertEqual({case["id"] for case in cases}, {f"T{i:02d}" for i in range(1, 19)})


if __name__ == "__main__":
    unittest.main()
