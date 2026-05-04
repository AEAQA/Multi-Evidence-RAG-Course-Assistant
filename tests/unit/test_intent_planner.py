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


def test_deterministic_planner_does_not_duplicate_question_prefix() -> None:
    plan = DeterministicIntentPlanner().plan(
        "what is word2vec and what is tf-idf?",
        top_k=3,
    )

    assert [item.question for item in plan.sub_questions] == [
        "what is word2vec?",
        "what is tf-idf?",
    ]
    assert "what is what is" not in plan.sub_questions[1].question.lower()


def test_deterministic_planner_keeps_single_query_single() -> None:
    plan = DeterministicIntentPlanner().plan("How does reranking improve retrieval?")

    assert plan.route == "material_query"
    assert plan.requires_retrieval is True
    assert plan.answer_mode == "grounded"
    assert plan.evidence_panel_mode == "show"
    assert plan.is_multi_intent is False
    assert len(plan.sub_questions) == 1
    assert plan.sub_questions[0].intent == "concept"


def test_deterministic_router_skips_general_questions() -> None:
    plan = DeterministicIntentPlanner().plan("What is the weather today?")

    assert plan.route == "general_question"
    assert plan.requires_retrieval is False
    assert plan.answer_mode == "general"
    assert plan.evidence_panel_mode == "hide"
    assert plan.sub_questions == []


def test_deterministic_router_handles_app_help() -> None:
    plan = DeterministicIntentPlanner().plan("How do I upload materials?")

    assert plan.route == "app_help"
    assert plan.requires_retrieval is False
    assert plan.answer_mode == "help"


def test_deterministic_router_handles_out_of_scope() -> None:
    plan = DeterministicIntentPlanner().plan("Can you book a flight for me?")

    assert plan.route == "out_of_scope"
    assert plan.requires_retrieval is False
    assert plan.answer_mode == "refusal"


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


def test_siliconflow_planner_cannot_downgrade_material_query_to_general() -> None:
    def fake_post_json(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"original_query":"What is Word2Vec?",'
                            '"route":"general_question",'
                            '"requires_retrieval":false,'
                            '"is_multi_intent":false,'
                            '"sub_questions":[],'
                            '"answer_style":"single",'
                            '"requires_partial_support_status":false,'
                            '"retrieval_query":"",'
                            '"answer_mode":"general",'
                            '"evidence_panel_mode":"hide",'
                            '"reason_code":"general_knowledge"}'
                        )
                    }
                }
            ]
        }

    planner = SiliconFlowIntentPlanner(
        api_key="test-key",
        model="planner-model",
        post_json=fake_post_json,
    )

    plan = planner.plan("What is Word2Vec?")

    assert plan.route == "material_query"
    assert plan.requires_retrieval is True
    assert plan.answer_mode == "grounded"
    assert plan.evidence_panel_mode == "show"
    assert plan.sub_questions


def test_siliconflow_planner_cannot_force_weather_into_retrieval() -> None:
    def fake_post_json(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"original_query":"What is the weather today?",'
                            '"route":"material_query",'
                            '"requires_retrieval":true,'
                            '"is_multi_intent":false,'
                            '"sub_questions":[{"id":"Q1","question":"What is the weather today?",'
                            '"intent":"other","retrieval_query":"weather today",'
                            '"evidence_preference":["text"],"table_allowed":false,'
                            '"image_allowed":true,"top_k":3}],'
                            '"answer_style":"single",'
                            '"requires_partial_support_status":false,'
                            '"retrieval_query":"weather today",'
                            '"answer_mode":"grounded",'
                            '"evidence_panel_mode":"show",'
                            '"reason_code":"course_material_related"}'
                        )
                    }
                }
            ]
        }

    planner = SiliconFlowIntentPlanner(
        api_key="test-key",
        model="planner-model",
        post_json=fake_post_json,
    )

    plan = planner.plan("What is the weather today?")

    assert plan.route == "general_question"
    assert plan.requires_retrieval is False
    assert plan.answer_mode == "general"
    assert plan.evidence_panel_mode == "hide"
