"""
TTS优化器模块
包含：
1. 文本优化（清理格式、智能分句、TTS友好转换）
2. 音频播放管理（防重叠、处理乱序、失败重试）
3. 生产级可靠性保障
"""

import re
import time
import threading
import queue
import io
import asyncio
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError


# ============================================================
# 数据结构
# ============================================================

class AudioStatus(Enum):
    """音频状态"""
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
    PLAYING = "playing"
    COMPLETED = "completed"


@dataclass
class AudioChunk:
    """音频分片（带状态管理）"""
    chunk_id: int
    text: str
    audio_data: Optional[bytes] = None
    pause_after: int = 500
    status: AudioStatus = AudioStatus.PENDING
    retry_count: int = 0
    error_message: str = ""
    duration: float = 0.0


# ============================================================
# 文本优化器
# ============================================================

class TTSTextOptimizer:
    """TTS文本优化器 - 将AI输出转换为TTS友好格式"""
    
    def __init__(self, max_chunk_length: int = 100):
        """
        Args:
            max_chunk_length: 单个分段最大字符数
        """
        self.max_chunk_length = max_chunk_length
    
    def optimize(self, text: str) -> List[Dict]:
        """
        优化文本为TTS友好格式
        
        Args:
            text: 原始AI输出文本
            
        Returns:
            [
                {
                    'chunk_id': 0,
                    'text': '处理后的文本',
                    'pause_after': 500,
                    'length': 10
                }
            ]
        """
        # 1. 清理格式
        clean_text = self._clean_formats(text)
        
        if not clean_text.strip():
            return []
        
        # 2. 智能分句
        sentences = self._smart_split(clean_text)
        
        # 3. 处理长句
        chunks = []
        for sent in sentences:
            if len(sent) > self.max_chunk_length:
                chunks.extend(self._split_long_sentence(sent))
            else:
                chunks.append(sent)
        
        # 4. 生成TTS结构
        result = []
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            
            result.append({
                'chunk_id': i,
                'text': self._normalize_for_tts(chunk),
                'pause_after': self._calculate_pause(chunk),
                'length': len(chunk)
            })
        
        return result
    
    def _clean_formats(self, text: str) -> str:
        """清除markdown和特殊格式"""
        # 移除代码块
        text = re.sub(r'```[\s\S]*?```', '[代码内容]', text)
        # 移除行内代码
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # 移除链接
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # 移除markdown标题
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 移除列表标记
        text = re.sub(r'^\s*[-*+•]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        # 移除加粗斜体
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        # 移除多余换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 移除JSON格式提示（如果有）
        text = re.sub(r'\{[\s\S]*?".*?"[\s\S]*?\}', '', text)
        
        return text.strip()
    
    def _smart_split(self, text: str) -> List[str]:
        """智能分句 - 考虑语义完整性"""
        sentences = []
        current = ""
        
        for i, char in enumerate(text):
            current += char
            
            # 句号、问号、感叹号
            if char in '。！？.!?':
                if self._is_sentence_end(text, i):
                    sentences.append(current.strip())
                    current = ""
            
            # 逗号/分号（长句时分割）
            elif char in '，；,;' and len(current) > 50:
                if i + 1 < len(text) and not text[i + 1].isdigit():
                    sentences.append(current.strip())
                    current = ""
        
        if current.strip():
            sentences.append(current.strip())
        
        return [s for s in sentences if s]
    
    def _is_sentence_end(self, text: str, pos: int) -> bool:
        """判断是否真正的句子结束"""
        # 检查后面是否有引号
        if pos + 1 < len(text) and text[pos + 1] in '""』】':
            return False
        # 检查是否是省略号
        if pos + 2 < len(text) and text[pos:pos+3] in ['...', '。。。']:
            return False
        # 检查是否在数字中（3.14）
        if pos > 0 and pos + 1 < len(text):
            if text[pos - 1].isdigit() and text[pos + 1].isdigit():
                return False
        return True
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """拆分长句子"""
        chunks = []
        current = ""
        
        for word in re.split(r'([，；,;、])', sentence):
            if len(current + word) <= self.max_chunk_length:
                current += word
            else:
                if current:
                    chunks.append(current.strip())
                current = word
        
        if current:
            chunks.append(current.strip())
        
        return chunks
    
    def _normalize_for_tts(self, text: str) -> str:
        """标准化为TTS友好格式"""
        # 英文缩写展开
        abbreviations = {
            'AI': '人工智能',
            'TTS': '文字转语音',
            'API': 'A P I',
            'WiFi': 'Wi-Fi',
            'JSON': 'JSON格式',
            'HTTP': 'HTTP',
            'URL': 'U R L',
        }
        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)
        
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _calculate_pause(self, chunk: str) -> int:
        """计算停顿时长（毫秒）"""
        if chunk.endswith(('。', '.', '！', '!', '？', '?')):
            return 30  # 长停顿
        elif chunk.endswith(('，', ',', '；', ';')):
            return 20  # 中停顿
        else:
            return 10  # 短停顿


