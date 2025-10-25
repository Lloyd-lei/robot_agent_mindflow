# ConversationSession API 文档

## 📦 概述

`ConversationSession` 是一个高层封装的对话会话管理器，用于统一管理 LLM + TTS 的完整生命周期。

**位置**：`conversation_session.py`

**核心功能**：
- 🔐 自动资源管理（启动/清理）
- ⏱️ 超时保护（防止卡死）
- 💾 对话历史持久化（支持会话恢复）
- 🛡️ 统一异常处理
- 📊 详细日志追踪

---

## 🎯 快速开始

### 最简单的用法

```python
from conversation_session import ConversationSession

# 创建并使用会话（自动清理资源）
with ConversationSession() as session:
    result = session.chat("你好")
    print(result.response)
```

### 完整配置

```python
with ConversationSession(
    llm_model="qwen2.5:3b",      # Ollama 模型
    tts_provider="edge",         # Edge TTS
    tts_voice="zh-CN-XiaoxiaoNeural",  # 晓晓语音
    enable_cache=True,           # 启用 KV Cache
    show_reasoning=True,         # 显示推理过程
    timeout=120,                 # LLM 推理超时 2 分钟
    tts_wait_timeout=180         # TTS 播放超时 3 分钟
) as session:
    result = session.chat("详细介绍一下 Google")
    print(f"回复: {result.response}")
    print(f"耗时: {result.duration:.2f}秒")
    print(f"工具调用: {result.tool_calls}次")
```

---

## 📖 API 参考

### 构造函数

```python
ConversationSession(
    llm_provider: str = None,
    llm_model: str = None,
    tts_provider: str = "edge",
    tts_voice: str = None,
    enable_cache: bool = True,
    show_reasoning: bool = True,
    timeout: int = 60,
    tts_wait_timeout: int = 30
)
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_provider` | `str` | `None` | LLM 提供商（自动从 config 读取） |
| `llm_model` | `str` | `None` | 模型名称（如 `"qwen2.5:3b"`, `"gpt-4o-mini"`） |
| `tts_provider` | `str` | `"edge"` | TTS 提供商（`"edge"` / `"azure"` / `"openai"`） |
| `tts_voice` | `str` | `None` | 语音名称（默认：`"zh-CN-XiaoxiaoNeural"`） |
| `enable_cache` | `bool` | `True` | 启用 KV Cache（提升 3-5 倍速度） |
| `show_reasoning` | `bool` | `True` | 显示推理过程（工具调用日志） |
| `timeout` | `int` | `60` | LLM 推理超时（秒） |
| `tts_wait_timeout` | `int` | `30` | TTS 播放超时（秒） |

#### 超时参数建议

| 场景 | `timeout` | `tts_wait_timeout` |
|------|-----------|-------------------|
| Ollama qwen2.5:3b | 60-120s | 120-180s |
| Ollama qwen2.5:7b | 120-180s | 180-300s |
| OpenAI GPT-4 | 30-60s | 60-120s |
| 长对话/讲故事 | 180-300s | 300-600s |

---

### 核心方法

#### `start()` - 启动会话

```python
session.start() -> None
```

初始化 LLM 和 TTS 资源。

**注意**：使用上下文管理器时会自动调用。

#### `chat(user_input)` - 单轮对话

```python
session.chat(user_input: str) -> SessionResult
```

执行单轮对话，带超时保护和自动保存历史。

**参数**：
- `user_input` (`str`): 用户输入文本

**返回**：`SessionResult`
```python
@dataclass
class SessionResult:
    response: str           # LLM 回复
    tool_calls: int         # 工具调用次数
    duration: float         # 耗时（秒）
    should_end: bool        # 是否需要结束会话
    streaming_stats: Dict   # TTS 统计信息
```

**抛出异常**：
- `SessionNotStartedError`: 会话未启动
- `SessionTimeoutError`: 对话超时

**示例**：
```python
with ConversationSession() as session:
    result = session.chat("现在几点？")
    print(result.response)       # "现在是下午3点15分"
    print(result.duration)       # 2.5
    print(result.tool_calls)     # 1 (调用了时间工具)
    print(result.should_end)     # False
```

#### `end()` - 结束会话

```python
session.end() -> None
```

清理资源（停止 TTS 管道）。

**注意**：使用上下文管理器时会自动调用。

---

### 对话历史管理

