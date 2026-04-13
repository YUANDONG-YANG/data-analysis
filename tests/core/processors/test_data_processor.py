import pandas as pd
import pandas.testing as pdt

from src.core.config import CommunityNamesConfig
from src.core.processors.data_processor import DataProcessor


def make_processor() -> DataProcessor:
    return DataProcessor(
        CommunityNamesConfig(
            aliases={
                "Riverbend TH": "Riverbend Townhomes",
                "Fairview Estates - Phase 2": "Fairview Estates",
                "Maplewood-Heights": "Maplewood Heights",
            },
            path_slugs=["riverbend-townhomes", "fairview-estates"],
        )
    )


def test_standardize_date_handles_iso_and_invalid_values():
    processor = make_processor()

    assert processor.standardize_date("2025-09-21T08:38:53Z") == "2025-09-21"
    assert processor.standardize_date("09/21/2025") == "2025-09-21"
    assert processor.standardize_date("not-a-date") is None


def test_standardize_community_name_resolves_aliases_and_suffixes():
    processor = make_processor()

    assert processor.standardize_community_name("Fairview Estates - Phase 2") == "Fairview Estates"
    assert processor.standardize_community_name("riverbend th community") == "Riverbend Townhomes"
    assert processor.standardize_community_name("Maplewood-Heights") == "Maplewood Heights"


def test_clean_data_removes_duplicates_and_outliers():
    processor = make_processor()
    raw = pd.DataFrame(
        [
            {"home_id": "1", "total_sale_price": 250000, "sqft": 1800},
            {"home_id": "1", "total_sale_price": 250000, "sqft": 1800},
            {"home_id": "2", "total_sale_price": -1, "sqft": 1800},
            {"home_id": "3", "total_sale_price": 300000, "sqft": 40},
            {"home_id": "4", "total_sale_price": 15000000, "sqft": 2200},
            {"home_id": "5", "total_sale_price": 350000, "sqft": 2200},
        ]
    )

    cleaned = processor.clean_data(raw)

    assert list(cleaned["home_id"]) == ["1", "5"]


def test_process_sales_data_standardizes_and_adds_year_month():
    processor = make_processor()
    sales = pd.DataFrame(
        [
            {
                "home_id": "HS-001",
                "sale_contract_date": "03/12/2025",
                "community_name": "Fairview Estates - Phase 2",
                "builder": "a",
                "total_sale_price": 388737,
            },
            {
                "home_id": "HS-002",
                "sale_contract_date": "bad-date",
                "community_name": "Riverbend TH",
                "builder": "a",
                "total_sale_price": 300000,
            },
        ]
    )

    processed = processor.process_sales_data(sales)

    assert len(processed) == 1
    assert processed.iloc[0]["community_name"] == "Fairview Estates"
    assert processed.iloc[0]["sale_contract_date"] == "2025-03-12"
    assert processed.iloc[0]["year_month"] == "2025-03"
    assert str(processed.iloc[0]["date"].date()) == "2025-03-12"


def test_process_web_traffic_data_extracts_community_from_page_path():
    processor = make_processor()
    traffic = pd.DataFrame(
        [
            {"page_path": "/communities/riverbend-townhomes/overview", "date": "2025-04-09"},
            {"page_path": "/unknown", "date": "2025-04-10"},
        ]
    )

    processed = processor.process_web_traffic_data(traffic)

    expected = pd.DataFrame(
        [
            {
                "page_path": "/communities/riverbend-townhomes/overview",
                "date": pd.Timestamp("2025-04-09"),
                "year_month": "2025-04",
                "community_name": "Riverbend Townhomes",
            }
        ]
    )

    pdt.assert_frame_equal(processed.reset_index(drop=True), expected)
