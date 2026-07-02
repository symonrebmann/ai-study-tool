
import pytest
from analytics_function import get_stats, get_trend, generate_report

def test_get_stats_empty():
    results = []
    assert get_stats(results) is None

def test_get_stats_all_correct():
    records = [{"grade": "Correct", "score": 1}, {"grade": "Correct", "score": 1}, {"grade": "Correct", "score": 1}, {"grade": "Correct", "score": 1}, {"grade": "Correct", "score": 1}]
    results = get_stats(records)
    assert results is not None
    assert len(results) == 7
    assert results["total"] == 5
    assert results["correct"] == 5
    assert results["partial"] == 0
    assert results["incorrect"] == 0
    assert results["correct%"] == 1.0
    assert results["partial%"] == 1.0
    assert results["weighted"] == 1.0

def test_get_stats_mixed():
    records = [{"grade": "Correct", "score": 1}, {"grade": "Correct", "score": 1}, {"grade": "Partially Correct", "score": .5}, {"grade": "Incorrect", "score": 0}, {"grade": "Incorrect", "score": 0}]
    results = get_stats(records)
    assert results is not None
    assert len(results) == 7
    assert results["total"] == 5
    assert results["correct"] == 2
    assert results["partial"] == 1
    assert results["correct"] == 2
    assert results["correct%"] == .40
    assert results["partial%"] == .60
    assert results["weighted"] == .50


def test_get_trend_no_change():
    records = [{"date": "2026-01-01-12-00-PM", "score": 0}, {"date": "2026-02-02-12-00-PM", "score": 0}, {"date": "2026-03-03-12-00-PM", "score": 0}, {"date": "2026-04-04-12-00-PM", "score": 0}]
    results = get_trend(records)
    assert results == "No Change →"

def test_get_trend_improvement():
    records = [{"date": "2026-01-01-12-00-PM", "score": 0}, {"date": "2026-02-02-12-00-PM", "score": 0}, {"date": "2026-03-03-12-00-PM", "score": 1}, {"date": "2026-04-04-12-00-PM", "score": 1}]
    results = get_trend(records)
    assert results == "Improvement ↑"

def test_get_trend_worsen():
    records = [{"date": "2026-01-01-12-00-PM", "score": 1}, {"date": "2026-02-02-12-00-PM", "score": 1}, {"date": "2026-03-03-12-00-PM", "score": 0}, {"date": "2026-04-04-12-00-PM", "score": 0}]
    results = get_trend(records)
    assert results == "Worsen ↓"

def test_get_trend_empty():
    records = []
    results = get_trend(records)
    assert results == "Needs more data"

def test_generate_report():
    topic_groups = {
        "Slope": [
            {"grade": "Correct", "score": 1.0, "date": "2026-01-01-12-00-PM"},
            {"grade": "Incorrect", "score": 0.0, "date": "2026-02-02-12-00-PM"}
        ]
    }
    result = generate_report(topic_groups)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Weakness Ranking" in result