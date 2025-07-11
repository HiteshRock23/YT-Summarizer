# summarizer_test.py

import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ✅ Load environment variables
load_dotenv()

# ✅ Fetch the API key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in .env file")

# ✅ Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# 🔁 Summarize a single chunk using Gemini
def summarize_chunk(chunk: str, retries: int = 3) -> str:
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')


    for attempt in range(retries):
        try:
            response = model.generate_content(
                f"Summarize the following transcript chunk in concise bullet points for student revision:\n\n{chunk}"
            )
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ Error summarizing chunk (attempt {attempt + 1}): {e}")
            time.sleep(2)
    return "⚠️ Summary failed for this chunk."

# 🔁 Split and summarize entire transcript
def summarize_transcript(transcript: str) -> str:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_text(transcript)

    if not chunks:
        return "❌ No content found in transcript."

    summaries = [summarize_chunk(chunk) for chunk in chunks]
    final_summary = summarize_chunk("\n".join(summaries))
    return final_summary

# ✅ Main function to test
if __name__ == "__main__":
    sample_transcript = """
    Welcome everyone. Today we're going to discuss the basics of Artificial Intelligence and Machine Learning.
    AI refers to systems or machines that mimic human intelligence to perform tasks and can iteratively improve themselves based on the information they collect.
    Machine learning is a subset of AI, and it allows software applications to become more accurate at predicting outcomes without being explicitly programmed to do so.
    It uses historical data as input to predict new output values.
    Let's now look at the key types of machine learning: supervised, unsupervised, and reinforcement learning...
    """

    print("\n🔍 Running Gemini Summarizer...\n")
    result = summarize_transcript(sample_transcript)
    print("📄 Final Summary:\n")
    print(result)
