"""
配置管理模块
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# OpenAI配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

# 验证配置
if not OPENAI_API_KEY:
    raise ValueError("❌ 请在 .env 文件中设置 OPENAI_API_KEY 环境变量")