#### `save_history()` - 保存对话历史

```python
session.save_history(filepath: Optional[Path] = None) -> None
```

手动保存对话历史到 JSON 文件。

**参数**：
- `filepath` (`Path`, 可选): 保存路径（默认：`sessions/session_TIMESTAMP.json`）

**示例**：
```python
session.save_history()  # 保存到默认位置
session.save_history(Path("backup/my_chat.json"))  # 自定义路径
```

#### `load_history()` - 加载对话历史

```python
session.load_history(filepath: Optional[Path] = None) -> bool
```

从文件恢复对话历史（支持会话恢复）。

**参数**：
- `filepath` (`Path`, 可选): 文件路径（默认：自动查找最新的会话文件）

**返回**：
- `True`: 加载成功
- `False`: 文件不存在或加载失败

**示例**：
```python
with ConversationSession() as session:
    if session.load_history():
        print("✅ 历史已恢复")
    
    result = session.chat("我之前问过什么？")
```

#### `get_history_summary()` - 获取历史摘要

```python
session.get_history_summary() -> Dict[str, Any]
```

获取对话统计信息。

**返回**：
```python
{
    "session_id": "session_1234567890",
    "total_messages": 10,
    "turns": 5,
    "cache_enabled": True,
    "has_history_file": True
}
```

**示例**：
```python
summary = session.get_history_summary()
print(f"对话轮次: {summary['turns']}")
print(f"消息总数: {summary['total_messages']}")
```

#### `reset()` - 重置对话历史

```python
session.reset() -> None
```

清除对话历史（但保持资源）。

**示例**：
```python
session.reset()
# 之后的对话不会记得之前的内容
```

---

### 属性（只读）

```python
session.is_started: bool          # 会话是否已启动
session.session_id: str           # 会话唯一 ID
```

---

## 🔄 完整使用流程

### 手动管理模式

```python
from conversation_session import ConversationSession

# 1. 创建会话
session = ConversationSession(
    llm_model="qwen2.5:3b",
    timeout=120,
    tts_wait_timeout=180
)

# 2. 启动
session.start()

# 3. 多轮对话
result1 = session.chat("我叫小明")
result2 = session.chat("我叫什么名字？")  # ✅ 记得

# 4. 查看历史
summary = session.get_history_summary()
print(f"对话了 {summary['turns']} 轮")

# 5. 结束
session.end()
```

### 上下文管理器模式（推荐）

```python
with ConversationSession(llm_model="qwen2.5:3b") as session:
    # 自动调用 start()
    
    result = session.chat("你好")
    print(result.response)
    
    # 自动调用 end()
```

---

## 🎨 使用场景

### 场景 1：基础对话

```python
with ConversationSession() as session:
    result = session.chat("你好")
    print(result.response)
```

### 场景 2：多轮对话（带记忆）

```python
with ConversationSession(enable_cache=True) as session:
    session.chat("我喜欢 Python")
    session.chat("我讨厌 Java")
    
    result = session.chat("我喜欢什么语言？")
    print(result.response)  # "你喜欢 Python" ✅
```

### 场景 3：异常处理

```python
from conversation_session import SessionTimeoutError

with ConversationSession(timeout=30) as session:
    try:
        result = session.chat("给我写一个很长的故事")
    except SessionTimeoutError:
        print("超时了，但对话历史已保存")
        # 可以继续对话
        result = session.chat("简短点")
```

### 场景 4：会话恢复

```python
# 第一次运行
with ConversationSession() as session:
    session.chat("我喜欢 Rust")
    # 自动保存到 sessions/session_XXX.json

# 程序重启后
with ConversationSession() as session:
    if session.load_history():
        print("✅ 历史已恢复")
    
    result = session.chat("我喜欢什么语言？")
    print(result.response)  # "你喜欢 Rust" ✅
```

### 场景 5：长对话优化

```python
# 长回复场景（如讲故事）
with ConversationSession(
    timeout=180,           # 3 分钟 LLM 超时
    tts_wait_timeout=300   # 5 分钟 TTS 超时
) as session:
    result = session.chat("给我讲一个长篇故事")
    # ✅ 不会超时
```

### 场景 6：生产环境

```python
# 关闭调试信息
with ConversationSession(
    show_reasoning=False,  # 不显示推理过程
    enable_cache=True      # 启用缓存
) as session:
    result = session.chat("用户问题")
    return result.response
```

