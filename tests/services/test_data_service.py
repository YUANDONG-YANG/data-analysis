from unittest.mock import Mock

import pandas as pd
import pandas.testing as pdt
import pytest

from src.core.exceptions import DataProcessError
from src.services.data_service import DataService


def test_load_and_process_sales_data_runs_pipeline_and_writes_silver(tmp_path):
    merged = pd.DataFrame([{"home_id": "1", "total_sale_price": 300000}])
    cleaned = pd.DataFrame([{"home_id": "1", "total_sale_price": 300000}])
    processed = pd.DataFrame([{"home_id": "1", "year_month": "2025-03"}])

    file_repository = Mock()
    file_repository.load_all_sales_data.return_value = [merged]

    processor = Mock()
    processor.merge_dataframes.return_value = merged
    processor.clean_data.return_value = cleaned
    processor.process_sales_data.return_value = processed

    service = DataService(file_repository, None, processor, processed_path=tmp_path)

    result = service.load_and_process_sales_data()

    pdt.assert_frame_equal(result, processed)
    processor.merge_dataframes.assert_called_once_with([merged])
    processor.clean_data.assert_called_once_with(merged)
    processor.process_sales_data.assert_called_once_with(cleaned)
    assert (tmp_path / "sales_processed.csv").exists()


def test_load_and_process_crm_data_requires_api_repository():
    service = DataService(Mock(), None, Mock())

    with pytest.raises(DataProcessError, match="API repository is not configured") as exc_info:
        service.load_and_process_crm_data()

    assert exc_info.value.context["operation"] == "load_and_process_crm_data"


def test_load_and_process_web_traffic_data_wraps_unexpected_errors():
    api_repository = Mock()
    api_repository.load_all_web_traffic_data.side_effect = RuntimeError("boom")

    service = DataService(Mock(), api_repository, Mock())

    with pytest.raises(DataProcessError, match="Failed to load and process web traffic data: boom") as exc_info:
        service.load_and_process_web_traffic_data()

    assert exc_info.value.context["operation"] == "load_and_process_web_traffic_data"