# ============================================================
# 音频播放管理器
# ============================================================

class TTSAudioManager:
    """
    TTS音频播放管理器
    
    功能：
    1. 防止重叠播放（互斥锁）
    2. 处理乱序/失败（有序字典 + 重试）
    3. 并发生成 + 顺序播放
    4. 超时控制和降级
    """
    
    def __init__(self,
                 tts_engine: Optional[Callable] = None,
                 max_retries: int = 3,
                 timeout_per_chunk: int = 10,
                 buffer_size: int = 3):
        """
        Args:
            tts_engine: TTS引擎函数 (text -> audio_bytes)
            max_retries: 最大重试次数
            timeout_per_chunk: 每段超时时间（秒）
            buffer_size: 并发生成缓冲区大小
        """
        self.tts_engine = tts_engine
        self.max_retries = max_retries
        self.timeout_per_chunk = timeout_per_chunk
        self.buffer_size = buffer_size
        
        # 播放控制
        self.play_lock = threading.Lock()
        self.playback_finished = threading.Event()
        self.current_playing = None
        
        # 音频存储（有序）
        self.audio_chunks: Dict[int, AudioChunk] = {}
        self.next_play_index = 0
        self.total_chunks = 0
        
        # 线程管理
        self.generation_threads = []
        self.is_generating = False
        self.stop_requested = False
    
    def play_chunks(self, 
                    tts_chunks: List[Dict], 
                    on_chunk_start: Optional[Callable] = None,
                    on_chunk_end: Optional[Callable] = None,
                    simulate_mode: bool = True) -> bool:
        """
        播放TTS分段
        
        Args:
            tts_chunks: TTS文本优化器生成的分段列表
            on_chunk_start: 播放开始回调 (chunk_id, text)
            on_chunk_end: 播放结束回调 (chunk_id, success)
            simulate_mode: 是否模拟模式（无真实TTS引擎时）
            
        Returns:
            bool: 是否全部成功播放
        """
        self.total_chunks = len(tts_chunks)
        self.next_play_index = 0
        self.is_generating = True
        self.stop_requested = False
        
        # 初始化所有chunk
        for i, chunk in enumerate(tts_chunks):
            self.audio_chunks[i] = AudioChunk(
                chunk_id=i,
                text=chunk['text'],
                pause_after=chunk['pause_after'],
                status=AudioStatus.PENDING
            )
        
        print(f"🚀 开始生成 {self.total_chunks} 段音频...")
        
        # 启动生成线程（带并发控制）
        semaphore = threading.Semaphore(self.buffer_size)
        
        for i in range(self.total_chunks):
            thread = threading.Thread(
                target=self._generate_with_semaphore,
                args=(i, semaphore, simulate_mode),
                daemon=True
            )
            thread.start()
            self.generation_threads.append(thread)
        
        # 主线程：顺序播放
        success = self._sequential_playback(
            on_chunk_start=on_chunk_start,
            on_chunk_end=on_chunk_end,
            simulate_mode=simulate_mode
        )
        
        self.is_generating = False
        return success
    
    def _generate_with_semaphore(self, chunk_id: int, semaphore: threading.Semaphore, simulate_mode: bool):
        """带信号量的生成（控制并发）"""
        with semaphore:
            if not self.stop_requested:
                self._generate_one_chunk(chunk_id, simulate_mode)
    
    def _generate_one_chunk(self, chunk_id: int, simulate_mode: bool):
        """生成单个音频分片（带重试和时间戳）"""
        from datetime import datetime
        
        chunk = self.audio_chunks[chunk_id]
        chunk.status = AudioStatus.GENERATING
        
        # ⏰ 时间戳：开始生成
        ts_gen_start = time.perf_counter()
        ts_gen_start_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        for attempt in range(self.max_retries):
            if self.stop_requested:
                break
            
            try:
                print(f"🔄 [生成 {chunk_id + 1}/{self.total_chunks}] 尝试 {attempt + 1}/{self.max_retries}")
                print(f"   ⏰ 开始时间: {ts_gen_start_str}")
                print(f"   📝 文本长度: {len(chunk.text)} 字符")
                
                # ⏰ TTS 调用开始
                ts_tts_start = time.perf_counter()
                
                if simulate_mode:
                    # 模拟模式
                    audio_data = self._simulate_tts(chunk.text)
                else:
                    # 真实TTS引擎
                    audio_data = self._call_tts_with_timeout(chunk.text)
                
                # ⏰ TTS 调用结束
                ts_tts_end = time.perf_counter()
                ts_gen_end_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                tts_time = ts_tts_end - ts_tts_start
                total_gen_time = ts_tts_end - ts_gen_start
                
                # 成功
                chunk.audio_data = audio_data
                chunk.duration = len(chunk.text) * 0.15  # 估算时长（秒）
                chunk.status = AudioStatus.READY
                
                print(f"✅ [Chunk {chunk_id}] 生成成功")
                print(f"   ⏰ 完成时间: {ts_gen_end_str}")
                print(f"   📊 生成统计:")
                print(f"      - TTS耗时: {tts_time*1000:.1f}ms")
                print(f"      - 总耗时: {total_gen_time*1000:.1f}ms")
                print(f"      - 音频大小: {len(audio_data):,} bytes")
                print(f"      - 字符/秒: {len(chunk.text)/tts_time:.1f}")
                return
                
            except TimeoutError:
                chunk.retry_count += 1
                chunk.error_message = f"超时（尝试 {attempt + 1}）"
                ts_timeout = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"⏰ [Chunk {chunk_id}] 超时 at {ts_timeout}，重试...")
                time.sleep(0.5)
                
            except Exception as e:
                chunk.retry_count += 1
                chunk.error_message = str(e)
                ts_error = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"❌ [Chunk {chunk_id}] 错误 at {ts_error}: {e}")
                time.sleep(0.5)
        
        # 所有重试失败
        chunk.status = AudioStatus.FAILED
        ts_fail = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        total_fail_time = time.perf_counter() - ts_gen_start
        print(f"💥 [Chunk {chunk_id}] 生成失败 at {ts_fail}")
        print(f"   ⏰ 总耗时: {total_fail_time*1000:.1f}ms")
        print(f"   🔄 重试次数: {self.max_retries}")
    
    def _sequential_playback(self,
                            on_chunk_start: Optional[Callable],
                            on_chunk_end: Optional[Callable],
                            simulate_mode: bool) -> bool:
        """顺序播放（关键方法）"""
        all_success = True
        
        while self.next_play_index < self.total_chunks and not self.stop_requested:
            chunk_id = self.next_play_index
            chunk = self.audio_chunks[chunk_id]
            
            # 等待当前chunk就绪（处理乱序）
            wait_time = 0
            max_wait = self.timeout_per_chunk * 2
            
            while chunk.status not in [AudioStatus.READY, AudioStatus.FAILED]:
                if wait_time >= max_wait or self.stop_requested:
                    print(f"⏰ [Chunk {chunk_id}] 等待超时，跳过")
                    chunk.status = AudioStatus.FAILED
                    break
                
                if wait_time % 2 == 0:
                    print(f"⏳ [等待 {chunk_id + 1}/{self.total_chunks}] {chunk.status.value}... ({wait_time}s)")
                
                time.sleep(1)
                wait_time += 1
            
            # 播放或降级处理
            if chunk.status == AudioStatus.READY:
                if on_chunk_start:
                    on_chunk_start(chunk_id, chunk.text)
                
                success = self._play_one_chunk(chunk, simulate_mode)
                
                if on_chunk_end:
                    on_chunk_end(chunk_id, success)
                
                if not success:
                    all_success = False
            else:
                # 失败降级
                print(f"⚠️  [降级 {chunk_id + 1}] TTS失败，显示文本: {chunk.text}")
                self._fallback_display(chunk)
                all_success = False
                
                if on_chunk_end:
                    on_chunk_end(chunk_id, False)
            
            self.next_play_index += 1
        
        return all_success
    
    def _play_one_chunk(self, chunk: AudioChunk, simulate_mode: bool) -> bool:
        """播放单个音频分片（线程安全）- 带时间戳记录"""
        # 获取播放锁（防止重叠）
        with self.play_lock:
            chunk.status = AudioStatus.PLAYING
            self.current_playing = chunk.chunk_id
            
            # ⏰ 时间戳：开始播放
            ts_start_perf = time.perf_counter()  # 高精度计时器
            ts_start_wall = time.time()          # 系统墙钟时间
            from datetime import datetime
            ts_start_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 毫秒精度
            
            print(f"\n{'─'*70}")
            print(f"🔊 [播放 {chunk.chunk_id + 1}/{self.total_chunks}] {chunk.text[:40]}...")
            print(f"⏰ 开始时间: {ts_start_str}")
            print(f"   - perf_counter: {ts_start_perf:.6f}s")
            print(f"   - wall_clock:   {ts_start_wall:.6f}s")
            
            try:
                # 阻塞式播放
                if simulate_mode:
                    self._simulate_play(chunk)
                else:
                    play_result = self._blocking_play(chunk.audio_data)
                    if play_result:
                        print(f"   音频播放耗时: {play_result['audio_duration']:.3f}s")
                
                # ⏰ 时间戳：音频播放完成，开始停顿
                ts_pause_start_perf = time.perf_counter()
                ts_pause_start_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # 精确停顿
                self._precise_pause(chunk.pause_after)
                
                # ⏰ 时间戳：停顿完成
                ts_end_perf = time.perf_counter()
                ts_end_wall = time.time()
                ts_end_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                chunk.status = AudioStatus.COMPLETED
                
                # 计算各阶段耗时
                total_time = ts_end_perf - ts_start_perf
                pause_time = ts_end_perf - ts_pause_start_perf
                audio_time = ts_pause_start_perf - ts_start_perf
                
                print(f"✅ [完成 {chunk.chunk_id + 1}]")
                print(f"⏰ 结束时间: {ts_end_str}")
                print(f"   - perf_counter: {ts_end_perf:.6f}s")
                print(f"   - wall_clock:   {ts_end_wall:.6f}s")
                print(f"📊 耗时统计:")
                print(f"   - 音频播放: {audio_time:.3f}s")
                print(f"   - 停顿时间: {pause_time:.3f}s ({chunk.pause_after}ms)")
                print(f"   - 总计时长: {total_time:.3f}s")
                print(f"{'─'*70}\n")
                
                return True
                
            except Exception as e:
                ts_error = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"❌ [播放失败] Chunk {chunk.chunk_id} at {ts_error}: {e}")
                chunk.status = AudioStatus.FAILED
                return False
            
            finally:
                self.current_playing = None
    
    def _blocking_play(self, audio_data: bytes):
        """
        阻塞式音频播放 - 使用 pygame 实现真实播放（带详细时间戳）
        
        Returns:
            dict: {'audio_duration': float, 'load_time': float, 'play_time': float}
        """
        from datetime import datetime
        
        try:
            import pygame
            
            # ⏰ 时间戳：开始加载音频
            ts_load_start = time.perf_counter()
            ts_load_start_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # 初始化 pygame mixer（如果尚未初始化）
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                print(f"   🎵 pygame mixer 初始化完成")
            
            # 从字节数据加载音频
            audio_io = io.BytesIO(audio_data)
            pygame.mixer.music.load(audio_io)
            
            # ⏰ 时间戳：加载完成，开始播放
            ts_play_start = time.perf_counter()
            ts_play_start_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            load_time = ts_play_start - ts_load_start
            
            print(f"   ⏰ 音频加载: {ts_load_start_str} -> {ts_play_start_str} ({load_time*1000:.1f}ms)")
            print(f"   📦 音频大小: {len(audio_data):,} bytes")
            
            # 播放音频
            pygame.mixer.music.play()
            print(f"   ▶️  开始播放: {ts_play_start_str}")
            
            # 阻塞等待播放完成
            play_loop_count = 0
            while pygame.mixer.music.get_busy():
                if self.stop_requested:
                    pygame.mixer.music.stop()
                    print(f"   ⏸️  用户中断播放")
                    break
                time.sleep(0.01)
                play_loop_count += 1
            
            # ⏰ 时间戳：播放结束
            ts_play_end = time.perf_counter()
            ts_play_end_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            play_time = ts_play_end - ts_play_start
            total_time = ts_play_end - ts_load_start
            
            print(f"   ⏹️  播放结束: {ts_play_end_str}")
            print(f"   📊 播放统计:")
            print(f"      - 加载耗时: {load_time*1000:.1f}ms")
            print(f"      - 播放耗时: {play_time*1000:.1f}ms")
            print(f"      - 总计耗时: {total_time*1000:.1f}ms")
            print(f"      - 轮询次数: {play_loop_count}")
            
            return {
                'audio_duration': play_time,
                'load_time': load_time,
                'play_time': play_time,
                'total_time': total_time,
                'audio_size': len(audio_data)
            }
            
        except ImportError:
            print("⚠️  pygame 未安装，使用文本模拟模式")
            print(f"   提示：运行 pip install pygame 来启用音频播放")
            # 降级：模拟播放时间
            estimated_duration = len(audio_data) / 16000  # 粗略估算
            self._precise_pause(int(estimated_duration * 1000))
            return {
                'audio_duration': estimated_duration,
                'load_time': 0,
                'play_time': estimated_duration,
                'total_time': estimated_duration,
                'audio_size': len(audio_data)
            }
            
        except Exception as e:
            ts_error = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"⚠️  音频播放出错 at {ts_error}: {e}")
            # 降级：模拟播放时间
            estimated_duration = len(audio_data) / 16000
            self._precise_pause(int(estimated_duration * 1000))
            return {
                'audio_duration': estimated_duration,
                'load_time': 0,
                'play_time': estimated_duration,
                'total_time': estimated_duration,
                'audio_size': len(audio_data),
                'error': str(e)
            }
    
    def _simulate_play(self, chunk: AudioChunk):
        """模拟播放（用于测试）"""
        # 模拟播放时间
        play_time = chunk.duration
        self._precise_pause(int(play_time * 1000))
    
    def _precise_pause(self, milliseconds: int):
        """精确停顿（不依赖sleep精度）"""
        self.playback_finished.clear()
        target_time = time.perf_counter() + milliseconds / 1000
        
        while time.perf_counter() < target_time:
            if self.playback_finished.is_set() or self.stop_requested:
                break
            
            remaining = target_time - time.perf_counter()
            sleep_time = min(0.01, remaining)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _call_tts_with_timeout(self, text: str) -> bytes:
        """调用TTS引擎（带超时控制，支持异步TTS）"""
        if not self.tts_engine:
            raise Exception("TTS引擎未配置")
        
        # 检查 TTS 引擎是否是 BaseTTS 实例（异步）
        try:
            from tts_interface import BaseTTS
            if isinstance(self.tts_engine, BaseTTS):
                # 异步 TTS 调用
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # 如果没有运行中的事件循环，创建新的
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # 使用 asyncio.wait_for 实现超时
                try:
                    audio_data = loop.run_until_complete(
                        asyncio.wait_for(
                            self.tts_engine.synthesize(text),
                            timeout=self.timeout_per_chunk
                        )
                    )
                    return audio_data
                except asyncio.TimeoutError:
                    raise TimeoutError(f"TTS生成超时 ({self.timeout_per_chunk}秒)")
        except ImportError:
            pass
        
        # 同步 TTS 调用（兼容回调函数）
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.tts_engine, text)
            try:
                return future.result(timeout=self.timeout_per_chunk)
            except FutureTimeoutError:
                raise TimeoutError(f"TTS生成超时 ({self.timeout_per_chunk}秒)")
    
    def _simulate_tts(self, text: str) -> bytes:
        """模拟TTS生成"""
        import random
        # 模拟网络延迟
        delay = random.uniform(0.5, 2.0)
        time.sleep(delay)
        
        # 10%概率失败（测试重试机制）
        if random.random() < 0.1:
            raise Exception("模拟网络错误")
        
        return f"audio_for_{text[:10]}".encode()
    
    def _fallback_display(self, chunk: AudioChunk):
        """降级策略：显示文本"""
        print(f"\n{'─'*60}")
        print(f"💬 [文本显示] {chunk.text}")
        print(f"{'─'*60}\n")
        
        # 模拟阅读时间
        reading_time = len(chunk.text) * 0.3
        self._precise_pause(int(reading_time * 1000))
    
    def stop(self):
        """停止播放"""
        self.stop_requested = True
        self.is_generating = False
        self.playback_finished.set()
        print("🛑 播放已停止")


