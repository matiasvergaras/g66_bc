"""
api.py — Global66 Fraud Detection API.

Usage
-----
    make venv
    source .venv/bin/activate
    make install
    make run

Interactive docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException

from src.config import MODEL
from src.llm import call_llm
from src.memory import (
    append_message,
    build_conversation,
    delete_case,
    load_case,
    read_all,
    save_decision,
)
from src.models import ClassifyResponse, IncomingMessage

app = FastAPI(title="Sofia — Global66 Fraud Detection API", version="1.0.0")


# Routes ───────────────────────────────────────────────────────────────────────


@app.post("/sofia/classify", response_model=ClassifyResponse)
def classify(msg: IncomingMessage) -> ClassifyResponse:
    """
    Classify an incoming support message and accumulate it in memory.

    OUTBOUND messages are stored but not analysed by the LLM.
    INBOUND messages trigger a full conversation analysis.

    Parameters
    ----------
    msg : IncomingMessage
        The support message payload (INBOUND or OUTBOUND).

    Returns
    -------
    ClassifyResponse
        decision="keep_hearing"  — no fraud detected; ticket follows normal flow.
        decision="trigger_block" — fraud detected; ``text`` contains the immediate
        response to send to the user.
    """
    append_message(msg)

    if msg.direction == "OUTBOUND":
        return ClassifyResponse(
            case_id=msg.case_id,
            message_id=msg.message_id,
            decision="keep_hearing",
            category="AGENT",
            subcategory="AGENT",
            sentiment="NEUTRAL",
            urgency="BAJA",
            confidence=0.0,
            text="",
        )

    messages, country = load_case(msg.case_id)
    conversation = build_conversation(messages)

    try:
        decision = call_llm(conversation, country)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

    save_decision(msg.message_id, decision)

    if decision.is_fraud:
        return ClassifyResponse(
            case_id=msg.case_id,
            message_id=msg.message_id,
            decision="trigger_block",
            category=decision.category.value,
            subcategory=decision.subcategory.value,
            sentiment=decision.sentiment.value,
            urgency=decision.urgency.value,
            confidence=decision.confidence,
            text=decision.suggested_response,
        )

    return ClassifyResponse(
        case_id=msg.case_id,
        message_id=msg.message_id,
        decision="keep_hearing",
        category=decision.category.value,
        subcategory=decision.subcategory.value,
        sentiment=decision.sentiment.value,
        urgency=decision.urgency.value,
        confidence=decision.confidence,
        text="",
    )


@app.get("/sofia/memory", summary="List accumulated messages")
def get_memory(case_id: str | None = None):
    """
    Return all records stored in memory.

    Parameters
    ----------
    case_id : str, optional
        When provided, filters results to the given case.

    Returns
    -------
    list[dict]
        List of memory records as dicts.
    """
    return read_all(case_id)


@app.delete("/sofia/memory/{case_id}", summary="Delete a case history")
def clear_case(case_id: str):
    """
    Delete all messages belonging to a case.

    Parameters
    ----------
    case_id : str
        Identifier of the case to remove.

    Returns
    -------
    dict
        Confirmation payload with the deleted case_id.
    """
    delete_case(case_id)
    return {"deleted": case_id}


@app.get("/health")
def health():
    """
    Health check endpoint.

    Returns
    -------
    dict
        Service status and active model name.
    """
    return {"status": "ok", "model": MODEL}
