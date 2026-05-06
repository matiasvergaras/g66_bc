"""
memory.py — Thread-safe CSV persistence for support conversations.
"""

import threading
from datetime import datetime, timezone

import pandas as pd

from src.config import MEMORY_FILE
from src.models import AgentDecision, IncomingMessage

_lock = threading.Lock()
_COLS = [
    "case_id",
    "message_id",
    "user_id",
    "direction",
    "text",
    "pais_usuario",
    "channel",
    "ts",
    "category",
    "subcategory",
    "sentiment",
    "urgency",
    "confidence",
    "is_fraud",
    "suggested_response",
    "reasoning",
]


def _ensure() -> None:
    """
    Ensure the memory CSV exists and has the expected schema.

    Creates the file with the correct header if it does not exist.
    Recreates it if the on-disk schema differs from ``_COLS``.
    Must be called while holding ``_lock``.
    """
    if not MEMORY_FILE.exists():
        pd.DataFrame(columns=_COLS).to_csv(MEMORY_FILE, index=False)
        return
    try:
        existing_cols = pd.read_csv(MEMORY_FILE, nrows=0).columns.tolist()
    except Exception:
        existing_cols = []
    if existing_cols != _COLS:
        pd.DataFrame(columns=_COLS).to_csv(MEMORY_FILE, index=False)


def append_message(msg: IncomingMessage) -> None:
    """
    Append an incoming message to the memory CSV.

    Decision fields are left empty and filled later by ``save_decision``.

    Parameters
    ----------
    msg : IncomingMessage
        The support message to persist.
    """
    row = {
        "case_id": msg.case_id,
        "message_id": msg.message_id,
        "user_id": msg.user_id,
        "direction": msg.direction,
        "text": msg.text,
        "pais_usuario": msg.pais_usuario,
        "channel": msg.channel,
        "ts": datetime.now(timezone.utc).isoformat(),
        "category": "",
        "subcategory": "",
        "sentiment": "",
        "urgency": "",
        "confidence": "",
        "is_fraud": "",
        "suggested_response": "",
        "reasoning": "",
    }
    with _lock:
        _ensure()
        pd.DataFrame([row]).to_csv(MEMORY_FILE, mode="a", header=False, index=False)


def save_decision(message_id: str, decision: AgentDecision) -> None:
    """
    Write LLM decision fields into the row matching ``message_id``.

    Newlines in ``suggested_response`` and ``reasoning`` are replaced
    with spaces to keep each record on a single CSV line.

    Parameters
    ----------
    message_id : str
        Identifier of the message row to update.
    decision : AgentDecision
        Validated LLM output to persist alongside the message.
    """
    with _lock:
        _ensure()
        df = pd.read_csv(MEMORY_FILE, dtype=str)
        idx = df.index[df["message_id"] == message_id]
        if len(idx):
            df.loc[idx, "category"] = decision.category.value
            df.loc[idx, "subcategory"] = decision.subcategory.value
            df.loc[idx, "sentiment"] = decision.sentiment.value
            df.loc[idx, "urgency"] = decision.urgency.value
            df.loc[idx, "confidence"] = str(decision.confidence)
            df.loc[idx, "is_fraud"] = str(decision.is_fraud)
            df.loc[idx, "suggested_response"] = decision.suggested_response.replace(
                "\n", " "
            ).replace("\r", "")
            df.loc[idx, "reasoning"] = decision.reasoning.replace("\n", " ").replace("\r", "")
            df.to_csv(MEMORY_FILE, index=False)


def load_case(case_id: str) -> tuple[list[dict], str]:
    """
    Load all messages for a case, ordered by timestamp.

    Parameters
    ----------
    case_id : str
        The case identifier to retrieve.

    Returns
    -------
    messages : list[dict]
        Rows for the case sorted by ``ts``.
    country : str
        Country of the user, taken from the first message in the case.
        Falls back to ``"Desconocido"`` if the case has no messages.
    """
    with _lock:
        _ensure()
        df = pd.read_csv(MEMORY_FILE, dtype=str)

    case_df = df[df["case_id"] == case_id].sort_values("ts")
    messages = case_df.to_dict("records")
    country = case_df["pais_usuario"].iloc[0] if len(case_df) else "Desconocido"
    return messages, country


def build_conversation(messages: list[dict]) -> str:
    """
    Format a list of messages into a readable conversation string.

    Parameters
    ----------
    messages : list[dict]
        Ordered message records, each containing ``direction`` and ``text``.

    Returns
    -------
    str
        Conversation formatted as ``[Usuario]: <text>`` / ``[Agente]: <text>`` lines.
    """
    lines = []
    for m in messages:
        who = "Usuario" if m["direction"] == "INBOUND" else "Agente"
        lines.append(f"[{who}]: {m['text']}")
    return "\n".join(lines)


def read_all(case_id: str | None = None) -> list[dict]:
    """
    Return all memory records, optionally filtered by case.

    Parameters
    ----------
    case_id : str, optional
        When provided, only records for this case are returned.

    Returns
    -------
    list[dict]
        Memory records with NaN values replaced by empty strings.
    """
    with _lock:
        _ensure()
        df = pd.read_csv(MEMORY_FILE, dtype=str)

    if case_id:
        df = df[df["case_id"] == case_id]

    return df.fillna("").to_dict("records")


def delete_case(case_id: str) -> None:
    """
    Remove all records for a given case from the memory CSV.

    Parameters
    ----------
    case_id : str
        Identifier of the case to delete.
    """
    with _lock:
        _ensure()
        df = pd.read_csv(MEMORY_FILE, dtype=str)
        df[df["case_id"] != case_id].to_csv(MEMORY_FILE, index=False)
