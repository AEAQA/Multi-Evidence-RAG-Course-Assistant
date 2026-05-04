from rag_project.query_planning.intent_planner import DeterministicIntentPlanner
from rag_project.query_planning.siliconflow_intent_planner import SiliconFlowIntentPlanner


def test_deterministic_planner_splits_simple_and_query() -> None:
    plan = DeterministicIntentPlanner().plan(
        "what is word2vec? and what is transformer?",
        top_k=3,
    )

    assert plan.is_multi_intent is True
    assert [item.id for item in plan.sub_questions] == ["Q1", "Q2"]
    assert "word2vec" in plan.sub_questions[0].retrieval_query.lower()
    assert "transformer" in plan.sub_questions[1].retrieval_query.lower()
    assert all(item.intent == "definition" for item in plan.sub_questions)
    assert plan.answer_style == "sectioned"


def test_deterministic_planner_keeps_single_query_single() -> None:
    plan = DeterministicIntentPlanner().plan("How does reranking improve retrieval?")

    assert plan.is_multi_intent is False
    assert len(plan.sub_questions) == 1
    assert plan.sub_questions[0].intent == "concept"


def test_deterministic_planner_marks_table_intent() -> None:
    plan = DeterministicIntentPlanner().plan(
        "Compare the numerical columns in the table.",
        available_evidence_types=["text", "table_summary"],
    )

    sub = plan.sub_questions[0]
    assert sub.intent == "comparison"
    assert sub.table_allowed is True
    assert sub.evidence_preference[0] == "table_summary"


def test_siliconflow_planner_falls_back_on_invalid_json() -> None:
    def fake_post_json(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        return {"choices": [{"message": {"content": "not json"}}]}

    planner = SiliconFlowIntentPlanner(
        api_key="test-key",
        model="planner-model",
        post_json=fake_post_json,
    )

    plan = planner.plan("what is word2vec? and what is transformer?")

    assert plan.fallback_used is True
    assert plan.planner_provider == "mock"
    assert plan.is_multi_intent is True
