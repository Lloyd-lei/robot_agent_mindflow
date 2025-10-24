"""
TTS 范型接口模块
支持多种 TTS 服务的统一接口，方便切换
后续添加多语种tts范型，现在只支持中文。由agent自己识别语言
"""
from abc import ABC, abstractmethod
from typing import Optional, List
import asyncio
from enum import Enum


class TTSProvider(Enum):
    """TTS 服务提供商"""
    EDGE = "edge"
    AZURE = "azure"
    OPENAI = "openai"


class BaseTTS(ABC):
    """TTS 抽象基类 - 所有 TTS 实现必须继承此类"""
    
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """
        合成语音（异步）
        
        Args:
            text: 要合成的文本
            
        Returns:
            bytes: 音频数据（MP3/WAV格式）
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[str]:
        """获取可用的语音列表"""
        pass
    
    @abstractmethod
    def set_voice(self, voice_name: str):
        """设置语音"""
        pass


class EdgeTTS(BaseTTS):
    """Edge TTS 实现"""
    
    def __init__(
        self,
        voice: str = "zh-CN-XiaoxiaoNeural",  # 晓晓（温柔女声）
        rate: str = "+10%",      # 语速：-50% 到 +50%
        volume: str = "+0%",    # 音量：-50% 到 +50%
        pitch: str = "+0Hz"     # 音调：-50Hz 到 +50Hz
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        
        # 导入 edge-tts
        try:
            import edge_tts
            self.edge_tts = edge_tts
        except ImportError:
            raise ImportError(
                "❌ Edge TTS 未安装！\n"
                "请运行: pip install edge-tts"
            )
    
    async def synthesize(self, text: str) -> bytes:
        """
        使用 Edge TTS 合成语音
        
        Args:
            text: 要合成的文本
            
        Returns:
            bytes: MP3 音频数据
        """
        communicate = self.edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch
        )
        
        # 收集所有音频数据
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        return audio_data
    
    def get_available_voices(self) -> List[str]:
        """获取推荐的中文语音列表"""
        return [
            "zh-CN-XiaoxiaoNeural",  # 晓晓 - 温柔女声（推荐）
            "zh-CN-XiaomoNeural",    # 晓墨 - 知性女声
            "zh-CN-XiaoyiNeural",    # 晓伊 - 成熟女声
            "zh-CN-YunxiNeural",     # 云希 - 阳光男声（推荐）
            "zh-CN-YunyangNeural",   # 云扬 - 新闻男声
            "zh-CN-YunjianNeural",   # 云健 - 体育男声
        ]
    
    def set_voice(self, voice_name: str):
        """设置语音"""
        self.voice = voice_name
    
    def set_rate(self, rate: str):
        """设置语速，例如：'+10%' 或 '-10%'"""
        self.rate = rate
    
    def set_volume(self, volume: str):
        """设置音量，例如：'+10%' 或 '-10%'"""
        self.volume = volume
    
    def set_pitch(self, pitch: str):
        """设置音调，例如：'+5Hz' 或 '-5Hz'"""
        self.pitch = pitch


class AzureTTS(BaseTTS):
    """Azure TTS 实现 - 官方付费服务（预留接口）"""
    
    def __init__(self, api_key: str, region: str = "eastasia", voice: str = "zh-CN-XiaoxiaoNeural"):
        self.api_key = api_key
        self.region = region
        self.voice = voice
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            self.speechsdk = speechsdk
        except ImportError:
            raise ImportError(
                "❌ Azure Speech SDK 未安装！\n"
                "请运行: pip install azure-cognitiveservices-speech"
            )
        
        # 初始化配置
        self.speech_config = self.speechsdk.SpeechConfig(
            subscription=api_key,
            region=region
        )
        self.speech_config.speech_synthesis_voice_name = voice
    
    async def synthesize(self, text: str) -> bytes:
        """使用 Azure TTS 合成语音"""
        synthesizer = self.speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=None  # 返回音频数据而不是播放
        )
        
        result = synthesizer.speak_text_async(text).get()
        
        if result.reason == self.speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        else:
            raise Exception(f"Azure TTS 合成失败: {result.reason}")
    
    def get_available_voices(self) -> List[str]:
        return [
            "zh-CN-XiaoxiaoNeural",
            "zh-CN-XiaomoNeural",
            "zh-CN-XiaoyiNeural",
            "zh-CN-YunxiNeural",
            "zh-CN-YunyangNeural",
        ]
    
    def set_voice(self, voice_name: str):
        self.voice = voice_name
        self.speech_config.speech_synthesis_voice_name = voice_name


class OpenAITTS(BaseTTS):
    """OpenAI TTS 实现 - 官方付费服务（预留接口）"""
    
    def __init__(self, api_key: str, model: str = "tts-1", voice: str = "alloy"):
        self.api_key = api_key
        self.model = model
        self.voice = voice
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError(
                "❌ OpenAI SDK 未安装！\n"
                "请运行: pip install openai"
            )
    
    async def synthesize(self, text: str) -> bytes:
        """使用 OpenAI TTS 合成语音"""
        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text
        )
        return response.content
    
    def get_available_voices(self) -> List[str]:
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    def set_voice(self, voice_name: str):
        self.voice = voice_name


class TTSFactory:
    """TTS 工厂类 - 根据配置创建对应的 TTS 实例"""
    
    @staticmethod
    def create_tts(
        provider: TTSProvider = TTSProvider.EDGE,
        **kwargs
    ) -> BaseTTS:
        """
        创建 TTS 实例
        
        Args:
            provider: TTS 服务提供商
            **kwargs: 各个 TTS 服务的特定参数
            
        Returns:
            BaseTTS: TTS 实例
            
        Examples:
            # Edge TTS（免费）
            tts = TTSFactory.create_tts(
                provider=TTSProvider.EDGE,
                voice="zh-CN-XiaoxiaoNeural"
            )
            
            # Azure TTS（付费）
            tts = TTSFactory.create_tts(
                provider=TTSProvider.AZURE,
                api_key="your_key",
                region="eastasia",
                voice="zh-CN-XiaoxiaoNeural"
            )
            
            # OpenAI TTS（付费）
            tts = TTSFactory.create_tts(
                provider=TTSProvider.OPENAI,
                api_key="your_key",
                model="tts-1",
                voice="alloy"
            )
        """
        if provider == TTSProvider.EDGE:
            return EdgeTTS(**kwargs)
        elif provider == TTSProvider.AZURE:
            return AzureTTS(**kwargs)
        elif provider == TTSProvider.OPENAI:
            return OpenAITTS(**kwargs)
        else:
            raise ValueError(f"不支持的 TTS 提供商: {provider}")


# 同步包装器（方便在非异步环境中使用）
class TTSSync:
    """同步 TTS 包装器"""
    
    def __init__(self, tts_instance: BaseTTS):
        self.tts = tts_instance
    
    def synthesize(self, text: str) -> bytes:
        """同步合成语音"""
        return asyncio.run(self.tts.synthesize(text))


if __name__ == "__main__":
    # 测试 Edge TTS
    print("🧪 测试 Edge TTS...")
    
    async def test_edge_tts():
        tts = TTSFactory.create_tts(
            provider=TTSProvider.EDGE,
            voice="zh-CN-XiaoxiaoNeural"
        )
        
        print(f"✅ 创建 Edge TTS 实例")
        print(f"   当前语音: {tts.voice}")
        print(f"   可用语音: {tts.get_available_voices()[:3]}...")
        
        # 合成测试
        audio_data = await tts.synthesize("你好，这是 Edge TTS 测试。")
        print(f"✅ 合成成功！音频大小: {len(audio_data)} 字节")
        
        # 保存到文件
        with open("test_edge_tts.mp3", "wb") as f:
            f.write(audio_data)
        print(f"✅ 已保存到 test_edge_tts.mp3")
    
    asyncio.run(test_edge_tts())

