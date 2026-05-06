"""
config.py — Variables de entorno, clientes y taxonomía.
"""

import json
import os
from pathlib import Path

import anthropic

#  Constantes ───────────────────────────────────────────────────────────────

MODEL = os.getenv("MODEL", "claude-haiku-4-5")
MEMORY_FILE = Path(os.getenv("MEMORY_FILE", "outputs/conversation_memory.csv"))
TAXONOMY_FILE = Path(os.getenv("TAXONOMY_FILE", "assets/categorias.json"))
PROMPT_FILE = Path(os.getenv("PROMPT_FILE", "assets/system_prompt.txt"))

#  Cliente Anthropic ────────────────────────────────────────────────────────

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", None)

if not ANTHROPIC_KEY:
    raise ValueError("Missing ANTHROPIC_API_KEY environment var. Aborting")

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

#  Taxonomía ────────────────────────────────────────────────────────────────

with TAXONOMY_FILE.open(encoding="utf-8") as f:
    _taxonomy = json.load(f)

TAXONOMY_STR = "\n".join(
    f"- {name}: {data['Descripcion']}.\n\t- Subcategorías: {', '.join(data['Subcategoria'].keys())}"
    for name, data in _taxonomy["Clasificacion"]["Categoria"].items()
)
