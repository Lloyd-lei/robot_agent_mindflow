"""
对话会话管理器

封装 LLM + TTS 的完整生命周期，提供统一的对外接口
"""

import time
import signal
import atexit
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime

from agent_hybrid import HybridReasoningAgent
from tts_interface import TTSFactory, TTSProvider
from logger_config import get_logger
import config


logger = get_logger(__name__)


@dataclass
class SessionResult:
    """单轮对话结果"""
    response: str           # LLM 回复
    tool_calls: int         # 工具调用次数
    duration: float         # 耗时（秒）
    should_end: bool        # 是否需要结束会话
    streaming_stats: Dict[str, Any] = None  # TTS 流式统计


class SessionTimeoutError(Exception):
    """会话超时异常"""
    pass


class SessionNotStartedError(Exception):
    """会话未启动异常"""
    pass


class ConversationSession:
    """
    对话会话管理器
    
    功能：
    - 封装 LLM + TTS 完整生命周期
    - 自动资源管理（启动/清理）
    - 超时保护（防止卡死）
    - 内存安全（限制队列大小）
    - 日志追踪
    
    使用示例：
    >>> session = ConversationSession(
    ...     llm_provider="ollama",
    ...     tts_provider="edge"
    ... )
    >>> session.start()
    >>> result = session.chat("你好")
    >>> print(result.response)
    >>> session.end()
    
    或使用上下文管理器：
    >>> with ConversationSession() as session:
    ...     result = session.chat("你好")
    """
    
    def __init__(
        self,
        llm_provider: str = None,
        llm_model: str = None,
        tts_provider: str = "edge",
        tts_voice: str = None,
        enable_cache: bool = True,
        show_reasoning: bool = True,
        timeout: int = 60,
        tts_wait_timeout: int = 30
    ):
        """
        初始化会话（不分配资源）
        
        参数：
        - llm_provider: LLM 提供商（None=自动从config读取）
        - llm_model: 模型名称（None=自动从config读取）
        - tts_provider: TTS 提供商（"edge" | "azure" | "openai"）
        - tts_voice: 语音名称（None=使用默认）
        - enable_cache: 是否启用对话历史缓存（KV Cache）
        - show_reasoning: 是否显示推理过程
        - timeout: 单轮对话超时（秒）
        - tts_wait_timeout: TTS 播放等待超时（秒）
        """
        # 配置参数
        self.llm_provider = llm_provider
        self.llm_model = llm_model or config.LLM_MODEL
        self.tts_provider = tts_provider
        self.tts_voice = tts_voice or self._get_default_voice(tts_provider)
        self.enable_cache = enable_cache
        self.show_reasoning = show_reasoning
        self.timeout = timeout
        self.tts_wait_timeout = tts_wait_timeout
        
        # 内部状态
        self._agent: Optional[HybridReasoningAgent] = None
        self._is_started = False
        self._session_id = f"session_{int(time.time())}"
        
        # 对话历史持久化
        self._history_dir = Path("sessions")
        self._history_dir.mkdir(exist_ok=True)
        self._history_file = self._history_dir / f"{self._session_id}.json"
        
        # 注册退出清理
        atexit.register(self._cleanup_on_exit)
        
        logger.info(f"📋 会话已创建: {self._session_id}")
        logger.info(f"   LLM: {self.llm_model} | TTS: {self.tts_provider}")
    
    def start(self):
        """
        启动会话，分配资源
        
        抛出：
        - RuntimeError: 会话已启动
        """
        if self._is_started:
            logger.warning("⚠️  会话已经启动，无需重复启动")
            return
        
        logger.info(f"🚀 启动会话: {self._session_id}")
        
        try:
            # === 初始化 Agent ===
            logger.debug("初始化 HybridReasoningAgent...")
            self._agent = HybridReasoningAgent(
                model=self.llm_model,
                enable_cache=self.enable_cache,
                enable_streaming_tts=True,
                voice_mode=False  # 由会话管理器控制
            )
            
            # === 初始化 TTS ===
            logger.debug(f"初始化 TTS ({self.tts_provider})...")
            self._agent.tts_engine = TTSFactory.create_tts(
                provider=TTSProvider[self.tts_provider.upper()],
                voice=self.tts_voice,
                rate="+15%",
                volume="+10%"
            )
            
            self._is_started = True
            logger.info(f"✅ 会话启动成功")
            
        except Exception as e:
            logger.error(f"❌ 会话启动失败: {e}")
            raise
    
    def chat(self, user_input: str) -> SessionResult:
        """
        单轮对话（阻塞式，带超时保护）
        
        参数：
        - user_input: 用户输入
        
        返回：
        - SessionResult: 对话结果
        
        抛出：
        - SessionNotStartedError: 会话未启动
        - SessionTimeoutError: 对话超时
        """
        if not self._is_started:
            raise SessionNotStartedError("❌ 会话未启动，请先调用 start()")
        
        logger.info(f"💬 用户输入: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
        
        start_time = time.time()
        
        try:
            # 使用超时保护执行对话
            result = self._run_with_timeout(user_input)
            
            duration = time.time() - start_time
            logger.info(f"⚡ 对话完成，耗时: {duration:.2f}秒")
            
            # 自动保存对话历史（支持超时恢复）
            if self.enable_cache:
                self.save_history()
            
            return SessionResult(
                response=result['output'],
                tool_calls=result['tool_calls'],
                duration=duration,
                should_end=result.get('should_end', False),
                streaming_stats=result.get('streaming_stats')
            )
            
        except SessionTimeoutError as e:
            logger.error(f"⏱️  对话超时: {e}")
            # 超时时也保存历史（保留已完成的对话）
            if self.enable_cache and self._agent:
                logger.warning("⚠️  超时发生，但对话历史已保留（支持恢复）")
                self.save_history()
            raise
        except Exception as e:
            logger.error(f"❌ 对话失败: {e}")
            # 异常时也尝试保存（最大程度保留历史）
            if self.enable_cache and self._agent:
                try:
                    self.save_history()
                except:
                    pass
            raise
    
    def _run_with_timeout(self, user_input: str) -> Dict[str, Any]:
        """
        带超时保护的对话执行
        
        使用 signal.alarm 实现超时（仅 Unix 系统）
        """
        def timeout_handler(signum, frame):
            raise SessionTimeoutError(f"对话超时（>{self.timeout}秒）")
        
        # 设置超时信号（仅 Unix）
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
        
        try:
            # 执行对话
            result = self._agent.run_with_streaming_tts(
                user_input,
                show_reasoning=self.show_reasoning,
                tts_wait_timeout=self.tts_wait_timeout  # 传递 TTS 超时参数
            )
            return result
            
        finally:
            # 取消超时信号
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
    
    def reset(self):
        """
        重置对话历史（保持资源）
        """
        if not self._is_started:
            logger.warning("⚠️  会话未启动，无需重置")
            return
        
        logger.info("🔄 重置对话历史...")
        self._agent.clear_cache()
        logger.info("✅ 对话历史已清除")
    
    def end(self):
        """
        结束会话，清理资源
        """
        if not self._is_started:
            logger.warning("⚠️  会话未启动，无需结束")
            return
        
        logger.info(f"🛑 结束会话: {self._session_id}")
        
        try:
            # 停止 TTS 管道
            if self._agent and hasattr(self._agent, 'streaming_pipeline') and self._agent.streaming_pipeline:
                logger.debug("停止 TTS 流式管道...")
                self._agent.streaming_pipeline.stop(wait=True, timeout=5.0)
            
            self._is_started = False
            logger.info("✅ 会话已结束，资源已清理")
            
        except Exception as e:
            logger.error(f"❌ 清理资源失败: {e}")
    
    def _cleanup_on_exit(self):
        """
        程序退出时自动清理（atexit 回调）
        """
        if self._is_started:
            logger.warning("⚠️  检测到程序退出，自动清理资源...")
            self.end()
    
    def _get_default_voice(self, provider: str) -> str:
        """获取默认语音"""
        defaults = {
            "edge": "zh-CN-XiaoxiaoNeural",
            "azure": "zh-CN-XiaoxiaoNeural",
            "openai": "nova"
        }
        return defaults.get(provider.lower(), "zh-CN-XiaoxiaoNeural")
    
    # === 对话历史持久化 ===
    
    def save_history(self, filepath: Optional[Path] = None):
        """
        保存对话历史到文件（支持超时恢复）
        
        参数：
        - filepath: 保存路径（None=使用默认路径）
        """
        if not self._is_started or not self._agent:
            logger.warning("⚠️  会话未启动，无法保存历史")
            return
        
        filepath = filepath or self._history_file
        
        try:
            # 获取对话历史
            history_data = {
                "session_id": self._session_id,
                "created_at": datetime.now().isoformat(),
                "llm_model": self.llm_model,
                "conversation_history": self._agent.conversation_history,
                "turns": len(self._agent.conversation_history) // 2  # 用户+助手=1轮
            }
            
            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 对话历史已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ 保存对话历史失败: {e}")
    
    def load_history(self, filepath: Optional[Path] = None) -> bool:
        """
        从文件加载对话历史（恢复会话）
        
        参数：
        - filepath: 文件路径（None=使用默认路径）
        
        返回：
        - bool: 是否成功加载
        """
        if not self._is_started or not self._agent:
            logger.warning("⚠️  会话未启动，无法加载历史")
            return False
        
        filepath = filepath or self._history_file
        
        if not filepath.exists():
            logger.debug(f"📂 历史文件不存在: {filepath}")
            return False
        
        try:
            # 从文件加载
            with open(filepath, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # 恢复对话历史
            if self.enable_cache:
                self._agent.conversation_history = history_data.get("conversation_history", [])
                turns = history_data.get("turns", 0)
                logger.info(f"📥 对话历史已恢复: {turns}轮对话")
                return True
            else:
                logger.warning("⚠️  缓存未启用，无法恢复历史")
                return False
                
        except Exception as e:
            logger.error(f"❌ 加载对话历史失败: {e}")
            return False
    
    def get_history_summary(self) -> Dict[str, Any]:
        """
        获取对话历史摘要
        
        返回：
        - Dict: 包含对话轮次、消息数等统计信息
        """
        if not self._is_started or not self._agent:
            return {"error": "会话未启动"}
        
        history = self._agent.conversation_history
        return {
            "session_id": self._session_id,
            "total_messages": len(history),
            "turns": len([m for m in history if m.get("role") == "user"]),
            "cache_enabled": self.enable_cache,
            "has_history_file": self._history_file.exists()
        }
    
    # === 上下文管理器支持 ===
    
    def __enter__(self):
        """进入上下文，自动启动会话"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，自动结束会话"""
        self.end()
        return False  # 不抑制异常
    
    # === 属性访问 ===
    
    @property
    def is_started(self) -> bool:
        """会话是否已启动"""
        return self._is_started
    
    @property
    def session_id(self) -> str:
        """会话 ID"""
        return self._session_id


# ============================================================================
# 便捷函数
# ============================================================================

@contextmanager
def create_session(**kwargs):
    """
    便捷的上下文管理器
    
    使用示例：
    >>> with create_session(llm_model="qwen2.5:3b") as session:
    ...     result = session.chat("你好")
    """
    session = ConversationSession(**kwargs)
    try:
        session.start()
        yield session
    finally:
        session.end()


if __name__ == "__main__":
    # 测试会话管理器
    from colorama import init
    init(autoreset=True)
    
    print("=" * 70)
    print("🧪 测试会话管理器")
    print("=" * 70)
    
    # 方式1：手动管理
    session = ConversationSession(llm_model="qwen2.5:3b", timeout=30)
    session.start()
    
    result = session.chat("你好")
    print(f"\n回复: {result.response}")
    print(f"耗时: {result.duration:.2f}秒")
    
    session.end()
    
    # 方式2：上下文管理器
    print("\n" + "=" * 70)
    print("🧪 测试上下文管理器")
    print("=" * 70)
    
    with create_session(llm_model="qwen2.5:3b") as session:
        result = session.chat("现在几点？")
        print(f"\n回复: {result.response}")

