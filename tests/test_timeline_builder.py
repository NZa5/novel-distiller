import pytest

from novel_distiller.analyzers.timeline_builder import TimelineBuilder
from novel_distiller.models.schemas import TimelineEvent


@pytest.fixture
def builder():
    return TimelineBuilder(llm_client=None)


def test_relative_time_reference_normalizes_and_calculates_offset(builder):
    reference = builder._extract_time_reference("次日，众人抵达城门。", "众人抵达城门。")
    assert reference is not None
    assert reference.type == "relative"
    assert reference.normalized == "1天后"
    assert reference.offset_days == 1.0


def test_timeline_summary_counts_events_and_types(builder):
    events = [
        TimelineEvent(id="EVT001", title="相遇", description="两人相遇", chapter=1, content="", event_type="meeting", estimated_day=0),
        TimelineEvent(id="EVT002", title="战斗", description="发生战斗", chapter=2, content="", event_type="battle", estimated_day=2),
        TimelineEvent(id="EVT003", title="发现", description="发现线索", chapter=2, content="", event_type="discovery", estimated_day=3),
    ]
    summary = builder.get_timeline_summary(events)
    assert summary["total_events"] == 3
    assert summary["span_days"] == 3
    assert summary["chapters_covered"] == 2
    assert summary["event_types"] == {"meeting": 1, "battle": 1, "discovery": 1}


def test_empty_timeline_summary_is_zeroed(builder):
    assert builder.get_timeline_summary([]) == {
        "total_events": 0, "span_days": 0, "events_per_day": 0,
        "event_types": {}, "chapters_covered": 0,
    }
