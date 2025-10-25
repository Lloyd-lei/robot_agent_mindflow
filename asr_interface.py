"""
OpenAI Whisper ASR 接口
支持最高质量的语音识别，自动语言检测
"""
import openai
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from logger_config import get_logger
import config

logger = get_logger(__name__)


@dataclass
class ASRResult:
    """ASR 识别结果"""
    text: str                           # 识别的文本
    language: str                       # 检测到的语言
    duration: float                     # 音频时长（秒）
    processing_time: float              # 处理耗时（秒）
    confidence: Optional[float] = None  # 置信度（如果有）
    segments: Optional[List[Dict]] = None  # 时间戳分段（如果请求）


class OpenAIASR:
    """
    OpenAI Whisper ASR 接口 - 最高质量语音识别
    
    特性：
    - ✅ 自动语言检测（98+ 种语言）
    - ✅ 超高准确率（State-of-the-art）
    - ✅ 支持噪音环境
    - ✅ 支持多种音频格式
    - ✅ 可选时间戳分段
    - ✅ 专业术语优化（prompt）
    
    支持的音频格式：
    - MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM
    
    最大文件大小：25 MB
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        temperature: float = 0.0,
        timeout: int = 30
    ):
        """
        初始化 ASR
        
        Args:
            api_key: OpenAI API Key（None=从 config 读取）
            model: 模型名称（whisper-1 是目前最好的）
            temperature: 温度（0=最确定，0.2=稍微随机）
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        
        # 初始化 OpenAI 客户端
        self.client = openai.OpenAI(
            api_key=self.api_key,
            timeout=timeout
        )
        
        logger.info(f"✅ ASR 初始化成功")
        logger.info(f"   模型: {model}")
        logger.info(f"   语言检测: 自动（98+ 种语言）")
        logger.info(f"   温度: {temperature}")
    
    def transcribe(
        self,
        audio_file: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        return_segments: bool = False,
        verbose: bool = True
    ) -> ASRResult:
        """
        语音识别（同步）
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码（None=自动检测，推荐）
            prompt: 提示词（提升专业术语识别准确率）
            return_segments: 是否返回时间戳分段
            verbose: 是否显示详细信息
        
        Returns:
            ASRResult: 识别结果
        
        Example:
            >>> asr = OpenAIASR()
            >>> result = asr.transcribe("audio.mp3")
            >>> print(f"识别: {result.text}")
            >>> print(f"语言: {result.language}")
            >>> print(f"耗时: {result.processing_time:.2f}秒")
        """
        start_time = time.time()
        
        try:
            # 检查文件存在
            audio_path = Path(audio_file)
            if not audio_path.exists():
                raise FileNotFoundError(f"音频文件不存在: {audio_file}")
            
            # 检查文件大小（OpenAI 限制 25MB）
            file_size = audio_path.stat().st_size
            if file_size > 25 * 1024 * 1024:
                raise ValueError(f"文件过大: {file_size / 1024 / 1024:.1f}MB（最大 25MB）")
            
            if verbose:
                logger.info(f"🎧 开始识别: {audio_path.name} ({file_size / 1024:.1f}KB)")
            
            # 构建 API 参数
            with open(audio_file, "rb") as f:
                kwargs = {
                    "model": self.model,
                    "file": f,
                    "temperature": self.temperature,
                }
                
                # 语言（None=自动检测）
                if language:
                    kwargs["language"] = language
                    if verbose:
                        logger.debug(f"   指定语言: {language}")
                else:
                    if verbose:
                        logger.debug("   自动检测语言")
                
                # 提示词（提升专业术语识别）
                if prompt:
                    kwargs["prompt"] = prompt
                    if verbose:
                        logger.debug(f"   提示词: {prompt[:50]}...")
                
                # 返回格式
                if return_segments:
                    kwargs["response_format"] = "verbose_json"
                    kwargs["timestamp_granularities"] = ["segment"]
                else:
                    kwargs["response_format"] = "verbose_json"  # 获取语言信息
                
                # 调用 OpenAI Whisper API
                response = self.client.audio.transcriptions.create(**kwargs)
            
            processing_time = time.time() - start_time
            
            # 解析结果
            if return_segments:
                result = ASRResult(
                    text=response.text,
                    language=response.language,
                    duration=response.duration,
                    processing_time=processing_time,
                    segments=[
                        {
                            'id': seg.id,
                            'start': seg.start,
                            'end': seg.end,
                            'text': seg.text
                        }
                        for seg in response.segments
                    ]
                )
            else:
                result = ASRResult(
                    text=response.text,
                    language=response.language,
                    duration=response.duration,
                    processing_time=processing_time
                )
            
            if verbose:
                logger.info(f"✅ 识别完成")
                logger.info(f"   文本: {result.text[:100]}{'...' if len(result.text) > 100 else ''}")
                logger.info(f"   语言: {result.language}")
                logger.info(f"   音频时长: {result.duration:.2f}秒")
                logger.info(f"   处理耗时: {result.processing_time:.2f}秒")
                logger.info(f"   速度比: {result.duration / result.processing_time:.1f}x 实时")
            
            return result
        
        except FileNotFoundError as e:
            logger.error(f"❌ 文件错误: {e}")
            raise
        
        except openai.APIError as e:
            logger.error(f"❌ OpenAI API 错误: {e}")
            raise
        
        except Exception as e:
            logger.error(f"❌ ASR 识别失败: {e}")
            raise
    
    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> ASRResult:
        """
        直接识别音频字节流（无需保存文件）
        
        Args:
            audio_bytes: 音频数据
            filename: 虚拟文件名（用于指定格式）
            language: 语言代码（None=自动检测）
            prompt: 提示词
        
        Returns:
            ASRResult: 识别结果
        """
        from io import BytesIO
        
        start_time = time.time()
        
        try:
            # 创建字节流文件对象
            audio_file = BytesIO(audio_bytes)
            audio_file.name = filename
            
            kwargs = {
                "model": self.model,
                "file": audio_file,
                "temperature": self.temperature,
                "response_format": "verbose_json"
            }
            
            if language:
                kwargs["language"] = language
            
            if prompt:
                kwargs["prompt"] = prompt
            
            response = self.client.audio.transcriptions.create(**kwargs)
            
            processing_time = time.time() - start_time
            
            return ASRResult(
                text=response.text,
                language=response.language,
                duration=response.duration,
                processing_time=processing_time
            )
        
        except Exception as e:
            logger.error(f"❌ 字节流识别失败: {e}")
            raise
    
    def transcribe_batch(
        self,
        audio_files: List[str],
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> List[ASRResult]:
        """
        批量识别多个音频文件
        
        Args:
            audio_files: 音频文件列表
            language: 语言代码（None=自动检测）
            prompt: 提示词
        
        Returns:
            识别结果列表
        """
        logger.info(f"📦 批量识别: {len(audio_files)} 个文件")
        
        results = []
        for i, audio_file in enumerate(audio_files, 1):
            logger.info(f"处理 {i}/{len(audio_files)}: {Path(audio_file).name}")
            
            try:
                result = self.transcribe(
                    audio_file=audio_file,
                    language=language,
                    prompt=prompt,
                    verbose=False
                )
                results.append(result)
            
            except Exception as e:
                logger.error(f"❌ 文件 {i} 识别失败: {e}")
                results.append(ASRResult(
                    text="",
                    language="",
                    duration=0,
                    processing_time=0
                ))
        
        logger.info(f"✅ 批量识别完成")
        return results
    
    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言列表
        
        Returns:
            语言代码列表
        """
        # Whisper 支持的主要语言
        return [
            'zh',  # 中文
            'en',  # 英文
            'ja',  # 日文
            'ko',  # 韩文
            'es',  # 西班牙语
            'fr',  # 法语
            'de',  # 德语
            'it',  # 意大利语
            'pt',  # 葡萄牙语
            'ru',  # 俄语
            'ar',  # 阿拉伯语
            'tr',  # 土耳其语
            'vi',  # 越南语
            'th',  # 泰语
            'id',  # 印尼语
            # ... 还有 80+ 种语言
        ]
    
    def estimate_cost(self, audio_duration_seconds: float) -> float:
        """
        估算识别成本
        
        Args:
            audio_duration_seconds: 音频时长（秒）
        
        Returns:
            成本（美元）
        """
        # Whisper-1 定价: $0.006 / 分钟
        minutes = audio_duration_seconds / 60
        cost = minutes * 0.006
        return cost


# 工厂方法
def create_asr(
    provider: str = "openai",
    **kwargs
) -> OpenAIASR:
    """
    创建 ASR 实例
    
    Args:
        provider: ASR 提供商（目前只支持 openai）
        **kwargs: 其他参数
    
    Returns:
        ASR 实例
    """
    if provider.lower() == "openai":
        return OpenAIASR(**kwargs)
    else:
        raise ValueError(f"不支持的 ASR 提供商: {provider}")


