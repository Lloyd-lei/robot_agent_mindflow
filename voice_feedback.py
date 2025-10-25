"""
语音等待反馈模块
用于语音交互Agent的等待提示
支持在工具调用时播放音效
"""
import threading
import time
import random
import os
from pathlib import Path
from logger_config import get_logger

logger = get_logger(__name__)


class VoiceWaitingFeedback:
    """语音等待反馈器 - 支持音效播放"""
    
    def __init__(self, mode='audio', sound_dir='sounds'):
        """
        Args:
            mode: 'text' - 文本提示
                  'audio' - 播放音效文件（推荐）
                  'silent' - 静默模式
            sound_dir: 音效文件目录
        """
        self.mode = mode
        self.is_playing = False
        self.thread = None
        self.sound_dir = Path(sound_dir)
        self._pygame_initialized = False
        
        # 音效文件路径
        self.sounds = {
            'tool_thinking': self.sound_dir / 'tool_thinking.wav',  # 工具调用时的音效
        }
        
        # 等待提示语（文本模式备用）
        self.thinking_phrases = [
            "🛠️  正在调用工具...",
            "⏳ 处理中...",
            "🔧 执行中...",
        ]
        
        # 检查音效文件
        self._check_sound_files()
    
    def _check_sound_files(self):
        """检查音效文件是否存在"""
        if self.mode != 'audio':
            return
        
        missing = []
        for name, path in self.sounds.items():
            if not path.exists():
                missing.append(f"{name} ({path})")
        
        if missing:
            print(f"⚠️  音效文件缺失: {', '.join(missing)}")
            print(f"   降级为文本模式")
            self.mode = 'text'
        else:
            print(f"✅ 音效系统就绪: {len(self.sounds)} 个音效文件")
    
    def start(self, context="tool_thinking"):
        """
        开始播放等待反馈
        
        Args:
            context: 'tool_thinking' - 工具调用中（播放音效）
                    'thinking' - 思考中
        """
        if self.is_playing:
            return
        
        self.is_playing = True
        logger.debug(f"🎵 开始播放音效: {context}")
        
        if self.mode == 'audio' and context in self.sounds:
            self.thread = threading.Thread(
                target=self._play_audio,
                args=(context,),
                daemon=True
            )
            self.thread.start()
            logger.info(f"🎵 音效线程已启动: {context}")
        elif self.mode == 'text':
            self._show_text_prompt(context)
    
    def stop(self):
        """停止播放"""
        self.is_playing = False
        logger.debug("🛑 停止音效播放")
        
        # 停止音频播放
        if self._pygame_initialized:
            try:
                import pygame
                pygame.mixer.music.stop()
                logger.debug("🛑 pygame音频已停止")
            except:
                pass
        
        if self.thread:
            self.thread.join(timeout=0.5)
            logger.debug("🛑 音效线程已结束")
    
    def _show_text_prompt(self, context):
        """显示文本提示（降级方案）"""
        prompts = {
            'thinking': '🤔 思考中...',
            'tool_thinking': '🛠️  调用工具中...',
            'processing': '⏳ 处理中...',
        }
        print(f"{prompts.get(context, '⏳ 处理中...')}", end='', flush=True)
    
    def _play_audio(self, context):
        """播放音效文件"""
        sound_file = self.sounds.get(context)
        if not sound_file or not sound_file.exists():
            print(f"⚠️  音效文件不存在: {sound_file}")
            return
        
        try:
            import pygame
            
            # 初始化 pygame mixer（只初始化一次）
            if not self._pygame_initialized:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                self._pygame_initialized = True
            
            # 加载并播放音效
            pygame.mixer.music.load(str(sound_file))
            pygame.mixer.music.play()
            logger.info(f"🔊 音效播放中: {sound_file.name}")
            
            # 等待播放完成或停止信号
            while pygame.mixer.music.get_busy() and self.is_playing:
                time.sleep(0.1)
            
            # 如果提前停止，淡出
            if self.is_playing and pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(500)  # 0.5秒淡出
                logger.debug("🎵 音效淡出")
            else:
                logger.info("✅ 音效播放完成")
        
        except ImportError:
            print("⚠️  pygame 未安装，无法播放音效")
            print("   请运行: pip install pygame")
            self.mode = 'text'  # 降级到文本模式
        except Exception as e:
            print(f"⚠️  音效播放失败: {e}")
            self.mode = 'text'  # 降级到文本模式

