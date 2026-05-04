"""Intent-aware query planner with deterministic offline fallback."""

from __future__ import annotations

import re
from typing import Literal, Protocol

from pydantic import BaseModel, Field

IntentType = Literal[
    "definition",
    "concept",
    "formula",
    "figure",
    "comparison",
    "summary",
    "procedure",
    "other",
]

EvidenceType = Literal["text", "image", "table_summary"]
RouteType = Literal[
    "material_query",
    "multi_intent_material_query",
    "general_question",
    "app_help",
    "out_of_scope",
]
AnswerMode = Literal["grounded", "general", "help", "refusal"]
EvidencePanelMode = Literal["show", "hide", "diagnostics_only"]


class SubQuestionPlan(BaseModel):
    """One retrieval unit derived from the user query."""

    id: str
    question: str
    intent: IntentType = "other"
    retrieval_query: str
    evidence_preference: list[EvidenceType] = Field(default_factory=lambda: ["text"])
    table_allowed: bool = False
    image_allowed: bool = True
    top_k: int = 3


class QueryPlan(BaseModel):
    """Structured query decomposition for retrieval planning."""

    original_query: str
    route: RouteType = "material_query"
    requires_retrieval: bool = True
    is_multi_intent: bool = False
    sub_questions: list[SubQuestionPlan] = Field(default_factory=list)
    answer_style: Literal["sectioned", "single"] = "single"
    requires_partial_support_status: bool = False
    retrieval_query: str = ""
    answer_mode: AnswerMode = "grounded"
    evidence_panel_mode: EvidencePanelMode = "show"
    reason_code: str = "course_material_related"
    planner_provider: str = "mock"
    fallback_used: bool = False


class IntentPlanner(Protocol):
    """Planner interface for deterministic and optional LLM planners."""

    def plan(
        self,
        query: str,
        *,
        selected_document_scope: str = "combined",
        available_document_count: int | None = None,
        recent_chat_history: list[str] | None = None,
        available_evidence_types: list[str] | None = None,
        top_k: int = 3,
    ) -> QueryPlan:
        """Return a JSON-serializable plan. Must not answer the question."""


class DeterministicIntentPlanner:
    """Small local planner for offline tests and provider fallback."""

    def plan(
        self,
        query: str,
        *,
        selected_document_scope: str = "combined",
        available_document_count: int | None = None,
        recent_chat_history: list[str] | None = None,
        available_evidence_types: list[str] | None = None,
        top_k: int = 3,
    ) -> QueryPlan:
        del selected_document_scope, available_document_count, recent_chat_history
        available = set(available_evidence_types or ["text", "image", "table_summary"])
        original = " ".join(str(query or "").split())
        route, answer_mode, reason_code = _route_query(original)
        requires_retrieval = route in {"material_query", "multi_intent_material_query"}
        if not requires_retrieval:
            return QueryPlan(
                original_query=original,
                route=route,
                requires_retrieval=False,
                is_multi_intent=False,
                sub_questions=[],
                answer_style="single",
                requires_partial_support_status=False,
                retrieval_query="",
                answer_mode=answer_mode,
                evidence_panel_mode="hide",
                reason_code=reason_code,
                planner_provider="mock",
                fallback_used=False,
            )
        parts = _split_query(original)
        if not parts:
            parts = [original or "Answer the question."]

        sub_questions = [
            _sub_question_plan(
                index=index,
                question=part,
                available=available,
                top_k=max(1, min(top_k, 10)),
            )
            for index, part in enumerate(parts, start=1)
        ]
        is_multi = len(sub_questions) > 1
        route = "multi_intent_material_query" if is_multi else "material_query"
        return QueryPlan(
            original_query=original,
            route=route,
            requires_retrieval=True,
            is_multi_intent=is_multi,
            sub_questions=sub_questions,
            answer_style="sectioned" if is_multi else "single",
            requires_partial_support_status=is_multi,
            retrieval_query=sub_questions[0].retrieval_query if sub_questions else original,
            answer_mode="grounded",
            evidence_panel_mode="show",
            reason_code="course_material_related",
            planner_provider="mock",
            fallback_used=False,
        )


def _route_query(query: str) -> tuple[RouteType, AnswerMode, str]:
    text = query.lower().strip()
    if not text:
        return "out_of_scope", "refusal", "empty_query"

    app_help_terms = [
        "how do i upload",
        "how to upload",
        "upload document",
        "upload materials",
        "manage materials",
        "how do i use",
        "how to use",
        "open page",
        "citation",
        "citations",
        "evidence panel",
        "evidence intelligence",
        "scope",
        "selected documents",
        "怎么看",
        "怎么上传",
        "如何上传",
        "如何使用",
    ]
    if any(term in text for term in app_help_terms):
        if any(material_term in text for material_term in ["evidence about", "evidence for", "evidence supports"]):
            return "material_query", "grounded", "course_material_related"
        return "app_help", "help", "app_usage"

    out_of_scope_terms = [
        "book a flight",
        "buy stock",
        "medical diagnosis",
        "hack",
        "write malware",
        "生成恶意",
    ]
    if any(term in text for term in out_of_scope_terms):
        return "out_of_scope", "refusal", "unrelated"

    general_terms = [
        "weather",
        "temperature today",
        "time is it",
        "current time",
        "today's news",
        "tell me a joke",
        "how are you",
        "capital of",
        "president of",
        "stock price",
        "天气",
        "几点",
        "新闻",
        "讲个笑话",
    ]
    if any(term in text for term in general_terms):
        return "general_question", "general", "general_knowledge"

    return "material_query", "grounded", "course_material_related"


