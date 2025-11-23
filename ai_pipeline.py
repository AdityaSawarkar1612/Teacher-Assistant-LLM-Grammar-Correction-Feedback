import os
import torch
from transformers import pipeline
from langchain_huggingface import HuggingFacePipeline

MODEL_NAME = "google/flan-t5-base" 

# Select device: GPU if available, else CPU
device = 0 if torch.cuda.is_available() else -1  

# Force disable lazy loading to avoid meta tensor errors
os.environ["TRANSFORMERS_NO_LAZY_IMPORTS"] = "1"

# 1) Hugging Face pipeline
_hf = pipeline(
    "text2text-generation",
    model=MODEL_NAME,
    device=device
)

# 2) Wrap in LangChain
llm = HuggingFacePipeline(pipeline=_hf)

# Prompt template
PROMPT = (
    "Correct the grammar and spelling in this text. "
    "Return the corrected text first, then one short feedback sentence "
    "explaining the main fix.\n\nText: {text}"
)

def correct_and_feedback(text: str) -> tuple[str, str]:
    """Returns (corrected_text, feedback_sentence)"""

    try:
        # Use LangChain invoke
        raw_output = llm.invoke(PROMPT.format(text=text))

        # Ensure string type
        raw = str(raw_output).strip()

        # Split into corrected + feedback
        parts = raw.split("Feedback:")
        corrected = parts[0].strip()
        feedback = parts[1].strip() if len(parts) > 1 else "Fixed grammar and clarity."

        # Ensure corrected isn’t empty
        if not corrected:
            corrected = text

        return corrected, feedback

    except Exception as e:
        # Fallback in case of model failure
        return text, f"⚠️ Model error: {e}"


# 🔎 Quick test
if __name__ == "__main__":
    test_text = "This is my frst test sentnce for pipline."
    corrected, feedback = correct_and_feedback(test_text)
    print("Input:     ", test_text)
    print("Corrected: ", corrected)
    print("Feedback:  ", feedback)
