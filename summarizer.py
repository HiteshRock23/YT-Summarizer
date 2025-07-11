import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google.generativeai as genai
from dotenv import load_dotenv
import time

# ✅ Load environment variables
load_dotenv()

# ✅ Fetch the API key securely
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in .env file")

# ✅ Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# 🔁 Gemini Summarizer with Retry Logic
def summarize_chunk(chunk: str, retries: int = 3) -> str:
    model = genai.GenerativeModel('gemini-pro')
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

# 🔁 Split and summarize full transcript
def summarize_transcript(transcript: str) -> str:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_text(transcript)

    if not chunks:
        return "❌ No content found in transcript."

    # ✅ Summarize each chunk
    summaries = [summarize_chunk(chunk) for chunk in chunks]

    # ✅ Summarize all summaries (final summarization layer)
    final_summary = summarize_chunk("\n".join(summaries))
    return final_summary