def _split_query(query: str) -> list[str]:
    text = query.strip()
    if not text:
        return []

    question_parts = [
        _normalize_question(part)
        for part in re.split(r"(?<=[?？])\s+", text)
        if part.strip()
    ]
    if len(question_parts) > 1:
        return question_parts

    and_split = re.match(
        r"^\s*(what|who|where|when|why|how)\s+(?:is|are|was|were|do|does|did|can|should)\s+(.+?)\s+(?:,?\s*and|&)\s+(.+?)\s*\??\s*$",
        text,
        flags=re.IGNORECASE,
    )
    if and_split:
        prefix = and_split.group(1)
        left = and_split.group(2).strip(" ?,.;")
        right = and_split.group(3).strip(" ?,.;")
        verb_match = re.match(
            r"^\s*(?:what|who|where|when|why|how)\s+"
            r"(is|are|was|were|do|does|did|can|should)\s+",
            text,
            flags=re.IGNORECASE,
        )
        verb = verb_match.group(1) if verb_match else "is"
        right = re.sub(
            r"^(what|who|where|when|why|how)\s+"
            r"(is|are|was|were|do|does|did|can|should)\s+",
            "",
            right,
            flags=re.IGNORECASE,
        ).strip(" ?,.;")
        return [
            _normalize_question(f"{prefix} {verb} {left}?"),
            _normalize_question(f"{prefix} {verb} {right}?"),
        ]

    comparative_split = re.split(
        r"\s*(?:;|\n+)\s*",
        text,
    )
    parts = [_normalize_question(part) for part in comparative_split if part.strip()]
    return parts if len(parts) > 1 else [_normalize_question(text)]


def _normalize_question(text: str) -> str:
    cleaned = " ".join(str(text or "").strip().split())
    cleaned = cleaned.strip(" ;,")
    cleaned = re.sub(r"^(and|or)\s+", "", cleaned, flags=re.IGNORECASE)
    if not cleaned:
        return cleaned
    if cleaned[-1] not in ".?!？。":
        cleaned += "?"
    return cleaned


def _sub_question_plan(
    *,
    index: int,
    question: str,
    available: set[str],
    top_k: int,
) -> SubQuestionPlan:
    intent = _classify_intent(question)
    table_allowed = intent in {"comparison", "formula"}
    image_allowed = intent == "figure" or intent in {"definition", "concept", "summary", "other"}
    preference: list[EvidenceType] = ["text"]
    if intent == "figure" and "image" in available:
        preference = ["image", "text"]
    elif table_allowed and "table_summary" in available:
        preference = ["table_summary", "text", "image"]
    elif "image" in available:
        preference = ["text", "image"]

    return SubQuestionPlan(
        id=f"Q{index}",
        question=question,
        intent=intent,
        retrieval_query=_rewrite_for_retrieval(question, intent),
        evidence_preference=preference,
        table_allowed=table_allowed,
        image_allowed=image_allowed,
        top_k=top_k,
    )


def _classify_intent(question: str) -> IntentType:
    text = question.lower()
    if any(term in text for term in ["figure", "diagram", "image", "chart", "图", "图片", "图像"]):
        return "figure"
    if any(term in text for term in ["formula", "equation", "derive", "公式", "方程"]):
        return "formula"
    if any(term in text for term in ["compare", "difference", "versus", "vs", "numerical", "number", "columns", "rows", "table", "对比", "比较", "表格", "数值", "数据"]):
        return "comparison"
    if any(term in text for term in ["steps", "procedure", "process", "how to", "流程", "步骤"]):
        return "procedure"
    if any(term in text for term in ["summarize", "summary", "overview", "总结", "概括"]):
        return "summary"
    if re.search(r"\bwhat\s+(is|are|was|were)\b", text) or any(term in text for term in ["define", "definition", "是什么", "定义"]):
        return "definition"
    if any(term in text for term in ["why", "how", "explain", "concept", "解释", "为什么"]):
        return "concept"
    return "other"


def _rewrite_for_retrieval(question: str, intent: IntentType) -> str:
    cleaned = re.sub(r"^(what|who|where|when|why|how)\s+(is|are|was|were|do|does|did|can|should)\s+", "", question, flags=re.IGNORECASE)
    cleaned = cleaned.strip(" ?.!,;")
    suffix = {
        "definition": "definition concept",
        "concept": "concept explanation",
        "formula": "formula equation",
        "figure": "figure diagram image",
        "comparison": "comparison table numerical data",
        "summary": "summary overview",
        "procedure": "steps procedure process",
        "other": "",
    }[intent]
    return " ".join(part for part in [cleaned, suffix] if part).strip()
