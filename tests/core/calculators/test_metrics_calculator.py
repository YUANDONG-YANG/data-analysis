import pandas as pd

from src.core.calculators.metrics_calculator import MetricsCalculator


def test_calculate_monthly_community_metrics_combines_all_inputs():
    calculator = MetricsCalculator()
    sales = pd.DataFrame(
        [
            {
                "year_month": "2025-03",
                "community_name": "Fairview Estates",
                "builder": "a",
                "total_sale_price": 300000,
                "home_id": "HS-1",
            },
            {
                "year_month": "2025-03",
                "community_name": "Fairview Estates",
                "builder": "a",
                "total_sale_price": 350000,
                "home_id": "HS-2",
            },
        ]
    )
    targets = pd.DataFrame(
        [
            {
                "year_month": "2025-03",
                "community_name": "Fairview Estates",
                "builder": "a",
                "target_sales": 5,
            },
            {
                "year_month": "2025-04",
                "community_name": "Fairview Estates",
                "builder": "a",
                "target_sales": 3,
            },
        ]
    )
    crm = pd.DataFrame(
        [
            {"year_month": "2025-03", "community_name": "Fairview Estates", "builder_id": "builder_a"},
            {"year_month": "2025-03", "community_name": "Fairview Estates", "builder_id": "builder_a"},
            {"year_month": "2025-03", "community_name": "Fairview Estates", "builder_id": "builder_a"},
            {"year_month": "2025-03", "community_name": "Fairview Estates", "builder_id": "builder_a"},
        ]
    )
    traffic = pd.DataFrame(
        [
            {
                "year_month": "2025-03",
                "community_name": "Fairview Estates",
                "builder_id": "builder_a",
                "sessions": 40,
            }
        ]
    )

    result = calculator.calculate_monthly_community_metrics(sales, targets, crm, traffic)

    assert list(result.columns) == [
        "month",
        "community_name",
        "builder",
        "actual_sales",
        "target_sales",
        "variance",
        "crm_leads",
        "web_traffic",
        "estimated_revenue",
        "achievement_rate",
        "estimated_avg_sale_price",
        "conversion_rate",
        "traffic_to_sales_rate",
    ]
    assert list(result["month"]) == ["2025-03", "2025-04"]

    current = result[result["month"] == "2025-03"].iloc[0]
    assert current["actual_sales"] == 2
    assert current["target_sales"] == 5
    assert current["variance"] == -3
    assert current["crm_leads"] == 4
    assert current["web_traffic"] == 40
    assert current["estimated_revenue"] == 650000
    assert current["achievement_rate"] == 40
    assert current["estimated_avg_sale_price"] == 325000
    assert current["conversion_rate"] == 50
    assert current["traffic_to_sales_rate"] == 5

    forecast = result[result["month"] == "2025-04"].iloc[0]
    assert forecast["actual_sales"] == 0
    assert forecast["target_sales"] == 3
    assert forecast["estimated_revenue"] == 0
    assert forecast["achievement_rate"] == 0


def test_calculate_monthly_community_metrics_accepts_month_column_in_sales():
    calculator = MetricsCalculator()
    sales = pd.DataFrame(
        [
            {
                "month": "2025-03",
                "community_name": "Cedar Creek",
                "builder": "b",
                "total_sale_price": 500000,
                "home_id": "HS-9",
            }
        ]
    )

    result = calculator.calculate_monthly_community_metrics(
        sales,
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
    )

    row = result.iloc[0]
    assert row["month"] == "2025-03"
    assert row["actual_sales"] == 1
    assert row["builder"] == "b"


def test_calculate_monthly_community_metrics_returns_empty_schema_when_no_sales_and_targets():
    calculator = MetricsCalculator()

    result = calculator.calculate_monthly_community_metrics(
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
    )

    assert result.empty
    assert "actual_sales" in result.columns
    assert "traffic_to_sales_rate" in result.columns
