"""
语音等待反馈模块
用于语音交互Agent的等待提示
还需要找到一个合适的音效文件，作为等待提示
"""
import threading
import time
import random


class VoiceWaitingFeedback:
    """语音等待反馈器"""
    
    def __init__(self, mode='text'):
        """
        Args:
            mode: 'text' - 文本提示（默认）
                  'tts' - TTS语音提示（需要TTS引擎）
                  'audio' - 播放音效文件
                  'beep' - 系统提示音
        """
        self.mode = mode
        self.is_playing = False
        self.thread = None
        
        # 等待提示语
        self.thinking_phrases = [
            "嗯...",
            "让我想想...",
            "稍等一下...",
            "我正在思考...",
        ]
    
    def start(self, context="thinking"):
        """
        开始播放等待反馈
        
        Args:
            context: 'thinking' - 思考中
                    'calling_tool' - 调用工具中
                    'processing' - 处理中
        """
        if self.is_playing:
            return
        
        self.is_playing = True
        
        if self.mode == 'text':
            self._show_text_prompt(context)
        elif self.mode == 'tts':
            self.thread = threading.Thread(
                target=self._play_tts_prompt,
                args=(context,),
                daemon=True
            )
            self.thread.start()
        elif self.mode == 'audio':
            self.thread = threading.Thread(
                target=self._play_audio_loop,
                args=(context,),
                daemon=True
            )
            self.thread.start()
        elif self.mode == 'beep':
            self._play_beep()
    
    def stop(self):
        """停止播放"""
        self.is_playing = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def _show_text_prompt(self, context):
        """显示文本提示"""
        prompts = {
            'thinking': '🤔 Agent正在思考...',
            'calling_tool': '🛠️  正在调用工具...',
            'processing': '⏳ 正在处理...',
        }
        print(f"\n{prompts.get(context, '⏳ 处理中...')}")
    
    def _play_tts_prompt(self, context):
        """TTS语音提示"""
        phrase = random.choice(self.thinking_phrases)
        print(f"🗣️  [TTS] {phrase}")
        # 实际使用时调用TTS引擎：
        # tts_engine.speak(phrase, wait=False)
    
    def _play_audio_loop(self, context):
        """播放音频文件（循环）"""
        # 需要集成音频播放库，如 pygame, pydub 等
        print(f"🔊 [音效] 播放等待音效中...")
        # audio_file = f"sounds/{context}_waiting.wav"
        # while self.is_playing:
        #     pygame.mixer.music.load(audio_file)
        #     pygame.mixer.music.play()
        #     time.sleep(2)
    
    def _play_beep(self):
        """简单提示音"""
        print("\a")  # 系统beep音

