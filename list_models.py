import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
genai.configure(api_key="GOOGLE_API_KEY")  # Or use your environment variable

for model in genai.list_models():
    print(model.name, model.supported_generation_methods)