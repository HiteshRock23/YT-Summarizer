import os
import time
import logging
from typing import Dict, Optional
from dotenv import load_dotenv
import google.generativeai as genai
import together

# Load environment variables 
load_dotenv()

logger = logging.getLogger(__name__)

class MultiLLMHandler:
    """Handles multiple LLM providers with automatic fallback"""

    def __init__(self):
        # Initialize Gemini
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('models/gemini-1.5-flash')
        else:
            self.gemini_model = None
            logger.warning("No Google API key found. Gemini will not be available.")

        # Initialize Together.ai
        self.together_api_key = os.getenv('TOGETHER_API_KEY')
        if self.together_api_key:
            together.api_key = self.together_api_key
            self.together_model = "mistralai/Mistral-7B-Instruct-v0.2"
        else:
            self.together_model = None
            logger.warning("No Together API key found. Mistral-7B will not be available.")

        # Track usage and errors
        self.gemini_quota_exceeded = False
        self.gemini_last_error_time = 0
        self.together_quota_exceeded = False
        self.together_last_error_time = 0

        # Quota reset time (24 hours)
        self.quota_reset_hours = 24

    def _is_quota_reset(self, last_error_time: float) -> bool:
        if last_error_time == 0:
            return True
        hours_since_error = (time.time() - last_error_time) / 3600
        return hours_since_error >= self.quota_reset_hours

    def _reset_quota_flags(self):
        current_time = time.time()

        if self.gemini_quota_exceeded and self._is_quota_reset(self.gemini_last_error_time):
            self.gemini_quota_exceeded = False
            logger.info("Gemini quota reset - will try again")

        if self.together_quota_exceeded and self._is_quota_reset(self.together_last_error_time):
            self.together_quota_exceeded = False
            logger.info("Together.ai quota reset - will try again")

    def _call_gemini(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        if not self.gemini_model or self.gemini_quota_exceeded:
            return None

        for attempt in range(max_retries):
            try:
                response = self.gemini_model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                if "429" in error_str and "quota" in error_str.lower():
                    self.gemini_quota_exceeded = True
                    self.gemini_last_error_time = time.time()
                    logger.warning(f"Gemini quota exceeded: {error_str}")
                    return None
                elif "rate limit" in error_str.lower():
                    wait_time = 2 ** attempt
                    logger.warning(f"Gemini rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Gemini error (attempt {attempt + 1}): {error_str}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(1)

        return None

    def _call_mistral(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        if not self.together_model or self.together_quota_exceeded:
            return None

        formatted_prompt = f"<s>[INST] {prompt} [/INST]"

        for attempt in range(max_retries):
            try:
                response = together.Complete.create(
                    prompt=formatted_prompt,
                    model=self.together_model,
                    max_tokens=2048,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=50,
                    repetition_penalty=1.1
                )
                response_text = response['output']['choices'][0]['text'].strip()
                return response_text
            except Exception as e:
                error_str = str(e)
                if "quota" in error_str.lower() or "limit" in error_str.lower():
                    self.together_quota_exceeded = True
                    self.together_last_error_time = time.time()
                    logger.warning(f"Together.ai quota exceeded: {error_str}")
                    return None
                elif "rate limit" in error_str.lower():
                    wait_time = 2 ** attempt
                    logger.warning(f"Together.ai rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Together.ai error (attempt {attempt + 1}): {error_str}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(1)

        return None

    def generate_content(self, prompt: str, task_type: Optional[str] = None) -> Optional[str]:

        self._reset_quota_flags()

        if self.gemini_model and not self.gemini_quota_exceeded:
            logger.info("Trying Gemini...")
            result = self._call_gemini(prompt)
            if result:
                logger.info("Gemini successful")
                return result
            else:
                logger.warning("Gemini failed, trying Mistral-7B...")

        if self.together_model and not self.together_quota_exceeded:
            logger.info("Trying Mistral-7B via Together.ai...")
            result = self._call_mistral(prompt)
            if result:
                logger.info("Mistral-7B successful")
                return result
            else:
                logger.warning("Mistral-7B failed")

        logger.error("All LLM providers failed")
        return None



    def get_status(self) -> Dict:
        return {
            'gemini': {
                'available': self.gemini_model is not None,
                'quota_exceeded': self.gemini_quota_exceeded,
                'last_error_time': self.gemini_last_error_time,
                'api_key_configured': bool(self.gemini_api_key)
            },
            'mistral': {
                'available': self.together_model is not None,
                'quota_exceeded': self.together_quota_exceeded,
                'last_error_time': self.together_last_error_time,
                'api_key_configured': bool(self.together_api_key)
            }
        }

def create_llm_handler() -> MultiLLMHandler:
    return MultiLLMHandler()

def test_llm_providers():
    handler = create_llm_handler()

    print("🧪 Testing LLM Providers...")
    print("=" * 50)

    if handler.gemini_model:
        print("🔄 Testing Gemini...")
        result = handler._call_gemini("Say 'Hello from Gemini' in one sentence.")
        if result:
            print(f"✅ Gemini: {result}")
        else:
            print("❌ Gemini failed")
    else:
        print("❌ Gemini not available")

    if handler.together_model:
        print("🔄 Testing Mistral-7B...")
        result = handler._call_mistral("Say 'Hello from Mistral-7B' in one sentence.")
        if result:
            print(f"✅ Mistral-7B: {result}")
        else:
            print("❌ Mistral-7B failed")
    else:
        print("❌ Mistral-7B not available")

    print("\n🔄 Testing fallback mechanism...")
    result = handler.generate_content("Explain what a YouTube video summarizer does in one sentence.")
    if result:
        print(f"✅ Fallback successful: {result}")
    else:
        print("❌ All providers failed")

    print("\n📊 Provider Status:")
    status = handler.get_status()
    for provider, info in status.items():
        print(f"  {provider.title()}: {'✅' if info['available'] else '❌'} "
              f"(Quota exceeded: {'Yes' if info['quota_exceeded'] else 'No'})")

if __name__ == "__main__":
    test_llm_providers()
