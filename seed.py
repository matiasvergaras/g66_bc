"""
seed.py — Sends every message from XLSX to the API.
API must be running beforehand.

Usage:
    python seed.py
    python seed.py --file "otra_bbdd.xlsx" --url http://localhost:9000
"""

import argparse

import httpx
import pandas as pd

# Args ───────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument("--file", default="assets/Business tech case 1 - BBDD.xlsx")
parser.add_argument("--url", default="http://localhost:8000")
parser.add_argument("--out", default="outputs/seed_memory.csv")
args = parser.parse_args()

ENDPOINT = f"{args.url}/sofia/classify"

# Carga y limpieza ───────────────────────────────────────────────────────────

df = pd.read_excel(args.file)
df.columns = df.columns.str.strip()
df["text"] = df["text"].str.strip().str.strip('"')
df = df.sort_values("message_id").reset_index(drop=True)

total = len(df)
print(f"Enviando {total} mensajes de {df['case_id'].nunique()} casos...\n")

# Envío ──────────────────────────────────────────────────────────────────────

errors = []

with httpx.Client(timeout=30) as client:
    for i, row in df.iterrows():
        payload = {
            "case_id": row["case_id"],
            "message_id": row["message_id"],
            "user_id": row["user_id"],
            "direction": row["direction"],
            "text": row["text"],
            "pais_usuario": row["pais_usuario"],
        }

        try:
            r = client.post(ENDPOINT, json=payload)
            r.raise_for_status()
            decision = r.json().get("decision", "?")
            print(f"[{i + 1}/{total}] {row['message_id']} ({row['direction']}) → {decision}")
        except Exception as e:
            print(f"[{i + 1}/{total}] {row['message_id']} ERROR: {e}")
            errors.append(row["message_id"])

# ── Resumen ────────────────────────────────────────────────────────────────────

print(f"\nListo. {total - len(errors)}/{total} mensajes enviados correctamente.")
if errors:
    print(f"Fallidos: {errors}")

# Exportar memoria ───────────────────────────────────────────────────────────

with httpx.Client(timeout=30) as client:
    r = client.get(f"{args.url}/sofia/memory")
    r.raise_for_status()
    pd.DataFrame(r.json()).to_csv(args.out, index=False)

print(f"Memoria guardada en {args.out}")
