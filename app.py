import os
import logging
import traceback
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai_pipeline import correct_and_feedback, MODEL_NAME
from db import insert_essay

DEBUG = os.getenv("DEBUG", "1") == "1"   # set DEBUG=0 in .env to hide stack traces
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Brazil AI – Essay Assistant")

# ✅ Input model
class EssayIn(BaseModel):
    student_text: str
    student_id: str  # Required

@app.get("/health")
def health():
    return {"ok": True, "model": MODEL_NAME}

@app.post("/submit_essay")
def submit_essay(payload: EssayIn):
    try:
        start = time.time()

        # 1) Run AI pipeline
        corrected, feedback = correct_and_feedback(payload.student_text)

        # 2) Measure latency
        latency_ms = int((time.time() - start) * 1000)

        # 3) Save to DB
        essay_id = insert_essay(
            payload.student_id,
            payload.student_text,
            corrected,
            feedback,
            MODEL_NAME,
            latency_ms
        )

        # ✅ Final return
        return {
            "essay_id": essay_id,
            "student_id": payload.student_id,
            "original": payload.student_text,
            "corrected": corrected,
            "feedback": feedback,
            "model": MODEL_NAME,
            "latency_ms": latency_ms
        }

    except Exception as e:
        # Collect error message + stacktrace
        err_msg = str(e)
        stack = traceback.format_exc()
        logging.error(f"/submit_essay error: {err_msg}\n{stack}")

        # Return a useful JSON error
        detail = {"message": err_msg}
        if DEBUG:
            detail["stack"] = stack

        raise HTTPException(status_code=500, detail=detail)

