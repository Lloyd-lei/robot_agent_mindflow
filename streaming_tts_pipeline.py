#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流式TTS管道 - Streaming TTS Pipeline
====================================

核心功能：
1. LLM流式输出 → 智能分句 → TTS生成 → 音频播放（全流程无缝对接）
2. 自动背压控制（防止资源爆炸）
3. 资源安全保证（有界队列、线程池、超时机制）
4. 优雅关闭（保证资源释放）

架构：
    LLM Streaming → Text Queue → TTS Generator → Audio PriorityQueue → Audio Player
                      (背压)                        (背压)

"""

import queue
from queue import PriorityQueue
import threading
import time
import io
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import re


# ============================================================================
# 数据结构
# ============================================================================

class PipelineStatus(Enum):
    """管道状态"""
    IDLE = "idle"           # 空闲
    RUNNING = "running"     # 运行中
    STOPPING = "stopping"   # 正在停止
    STOPPED = "stopped"     # 已停止
    ERROR = "error"         # 错误


@dataclass
class TextChunk:
    """文本块"""
    chunk_id: int
    text: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class AudioChunk:
    """音频块"""
    chunk_id: int
    text: str
    audio_data: bytes
    duration: float = 0.0
    generation_time: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        """用于优先级队列排序（保证顺序播放）"""
        return self.chunk_id < other.chunk_id


@dataclass
class PipelineStats:
    """管道统计信息"""
    text_received: int = 0      # 接收的文本数
    text_dropped: int = 0       # 丢弃的文本数
    audio_generated: int = 0    # 生成的音频数
    audio_failed: int = 0       # 生成失败的音频数
    audio_played: int = 0       # 播放成功的音频数
    audio_play_failed: int = 0  # 播放失败的音频数
    
    total_generation_time: float = 0.0  # 总生成时间
    total_playback_time: float = 0.0    # 总播放时间
    
    text_queue_size: int = 0
    audio_queue_size: int = 0
    active_tasks: int = 0
    threads_alive: int = 0
    is_playing: bool = False    # 是否正在播放音频（关键！）
    
    def to_dict(self) -> Dict[str, Any]:
        """转为字典"""
        return {
            'text_received': self.text_received,
            'text_dropped': self.text_dropped,
            'audio_generated': self.audio_generated,
            'audio_failed': self.audio_failed,
            'audio_played': self.audio_played,
            'audio_play_failed': self.audio_play_failed,
            'total_generation_time': f"{self.total_generation_time:.2f}s",
            'total_playback_time': f"{self.total_playback_time:.2f}s",
            'text_queue_size': self.text_queue_size,
            'audio_queue_size': self.audio_queue_size,
            'active_tasks': self.active_tasks,
            'threads_alive': self.threads_alive,
        }


# ============================================================================
# 智能文本分句器
# ============================================================================

class SmartSentenceSplitter:
    """
    智能分句器（优化版）
    
    特点：
    - 按标点符号分句（。！？；等）
    - 合并短句（避免碎片化）
    - 支持英文和中文
    - 实时流式输出
    - 自动清理 markdown/代码/特殊符号（新增）
    """
    
    def __init__(self, 
                 min_chunk_length: int = 3,
                 max_chunk_length: int = 150):
        self.min_chunk_length = min_chunk_length
        self.max_chunk_length = max_chunk_length
        
        # 句子结束标点
        self.sentence_end_pattern = re.compile(r'[。！？；.!?;]')
        
        # 缓冲区
        self.buffer = ""
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本为 TTS 友好格式
        
        功能：
        - 移除 markdown 格式（代码块、加粗、斜体、链接等）
        - 展开英文缩写（AI → 人工智能）
        - 移除列表标记和标题符号
        - 清理多余空白
        """
        if not text:
            return ""
        
        # === 1. 清除 Markdown 格式 ===
        # 移除代码块
        text = re.sub(r'```[\s\S]*?```', '[代码内容]', text)
        # 移除行内代码
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # 移除链接 [文本](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # 移除 markdown 标题 (# ## ### 等)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 移除列表标记
        text = re.sub(r'^\s*[-*+•]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        # 移除加粗 **text** 或 __text__
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        # 移除斜体 *text* 或 _text_
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        # 移除多余换行（3个以上换行符）
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 移除 JSON 格式提示
        text = re.sub(r'\{[\s\S]*?".*?"[\s\S]*?\}', '', text)
        
        # === 2. 展开英文缩写（TTS 友好） ===
        abbreviations = {
            'AI': '人工智能',
            'TTS': '文字转语音',
            'API': 'A P I',
            'WiFi': 'Wi-Fi',
            'JSON': 'JSON格式',
            'HTTP': 'HTTP',
            'HTTPS': 'HTTPS',
            'URL': 'U R L',
            'LLM': '大语言模型',
            'NLP': '自然语言处理',
            'Ollama': 'Ollama',
            'Qwen': 'Qwen',
            'GPT': 'GPT',
            'ML': '机器学习',
            'DL': '深度学习',
            'CPU': 'CPU',
            'GPU': 'GPU',
            'RAM': '内存',
        }
        for abbr, full in abbreviations.items():
            # 🔧 修复：适配中文环境，匹配独立的缩写词
            # 匹配条件：前后是非字母字符或边界（兼容中文）
            pattern = r'(?<![A-Za-z])' + re.escape(abbr) + r'(?![A-Za-z])'
            text = re.sub(pattern, full, text)
        
        # === 3. 清理多余空格 ===
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def add_text(self, text: str) -> List[str]:
        """
        添加文本，返回完整的句子
        
        Args:
            text: 新增的文本
            
        Returns:
            完整的句子列表（可能为空）
        """
        # 🔧 关键修改：先清理文本再加入缓冲区！
        cleaned_text = self._clean_text(text)
        self.buffer += cleaned_text
        sentences = []
        
        while True:
            # 查找句子结束位置
            match = self.sentence_end_pattern.search(self.buffer)
            
            if match:
                end_pos = match.end()
                sentence = self.buffer[:end_pos].strip()
                
                # 如果句子长度合适，输出
                if len(sentence) >= self.min_chunk_length:
                    sentences.append(sentence)
                    self.buffer = self.buffer[end_pos:]
                else:
                    # 句子太短，继续累积
                    # 检查后面还有没有内容
                    if len(self.buffer) > end_pos:
                        # 继续查找下一个句子
                        continue
                    else:
                        # 没有更多内容了，等待新文本
                        break
            else:
                # 没有找到句子结束，检查是否超长
                if len(self.buffer) >= self.max_chunk_length:
                    # 强制切分（按最大长度）
                    sentence = self.buffer[:self.max_chunk_length].strip()
                    if sentence:
                        sentences.append(sentence)
                    self.buffer = self.buffer[self.max_chunk_length:]
                else:
                    # 等待更多文本
                    break
        
        return sentences
    
    def flush(self) -> Optional[str]:
        """
        清空缓冲区，返回剩余文本
        
        Returns:
            剩余的文本（如果有）
        """
        if self.buffer.strip():
            sentence = self.buffer.strip()
            self.buffer = ""
            return sentence
        return None


# ============================================================================
# 流式TTS管道
# ============================================================================

class StreamingTTSPipeline:
    """
    流式TTS管道
    
    资源限制：
    - 文本队列: 最多3个句子 (< 10KB)
    - 音频队列: 最多2个音频 (< 200KB)
    - 生成线程: 固定1个
    - 播放线程: 固定1个
    - 最大任务数: 10个
    
    总内存: < 500KB (可控)
    总线程: 2个 (固定)
    """
    
    def __init__(self,
                 tts_engine,
                 text_queue_size: int = 3,
                 audio_queue_size: int = 2,
                 max_tasks: int = 10,
                 generation_timeout: float = 10.0,
                 playback_timeout: float = 30.0,
                 min_chunk_length: int = 10,
                 max_chunk_length: int = 100,
                 verbose: bool = True):
        """
        初始化流式TTS管道
        
        Args:
            tts_engine: TTS引擎（实现 synthesize 方法）
            text_queue_size: 文本队列大小（背压限制1）
            audio_queue_size: 音频队列大小（背压限制2）
            max_tasks: 最大任务数（背压限制3）
            generation_timeout: TTS生成超时
            playback_timeout: 音频播放超时
            min_chunk_length: 最小句子长度
            max_chunk_length: 最大句子长度
            verbose: 是否输出详细日志
        """
        self.tts_engine = tts_engine
        self.generation_timeout = generation_timeout
        self.playback_timeout = playback_timeout
        self.verbose = verbose
        
        # === 资源限制配置 ===
        self.text_queue = queue.Queue(maxsize=text_queue_size)
        self.audio_queue = PriorityQueue(maxsize=audio_queue_size)  # 使用优先级队列保证顺序
        self.max_tasks = max_tasks
        
        # === 智能分句器 ===
        self.splitter = SmartSentenceSplitter(
            min_chunk_length=min_chunk_length,
            max_chunk_length=max_chunk_length
        )
        
        # === 控制信号 ===
        self.status = PipelineStatus.IDLE
        self.stop_event = threading.Event()
        self.error_event = threading.Event()
        self.stats_lock = threading.Lock()
        
        # === 播放状态（关键：防止过早停止）===
        self.is_playing = False
        self.playing_lock = threading.Lock()
        
        # === 统计 ===
        self.stats = PipelineStats()
        
        # === 计数器 ===
        self.chunk_counter = 0
        
        # === 线程 ===
        self.gen_thread: Optional[threading.Thread] = None
        self.play_thread: Optional[threading.Thread] = None
        
        # === pygame 初始化标志 ===
        self.pygame_initialized = False
    
    def _log(self, message: str):
        """输出日志"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] {message}")
    
    def start(self):
        """启动管道"""
        if self.status == PipelineStatus.RUNNING:
            self._log("⚠️  管道已在运行中")
            return
        
        self._log("🚀 启动流式TTS管道...")
        
        # 重置状态
        self.stop_event.clear()
        self.error_event.clear()
        self.status = PipelineStatus.RUNNING
        
        # 创建生成线程
        self.gen_thread = threading.Thread(
            target=self._generation_loop,
            daemon=True,
            name="TTS-Generator"
        )
        
        # 创建播放线程
        self.play_thread = threading.Thread(
            target=self._playback_loop,
            daemon=True,
            name="TTS-Player"
        )
        
        # 启动线程
        self.gen_thread.start()
        self.play_thread.start()
        
        self._log("✅ 管道启动成功")
    
    def add_text_from_llm(self, text: str, timeout: float = 5.0) -> bool:
        """
        从LLM接收文本（带智能分句和背压）
        
        Args:
            text: LLM输出的文本（可能是部分句子）
            timeout: 队列放入超时
            
        Returns:
            True: 至少有一个句子成功加入队列
            False: 所有句子都被丢弃（背压生效）
        """
        # 智能分句
        sentences = self.splitter.add_text(text)
        
        if not sentences:
            # 还没有完整句子，继续等待
            return True
        
        # 将句子加入队列
        success_count = 0
        for sentence in sentences:
            if self._add_sentence_to_queue(sentence, timeout):
                success_count += 1
        
        return success_count > 0
    
    def flush_remaining_text(self) -> bool:
        """
        刷新缓冲区，处理剩余文本
        
        Returns:
            True: 成功
            False: 失败
        """
        remaining = self.splitter.flush()
        if remaining:
            return self._add_sentence_to_queue(remaining, timeout=5.0)
        return True
    
    def _add_sentence_to_queue(self, sentence: str, timeout: float) -> bool:
        """
        将句子加入文本队列（带背压控制）
        
        Args:
            sentence: 完整句子
            timeout: 超时时间
            
        Returns:
            True: 成功加入
            False: 队列满，被丢弃
        """
        # 检查任务数限制
        with self.stats_lock:
            if self.stats.active_tasks >= self.max_tasks:
                self._log(f"⚠️  任务数达到上限({self.max_tasks})，丢弃句子")
                self.stats.text_dropped += 1
                return False
        
        try:
            # 创建文本块
            chunk = TextChunk(
                chunk_id=self.chunk_counter,
                text=sentence
            )
            self.chunk_counter += 1
            
            # 尝试加入队列（带超时，背压触发点）
            self.text_queue.put(chunk, block=True, timeout=timeout)
            
            with self.stats_lock:
                self.stats.text_received += 1
                self.stats.active_tasks += 1
            
            self._log(f"📝 [接收 {chunk.chunk_id}] {sentence[:40]}...")
            return True
            
        except queue.Full:
            # 队列满了（背压触发）
            with self.stats_lock:
                self.stats.text_dropped += 1
            self._log(f"⚠️  文本队列满，丢弃: {sentence[:30]}...")
            return False
    
    def _generation_loop(self):
        """TTS生成循环"""
        self._log("🔄 TTS生成线程启动")
        
        while not self.stop_event.is_set() and not self.error_event.is_set():
            try:
                # 从文本队列取出（阻塞等待）
                try:
                    text_chunk = self.text_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                self._log(f"🔄 [生成 {text_chunk.chunk_id}] {text_chunk.text[:40]}...")
                
                # 生成音频
                gen_start = time.perf_counter()
                try:
                    audio_data = self._call_tts_with_timeout(text_chunk.text)
                    gen_time = time.perf_counter() - gen_start
                    
                    # 创建音频块
                    audio_chunk = AudioChunk(
                        chunk_id=text_chunk.chunk_id,
                        text=text_chunk.text,
                        audio_data=audio_data,
                        generation_time=gen_time
                    )
                    
                    # 放入优先级队列（无限等待，绝不丢弃）
                    wait_count = 0
                    while True:
                        try:
                            # 使用优先级队列，以 chunk_id 为优先级
                            self.audio_queue.put(audio_chunk, block=True, timeout=30.0)
                            break  # 成功就退出
                        except queue.Full:
                            wait_count += 1
                            self._log(f"⚠️  音频队列满，等待中...（第{wait_count}次，chunk {text_chunk.chunk_id}）")
                            # 继续循环，直到成功放入
                    
                    with self.stats_lock:
                        self.stats.audio_generated += 1
                        self.stats.total_generation_time += gen_time
                    
                    if wait_count > 0:
                        self._log(f"✅ [生成完成 {text_chunk.chunk_id}] "
                                f"{len(audio_data):,} bytes, {gen_time:.2f}s（等待了{wait_count}次）")
                    else:
                        self._log(f"✅ [生成完成 {text_chunk.chunk_id}] "
                                f"{len(audio_data):,} bytes, {gen_time:.2f}s")
                
                except Exception as e:
                    with self.stats_lock:
                        self.stats.audio_failed += 1
                    self._log(f"❌ [生成失败 {text_chunk.chunk_id}] {e}")
                
                finally:
                    with self.stats_lock:
                        self.stats.active_tasks -= 1
                    
            except Exception as e:
                self._log(f"❌ 生成线程错误: {e}")
                self.error_event.set()
                break
        
        self._log("🛑 TTS生成线程停止")
    
    def _playback_loop(self):
        """播放循环"""
        self._log("🔊 音频播放线程启动")
        
        # 初始化pygame（只初始化一次）
        if not self.pygame_initialized:
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                self.pygame_initialized = True
                self._log("✅ pygame初始化成功")
            except Exception as e:
                self._log(f"❌ pygame初始化失败: {e}")
                self.error_event.set()
                return
        
        while not self.stop_event.is_set() and not self.error_event.is_set():
            try:
                # 从优先级队列取出（阻塞等待，自动按 chunk_id 排序）
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # 设置播放状态（关键！）
                with self.playing_lock:
                    self.is_playing = True
                
                self._log(f"🔊 [播放 {audio_chunk.chunk_id}] {audio_chunk.text[:40]}...")
                
                # 播放音频
                play_start = time.perf_counter()
                success = self._play_audio(audio_chunk.audio_data)
                play_time = time.perf_counter() - play_start
                
                # 清除播放状态（关键！）
                with self.playing_lock:
                    self.is_playing = False
                
                if success:
                    with self.stats_lock:
                        self.stats.audio_played += 1
                        self.stats.total_playback_time += play_time
                    
                    self._log(f"✅ [播放完成 {audio_chunk.chunk_id}] {play_time:.2f}s")
                else:
                    with self.stats_lock:
                        self.stats.audio_play_failed += 1
                    self._log(f"❌ [播放失败 {audio_chunk.chunk_id}]")
                    
            except Exception as e:
                self._log(f"❌ 播放线程错误: {e}")
                self.error_event.set()
                break
        
        self._log("🛑 音频播放线程停止")
    
    def _call_tts_with_timeout(self, text: str) -> bytes:
        """
        调用TTS（带超时）
        
        Args:
            text: 要合成的文本
            
        Returns:
            音频数据
            
        Raises:
            TimeoutError: 超时
            Exception: TTS调用失败
        """
        # 检查TTS引擎是否为异步
        if asyncio.iscoroutinefunction(self.tts_engine.synthesize):
            # 异步TTS
            async def _async_call():
                return await asyncio.wait_for(
                    self.tts_engine.synthesize(text),
                    timeout=self.generation_timeout
                )
            
            return asyncio.run(_async_call())
        else:
            # 同步TTS（需要用线程实现超时）
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.tts_engine.synthesize, text)
                try:
                    return future.result(timeout=self.generation_timeout)
                except concurrent.futures.TimeoutError:
                    future.cancel()
                    raise TimeoutError(f"TTS生成超时 ({self.generation_timeout}s)")
    
    def _play_audio(self, audio_data: bytes) -> bool:
        """
        播放音频（阻塞式）
        
        Args:
            audio_data: 音频数据
            
        Returns:
            True: 播放成功
            False: 播放失败
        """
        try:
            import pygame
            
            # 加载音频
            audio_io = io.BytesIO(audio_data)
            pygame.mixer.music.load(audio_io)
            
            # 播放
            pygame.mixer.music.play()
            
            # 等待播放完成（带超时）
            start_time = time.time()
            while pygame.mixer.music.get_busy():
                if self.stop_event.is_set():
                    pygame.mixer.music.stop()
                    return False
                
                # 超时检查
                if time.time() - start_time > self.playback_timeout:
                    pygame.mixer.music.stop()
                    raise TimeoutError("播放超时")
                
                time.sleep(0.01)
            
            return True
            
        except Exception as e:
            self._log(f"❌ 播放错误: {e}")
            return False
    
    def get_stats(self) -> PipelineStats:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        with self.stats_lock:
            # 更新队列大小
            self.stats.text_queue_size = self.text_queue.qsize()
            self.stats.audio_queue_size = self.audio_queue.qsize()
            
            # 更新播放状态（关键！）
            with self.playing_lock:
                self.stats.is_playing = self.is_playing
            
            # 更新线程状态
            threads_alive = 0
            if self.gen_thread and self.gen_thread.is_alive():
                threads_alive += 1
            if self.play_thread and self.play_thread.is_alive():
                threads_alive += 1
            self.stats.threads_alive = threads_alive
            
            return self.stats
    
    def stop(self, wait: bool = True, timeout: float = 5.0):
        """
        停止管道（优雅关闭）
        
        Args:
            wait: 是否等待线程结束
            timeout: 等待超时时间
        """
        if self.status == PipelineStatus.STOPPED:
            self._log("⚠️  管道已经停止")
            return
        
        self._log("🛑 停止流式TTS管道...")
        self.status = PipelineStatus.STOPPING
        
        # 刷新缓冲区
        self.flush_remaining_text()
        
        # 设置停止信号
        self.stop_event.set()
        
        if wait:
            # 等待线程结束
            if self.gen_thread:
                self.gen_thread.join(timeout=timeout)
            if self.play_thread:
                self.play_thread.join(timeout=timeout)
        
        self.status = PipelineStatus.STOPPED
        
        # 输出最终统计
        stats = self.get_stats()
        self._log("=" * 70)
        self._log("📊 管道最终统计:")
        for key, value in stats.to_dict().items():
            self._log(f"   {key}: {value}")
        self._log("=" * 70)
        self._log("✅ 管道已停止")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


# ============================================================================
# 便捷接口
# ============================================================================

def create_streaming_pipeline(tts_engine, **kwargs) -> StreamingTTSPipeline:
    """
    创建流式TTS管道（工厂函数）
    
    Args:
        tts_engine: TTS引擎
        **kwargs: 其他参数（传递给 StreamingTTSPipeline）
        
    Returns:
        流式TTS管道实例
    """
    return StreamingTTSPipeline(tts_engine, **kwargs)


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == "__main__":
    print("🧪 流式TTS管道测试\n")
    
    # 1. 测试智能分句器
    print("=" * 70)
    print("测试1: 智能分句器")
    print("=" * 70)
    
    splitter = SmartSentenceSplitter(min_chunk_length=5, max_chunk_length=50)
    
    test_texts = [
        "你好",
        "，我是",
        "AI助手。",
        "今天天气很好",
        "！你想",
        "做什么",
        "呢？"
    ]
    
    for text in test_texts:
        sentences = splitter.add_text(text)
        if sentences:
            for s in sentences:
                print(f"✅ 完整句子: {s}")
    
    remaining = splitter.flush()
    if remaining:
        print(f"✅ 剩余文本: {remaining}")
    
    print()
    
    # 2. 测试流式管道（模拟模式）
    print("=" * 70)
    print("测试2: 流式TTS管道（模拟TTS）")
    print("=" * 70)
    
    class MockTTS:
        """模拟TTS引擎"""
        async def synthesize(self, text: str) -> bytes:
            import asyncio
            await asyncio.sleep(0.1)  # 模拟生成延迟
            return f"AUDIO:{text}".encode('utf-8')
    
    mock_tts = MockTTS()
    
    with create_streaming_pipeline(
        tts_engine=mock_tts,
        text_queue_size=3,
        audio_queue_size=2,
        max_tasks=5,
        verbose=True
    ) as pipeline:
        
        # 模拟LLM流式输出
        llm_outputs = [
            "今天",
            "天气",
            "真不错。",
            "我们",
            "去",
            "公园",
            "散步吧！",
            "那里",
            "风景",
            "很美。"
        ]
        
        for output in llm_outputs:
            pipeline.add_text_from_llm(output)
            time.sleep(0.2)  # 模拟LLM生成速度
        
        # 等待处理完成
        print("\n⏳ 等待处理完成...")
        time.sleep(3)
    
    print("\n✅ 测试完成！")

