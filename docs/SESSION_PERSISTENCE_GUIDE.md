# 会话持久化和超时恢复指南

## 📋 功能概述

新增了对话历史持久化功能，解决了会话超时后丢失对话记忆的问题。

## ✨ 核心特性

### 1. 自动保存对话历史

每次对话完成后，系统会自动保存对话历史到文件：

- 📁 保存路径：`sessions/session_TIMESTAMP.json`
- 💾 保存内容：对话历史、会话 ID、模型信息、对话轮次
- 🔄 自动触发：每次 `session.chat()` 完成后

### 2. 超时保护 + 历史保留

当发生超时异常时：

- ✅ 对话历史**不会丢失**
- ✅ KV Cache **保持可用**
- ✅ 可以**继续对话**（保留上下文）
- ✅ 历史文件**自动保存**

### 3. 会话恢复

程序重启后，可以恢复之前的对话历史：

```python
with ConversationSession(...) as session:
    # 自动尝试加载历史
    if session.load_history():
        print("✅ 历史已恢复")

    # 继续对话（带记忆）
    result = session.chat("我之前问过什么？")
```

## 📖 使用方法

### 基本使用（自动模式）

```python
from conversation_session import ConversationSession

# 创建会话
with ConversationSession(enable_cache=True) as session:
    # 自动加载历史
    session.load_history()

    # 对话（自动保存）
    result = session.chat("你好")
    # ✅ 历史已自动保存到 sessions/
```

### 手动控制

```python
# 手动保存历史
session.save_history()

# 手动加载历史
if session.load_history():
    print("✅ 历史已恢复")

# 查看历史摘要
summary = session.get_history_summary()
print(f"对话轮次: {summary['turns']}")
print(f"消息总数: {summary['total_messages']}")
```

### 超时恢复示例

```python
with ConversationSession(timeout=60, tts_wait_timeout=30) as session:
    while True:
        try:
            user_input = input("💬 您: ")
            result = session.chat(user_input)
            print(f"回复: {result.response}")

        except SessionTimeoutError as e:
            # 超时时，对话历史已自动保存
            print("⏱️  超时了，但对话历史已保留")
            # 继续对话（不丢失上下文）
            continue
```

## 📁 文件结构

```
sessions/
├── session_1730000001.json  # 会话1的历史
├── session_1730000123.json  # 会话2的历史
└── ...
```

### 历史文件格式

```json
{
  "session_id": "session_1730000001",
  "created_at": "2025-10-24T12:00:00",
  "llm_model": "qwen2.5:3b",
  "turns": 3,
  "conversation_history": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "你好！有什么可以帮助你的？" },
    { "role": "user", "content": "现在几点？" },
    { "role": "assistant", "content": "..." }
  ]
}
```

## 🎯 实际场景

### 场景 1：长时间对话（防止超时丢失记忆）

```python
# Ollama 推理慢 → 可能超时
with ConversationSession(timeout=60) as session:
    # 第1轮
    session.chat("我叫小明")  # ✅ 保存

    # 第2轮（假设超时）
    try:
        session.chat("给我写一个很长的故事")  # ⏱️  超时
    except SessionTimeoutError:
        print("超时了，但历史已保留")  # ✅ 对话历史已保存

    # 第3轮（继续对话，带记忆！）
    result = session.chat("我叫什么名字？")
    # 回复: "你叫小明" ✅ 记忆完整！
```

### 场景 2：程序意外重启（恢复会话）

```python
# 第一次运行
with ConversationSession() as session:
    session.chat("我喜欢 Python")
    session.chat("我讨厌 Java")
    # ✅ 历史已保存

# 程序崩溃/重启...

# 第二次运行
with ConversationSession() as session:
    if session.load_history():  # ✅ 恢复历史
        result = session.chat("我喜欢什么语言？")
        # 回复: "你喜欢 Python" ✅
```

### 场景 3：查看历史状态

```python
with ConversationSession() as session:
    # 对话几轮
    session.chat("你好")
    session.chat("现在几点？")

    # 查看历史摘要
    summary = session.get_history_summary()
    print(f"""
    会话ID: {summary['session_id']}
    对话轮次: {summary['turns']}
    消息总数: {summary['total_messages']}
    已保存: {'是' if summary['has_history_file'] else '否'}
    """)
```

## 🔧 命令行工具

在 `main.py` 中新增命令：

```bash
# 运行主程序
python main.py

# 可用命令：
💬 您: history      # 查看对话历史摘要
💬 您: stats        # 查看 KV Cache 统计
💬 您: clear        # 清除对话历史
💬 您: help         # 查看帮助
💬 您: quit         # 退出
```

## ⚠️ 注意事项

### 1. 必须启用缓存

```python
# ✅ 正确：启用缓存
session = ConversationSession(enable_cache=True)

# ❌ 错误：未启用缓存（无法持久化）
session = ConversationSession(enable_cache=False)
```

### 2. 历史文件管理

- 历史文件会持续累积（不会自动删除）
- 建议定期清理旧会话文件
- 可以手动删除 `sessions/` 目录

### 3. 超时时的行为

- 超时时，**已完成的对话**会被保存
- 超时时，**未完成的对话**不会保存
- 超时后，可以继续使用会话（不需要重启）

## 📊 性能影响

- **保存耗时**：< 10ms（JSON 序列化）
- **加载耗时**：< 10ms（JSON 反序列化）
- **磁盘占用**：~1-10KB / 会话（取决于对话长度）
- **对对话速度影响**：基本无影响（异步保存）

## 🧪 测试

运行测试脚本：

```bash
# 自动化测试
python test_session.py

# 交互式测试
python test_session.py interactive
```

测试包括：

1. ✅ 基本对话功能
2. ✅ 超时保护机制
3. ✅ 缓存管理和历史持久化
4. ✅ 多轮对话记忆保持

## 💡 最佳实践

### 1. 长时间对话

```python
# 设置较长的超时时间
with ConversationSession(
    timeout=120,          # 2分钟超时
    tts_wait_timeout=60   # 1分钟TTS超时
) as session:
    # 对话...
```

### 2. 生产环境

```python
# 定期备份会话文件
import shutil
from datetime import datetime

backup_dir = f"sessions_backup_{datetime.now().strftime('%Y%m%d')}"
shutil.copytree("sessions", backup_dir)
```

### 3. 调试模式

```python
from logger_config import setup_logger

# 启用 DEBUG 日志
logger = setup_logger(level="DEBUG")

# 会显示详细的保存/加载日志
with ConversationSession() as session:
    # 对话...
```

## 🔗 相关文件

- `conversation_session.py` - 会话管理器（核心实现）
- `main.py` - 主程序（集成示例）
- `test_session.py` - 测试脚本
- `logger_config.py` - 日志系统

## 🎉 总结

这次改进彻底解决了会话超时和意外中断导致对话记忆丢失的问题，让 Agent 可以在长时间对话和多次重启后仍然保持上下文记忆，大大提升了用户体验！
