"""
配置管理模块 - 支持环境区分和配置验证

使用方式:
    from src.core.config import settings

    api_key = settings.openai_api_key
    model = settings.llm_model
"""
import os
from typing import Optional
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


# 加载环境变量
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)


class Settings(BaseSettings):
    """应用配置类"""

    # ========== OpenAI 配置 ==========
    openai_api_key: str = Field(
        default="",  # 允许为空,测试环境可用
        description="OpenAI API密钥",
        validation_alias='OPENAI_API_KEY'
    )

    llm_model: str = Field(
        default="gpt-4-turbo-preview",
        description="LLM模型名称",
        validation_alias='LLM_MODEL'
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="温度参数(0-2)",
        validation_alias='TEMPERATURE'
    )

    # ========== Agent 配置 ==========
    enable_cache: bool = Field(
        default=True,
        description="是否启用KV Cache",
        validation_alias='ENABLE_CACHE'
    )

    max_retries: int = Field(
        default=3,
        ge=1,
        description="最大重试次数",
        validation_alias='MAX_RETRIES'
    )

    timeout: int = Field(
        default=30,
        ge=1,
        description="超时时间(秒)",
        validation_alias='TIMEOUT'
    )

    # ========== TTS 配置 ==========
    enable_tts: bool = Field(
        default=False,
        description="是否启用TTS",
        validation_alias='ENABLE_TTS'
    )

    tts_provider: str = Field(
        default="edge",
        description="TTS提供商(edge/azure/openai)",
        validation_alias='TTS_PROVIDER'
    )

    tts_voice: str = Field(
        default="zh-CN-XiaoxiaoNeural",
        description="TTS语音",
        validation_alias='TTS_VOICE'
    )

    tts_rate: str = Field(
        default="+0%",
        description="语速调整",
        validation_alias='TTS_RATE'
    )

    tts_volume: str = Field(
        default="+0%",
        description="音量调整",
        validation_alias='TTS_VOLUME'
    )

    max_chunk_length: int = Field(
        default=100,
        ge=10,
        description="TTS分段最大长度",
        validation_alias='MAX_CHUNK_LENGTH'
    )

    # ========== 日志配置 ==========
    log_level: str = Field(
        default="INFO",
        description="日志级别",
        validation_alias='LOG_LEVEL'
    )

    log_file: Optional[str] = Field(
        default=None,
        description="日志文件路径",
        validation_alias='LOG_FILE'
    )

    # ========== 环境配置 ==========
    environment: str = Field(
        default="development",
        description="运行环境(development/production)",
        validation_alias='ENVIRONMENT'
    )

    debug: bool = Field(
        default=False,
        description="是否调试模式",
        validation_alias='DEBUG'
    )

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'ignore'

    def is_production(self) -> bool:
        """是否生产环境"""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """是否开发环境"""
        return self.environment.lower() == "development"

    def validate_config(self, strict: bool = False) -> None:
        """
        验证配置

        Args:
            strict: 是否严格验证(生产环境应为True)
        """
        errors = []
        warnings = []

        # 验证 API Key
        if not self.openai_api_key or self.openai_api_key == "your-api-key-here":
            if strict:
                errors.append("❌ OPENAI_API_KEY 未设置或无效")
            else:
                warnings.append("⚠️  OPENAI_API_KEY 未设置(测试环境可忽略)")

        # 验证 TTS 配置
        if self.enable_tts:
            valid_providers = ["edge", "azure", "openai"]
            if self.tts_provider not in valid_providers:
                errors.append(f"❌ TTS_PROVIDER 无效,必须是 {valid_providers} 之一")

        if warnings:
            for warning in warnings:
                print(warning)

        if errors:
            raise ValueError("\n".join(["配置验证失败:"] + errors))


# 创建全局配置实例
try:
    settings = Settings()
    # 非严格验证,允许测试环境无API Key
    settings.validate_config(strict=False)
except Exception as e:
    print(f"⚠️  配置加载失败: {e}")
    print("提示: 请检查 .env 文件")
    # 测试环境不抛出异常
    if str(e).startswith("配置验证失败"):
        raise
    else:
        # 创建默认配置
        settings = Settings(openai_api_key="test-key")


# 导出
__all__ = ['settings', 'Settings']
