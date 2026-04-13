from unittest.mock import Mock

import pandas as pd
import pandas.testing as pdt
import pytest

from src.core.exceptions import DataProcessError
from src.services.metrics_service import MetricsService


def test_calculate_metrics_delegates_to_calculator():
    calculator = Mock()
    expected = pd.DataFrame([{"month": "2025-03", "actual_sales": 2}])
    calculator.calculate_monthly_community_metrics.return_value = expected
    service = MetricsService(calculator)

    result = service.calculate_metrics(
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
    )

    pdt.assert_frame_equal(result, expected)
    calculator.calculate_monthly_community_metrics.assert_called_once()


def test_calculate_metrics_wraps_errors():
    calculator = Mock()
    calculator.calculate_monthly_community_metrics.side_effect = RuntimeError("bad math")
    service = MetricsService(calculator)

    with pytest.raises(DataProcessError, match="Failed to calculate metrics: bad math"):
        service.calculate_metrics(pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())


def test_generate_quality_report_distinguishes_actual_and_target_ranges():
    service = MetricsService(Mock())
    metrics = pd.DataFrame(
        [
            {"month": "2025-03", "community_name": "A", "actual_sales": 2},
            {"month": "2025-04", "community_name": "A", "actual_sales": 0},
            {"month": "2025-05", "community_name": "B", "actual_sales": 0},
        ]
    )
    targets = pd.DataFrame([{"year_month": "2025-03"}, {"year_month": "2025-12"}])

    report = service.generate_quality_report(metrics, targets)

    assert report["total_records"] == 3
    assert report["communities"] == 2
    assert report["month_range"] == {"min": "2025-03", "max": "2025-05"}
    assert report["actual_data_range"] == {"min": "2025-03", "max": "2025-03"}
    assert report["target_month_range"] == {"min": "2025-03", "max": "2025-12"}
