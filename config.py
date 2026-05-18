from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")


LLM_CONFIG = {
    "deepseek": {
        "provider":"deepseek",
        "api_key":api_key,
        "base_url":"https://api.deepseek.com",
        "model":"deepseek-chat"
    },
    "qwen3.5:2b":{
        "provider": "openai-compatible",
        "api_key": "EMPTY",
        "base_url": "http://localhost:11434/v1",
        "model": "qwen3.5:2b"
    }
}