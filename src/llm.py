"""
llm.py — LLM call with tool_use and prompt caching.
"""

from src.config import MODEL, PROMPT_FILE, TAXONOMY_STR, client
from src.models import AgentDecision

# Load the prompt template and inject the taxonomy at startup
_template = PROMPT_FILE.read_text(encoding="utf-8")
SYSTEM_PROMPT = _template.replace("{TAXONOMY_STR}", TAXONOMY_STR)

TOOLS = [
    {
        "name": "classify_case",
        "description": "Classifies the support case and determines whether it is an active fraud incident.",
        "input_schema": AgentDecision.model_json_schema(),
    }
]


def call_llm(conversation: str, country: str) -> AgentDecision:
    """
    Classify an accumulated support conversation using the LLM.

    The system prompt is cached across calls via Anthropic prompt caching.
    The ``classify_case`` tool is forced so the response always matches
    the ``AgentDecision`` JSON schema.

    Parameters
    ----------
    conversation : str
        Full conversation history formatted as ``[Usuario]/[Agente]: <text>`` lines.
    country : str
        Country of the user, injected into the prompt for localisation context.

    Returns
    -------
    AgentDecision
        Validated Pydantic model with the LLM classification result.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=TOOLS,
        tool_choice={"type": "tool", "name": "classify_case"},
        messages=[
            {
                "role": "user",
                "content": f"PAÍS: {country}\n\nCONVERSACIÓN ACUMULADA:\n{conversation}",
            }
        ],
    )
    raw = response.content[0].input
    return AgentDecision.model_validate(raw)
