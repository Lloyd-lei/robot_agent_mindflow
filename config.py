"""
配置管理模块
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ============== LLM 提供商选择 ==============
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"

# ============== Ollama 配置（本地模型）==============
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# ============== OpenAI 配置（云端API）==============
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

# ============== 统一配置（根据提供商选择）==============
if USE_OLLAMA:
    LLM_MODEL = OLLAMA_MODEL
    LLM_BASE_URL = OLLAMA_BASE_URL
    LLM_API_KEY = "ollama"  # Ollama不需要真实API key
    print(f"🦙 使用 Ollama 本地模型: {LLM_MODEL}")
else:
    LLM_MODEL = OPENAI_MODEL
    LLM_BASE_URL = None  # OpenAI 使用默认地址
    LLM_API_KEY = OPENAI_API_KEY
    print(f"☁️  使用 OpenAI 云端模型: {LLM_MODEL}")
    
    # 验证 OpenAI API Key
    if not OPENAI_API_KEY:
        raise ValueError("❌ 使用OpenAI时，请在 .env 文件中设置 OPENAI_API_KEY 环境变量")

