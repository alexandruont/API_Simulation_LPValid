import os
import re
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var is required")

app = FastAPI(title="License Plate Payment API")

PLATE_RE = re.compile(r"[^A-Z0-9]")

def normalize_plate(raw: str) -> str:
    norm = PLATE_RE.sub("", raw.upper())
    return norm

def get_conn():
    # Uses a short-lived connection per request (fine for small services).
    # For higher throughput, switch to a pool (psycopg_pool).
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

class PlateUpsert(BaseModel):
    plate: str
    raw: Optional[str] = None

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/paid/{plate}")
def is_paid(plate: str):
    plate_norm = normalize_plate(plate)
    if not plate_norm:
        raise HTTPException(status_code=400, detail="Invalid plate")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM plates WHERE plate_norm = %s LIMIT 1;",
                (plate_norm,),
            )
            paid = cur.fetchone() is not None

    return {"plate": plate, "plate_norm": plate_norm, "paid": paid}

@app.post("/paid")
def mark_paid(body: PlateUpsert):
    plate_norm = normalize_plate(body.plate)
    if not plate_norm:
        raise HTTPException(status_code=400, detail="Invalid plate")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO plates (plate_norm, plate_raw)
                VALUES (%s, %s)
                ON CONFLICT (plate_norm) DO UPDATE
                SET plate_raw = EXCLUDED.plate_raw
                RETURNING id, plate_norm, plate_raw, created_at;
                """,
                (plate_norm, body.raw or body.plate),
            )
            row = cur.fetchone()
        conn.commit()

    return {"ok": True, "record": row}

@app.delete("/paid/{plate}")
def unmark_paid(plate: str):
    plate_norm = normalize_plate(plate)
    if not plate_norm:
        raise HTTPException(status_code=400, detail="Invalid plate")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM plates WHERE plate_norm = %s;", (plate_norm,))
            deleted = cur.rowcount
        conn.commit()

    return {"ok": True, "deleted": deleted}