import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv
from transformers import pipeline
from langchain_huggingface import HuggingFacePipeline

# Load environment
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Database insert function
def insert_essay(student_id, original, corrected, feedback, model_name, latency_ms):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO essays (student_id, original_text, corrected_text, feedback, model_name, latency_ms)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (student_id, original, corrected, feedback, model_name, latency_ms))
    essay_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return essay_id

# Load model
MODEL_NAME = "google/flan-t5-base"
_hf = pipeline("text2text-generation", model=MODEL_NAME, device=-1)  # CPU
llm = HuggingFacePipeline(pipeline=_hf)

PROMPT = (
    "Correct the grammar and spelling in this text. "
    "Return the corrected text first, then one short feedback sentence "
    "explaining the main fix.\n\nText: {text}"
)

def correct_and_feedback(text: str):
    raw_output = llm.invoke(PROMPT.format(text=text))
    raw = str(raw_output).strip()
    parts = raw.split("Feedback:")
    corrected = parts[0].strip()
    feedback = parts[1].strip() if len(parts) > 1 else "Fixed grammar and clarity."
    return corrected, feedback

# ---------------- Streamlit UI ----------------
st.title("📝 Student Essay Corrector")

student_id = st.text_input("Enter Student ID")
essay_text = st.text_area("Paste the student's essay here:")

if st.button("Correct Essay"):
    if essay_text.strip() == "":
        st.warning("Please enter some text.")
    else:
        with st.spinner("Correcting..."):
            corrected, feedback = correct_and_feedback(essay_text)

            # Insert into DB
            try:
                essay_id = insert_essay(
                    student_id, essay_text, corrected, feedback, MODEL_NAME, latency_ms=0
                )
                st.success(f"Essay saved with ID: {essay_id}")
            except Exception as e:
                st.error(f"DB insert failed: {e}")

            # Show results
            st.subheader("✅ Corrected Essay")
            st.write(corrected)
            st.subheader("💡 Feedback")
            st.info(feedback)

# Show stored essays
if st.checkbox("Show all past essays"):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT student_id, original_text, corrected_text, feedback, created_at FROM essays ORDER BY created_at DESC;")
        rows = cur.fetchall()
        conn.close()
        st.subheader("📚 Past Essays")
        for r in rows:
            st.markdown(f"**Student {r[0]}** ({r[4]})")
            st.markdown(f"- Original: {r[1]}")
            st.markdown(f"- Corrected: {r[2]}")
            st.markdown(f"- Feedback: {r[3]}")
            st.write("---")
    except Exception as e:
        st.error(f"Could not fetch essays: {e}")