---

## 🚨 异常处理

### 异常类型

```python
from conversation_session import (
    SessionNotStartedError,   # 会话未启动
    SessionTimeoutError        # 对话超时
)
```

### 完整异常处理

```python
with ConversationSession() as session:
    try:
        result = session.chat("用户输入")
        
    except SessionNotStartedError as e:
        print(f"会话未启动: {e}")
        
    except SessionTimeoutError as e:
        print(f"超时: {e}")
        # 对话历史已自动保存
        
    except Exception as e:
        print(f"未知错误: {e}")
```

---

## 📊 返回值详解

### `SessionResult` 结构

```python
@dataclass
class SessionResult:
    response: str           # LLM 的回复文本
    tool_calls: int         # 调用了几次工具
    duration: float         # 本次对话耗时（秒）
    should_end: bool        # 是否检测到对话结束
    streaming_stats: Dict   # TTS 统计信息（可选）
```

### `streaming_stats` 详解

```python
{
    "text_received": 10,      # 接收了多少段文本
    "audio_generated": 10,    # 生成了多少段音频
    "audio_played": 10,       # 播放了多少段音频
    "audio_failed": 0,        # 失败了多少段
    "text_dropped": 0,        # 背压丢弃了多少段
    "text_queue_size": 0,     # 当前文本队列大小
    "audio_queue_size": 0,    # 当前音频队列大小
    "active_tasks": 0,        # 活跃任务数
    "is_playing": False       # 是否正在播放
}
```

---

## 🔧 配置建议

### Ollama qwen2.5:3b（推荐）

```python
ConversationSession(
    llm_model="qwen2.5:3b",
    timeout=120,           # 2 分钟
    tts_wait_timeout=180   # 3 分钟
)
```

### Ollama qwen2.5:7b（质量更好）

```python
ConversationSession(
    llm_model="qwen2.5:7b",
    timeout=180,           # 3 分钟
    tts_wait_timeout=300   # 5 分钟
)
```

### OpenAI GPT-4（速度快）

```python
ConversationSession(
    llm_model="gpt-4o-mini",
    timeout=60,            # 1 分钟
    tts_wait_timeout=120   # 2 分钟
)
```

---

## 💡 最佳实践

### 1. 始终使用上下文管理器

```python
# ✅ 推荐
with ConversationSession() as session:
    result = session.chat("你好")

# ❌ 不推荐（需要手动清理）
session = ConversationSession()
session.start()
result = session.chat("你好")
session.end()
```

### 2. 启用缓存以支持历史恢复

```python
# ✅ 启用缓存（必须）
ConversationSession(enable_cache=True)

# ❌ 禁用缓存（无法保存历史）
ConversationSession(enable_cache=False)
```

### 3. 根据场景调整超时

```python
# 短对话
ConversationSession(timeout=60, tts_wait_timeout=120)

# 长对话
ConversationSession(timeout=180, tts_wait_timeout=300)
```

### 4. 处理超时异常

```python
try:
    result = session.chat(user_input)
except SessionTimeoutError:
    # 超时时历史已保存，可以继续对话
    print("请求超时，请简化问题")
```

### 5. 定期清理历史文件

```python
# sessions/ 目录会持续累积文件
# 建议定期手动清理旧文件
```

---

## 🐛 已知问题

### 1. 长回复 TTS 超时
**问题**：`tts_wait_timeout=30` 太短，长回复会被强制跳过  
**解决**：增加 `tts_wait_timeout` 到 120-300 秒

### 2. `(END_CONVERSATION)` 被播放
**问题**：结束对话时会听到 "END CONVERSATION"  
**状态**：待修复

### 3. 无法禁用 TTS
**问题**：即使不需要语音也会初始化 TTS  
**状态**：待优化

---

## 📚 相关文档

- [会话持久化指南](SESSION_PERSISTENCE_GUIDE.md)
- [Ollama 使用指南](Ollama使用指南.md)
- [项目 README](../README.md)

---

## 🆕 更新日志

### v1.0.0 (2024-10-24)
- ✅ 初始版本
- ✅ 支持 LLM + TTS 完整生命周期管理
- ✅ 超时保护机制
- ✅ 对话历史持久化
- ✅ 会话恢复功能
- ✅ 详细日志追踪

---

**最后更新**：2024-10-24  
**作者**：Agent MVP Team