# ============================================================
# 完整TTS优化器（组合）
# ============================================================

class TTSOptimizer:
    """
    完整TTS优化器
    组合文本优化 + 音频管理
    """
    
    def __init__(self,
                 tts_engine: Optional[Callable] = None,
                 max_chunk_length: int = 100,
                 max_retries: int = 3,
                 timeout_per_chunk: int = 10,
                 buffer_size: int = 3):
        """
        Args:
            tts_engine: TTS引擎函数
            max_chunk_length: 单个分段最大字符数
            max_retries: 最大重试次数
            timeout_per_chunk: 每段超时时间
            buffer_size: 并发缓冲区大小
        """
        self.text_optimizer = TTSTextOptimizer(max_chunk_length)
        self.audio_manager = TTSAudioManager(
            tts_engine=tts_engine,
            max_retries=max_retries,
            timeout_per_chunk=timeout_per_chunk,
            buffer_size=buffer_size
        )
    
    def optimize_and_play(self,
                         text: str,
                         on_chunk_start: Optional[Callable] = None,
                         on_chunk_end: Optional[Callable] = None,
                         simulate_mode: bool = True) -> Dict:
        """
        优化文本并播放
        
        Args:
            text: 原始AI输出
            on_chunk_start: 播放开始回调
            on_chunk_end: 播放结束回调
            simulate_mode: 是否模拟模式
            
        Returns:
            {
                'success': bool,
                'tts_chunks': List[Dict],
                'total_chunks': int
            }
        """
        # 1. 文本优化
        print("📝 优化文本...")
        tts_chunks = self.text_optimizer.optimize(text)
        
        if not tts_chunks:
            print("⚠️  没有可播放内容")
            return {
                'success': False,
                'tts_chunks': [],
                'total_chunks': 0
            }
        
        print(f"✅ 生成 {len(tts_chunks)} 个TTS分段")
        
        # 2. 播放音频
        success = self.audio_manager.play_chunks(
            tts_chunks,
            on_chunk_start=on_chunk_start,
            on_chunk_end=on_chunk_end,
            simulate_mode=simulate_mode
        )
        
        return {
            'success': success,
            'tts_chunks': tts_chunks,
            'total_chunks': len(tts_chunks)
        }
    
    def optimize_text_only(self, text: str) -> List[Dict]:
        """仅优化文本，不播放"""
        return self.text_optimizer.optimize(text)

