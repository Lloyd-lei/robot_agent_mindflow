# 更新日志

## [v1.2.0] - 2025-10-25

### 🔧 重大修复

#### 1. **OpenAI TTS 集成问题**
- 修复 TTS 初始化顺序错误导致 StreamingTTSPipeline 使用错误引擎的问题
- 根因：先创建 Agent 再设置 TTS，导致 Pipeline 已保存 Edge TTS 引用
- 解决方案：先创建 TTS 引擎，再传入 Agent 构造函数
- 验证：添加 `test/test_final_tts_verification.py` 确保引用一致性
- 详细说明：`docs/OpenAI_TTS_集成修复.md`

### ✨ 新功能

#### 1. **外部化 System Prompt**
- 创建 `prompts/system_prompt.txt` - 提示词独立管理
- 创建 `prompts/README.md` - 提示词修改指南
- `agent_hybrid.py` 自动从文件加载提示词
- 方便用户自定义 Agent 行为和风格

#### 2. **OpenAI LLM + TTS 完整支持**
- LLM：OpenAI gpt-4o-mini（便宜、快速）
- TTS：OpenAI TTS - Nova 语音（高质量、多语言）
- 配置：通过 `.env` 文件统一管理
- 成本：$15/1M 字符（TTS），约 100 字回复 = $0.0015

### 🧪 测试增强

#### 新增测试脚本
- `test/test_config_quick.py` - 快速配置验证
- `test/test_final_tts_verification.py` - TTS 集成验证
- `test/test_openai_tts.py` - OpenAI TTS 功能测试
- `test/test_prompt_loading.py` - 外部提示词加载测试
- `test/test_multilingual_voice.py` - 多语言语音测试

### 📦 项目清理

#### 目录结构优化
- 移动所有测试文件到 `test/` 目录
- 清理 `sessions/` 目录（保留最近 5 个）
- 清理 `logs/` 目录（保留今天的日志）
- 删除根目录重复文件

#### 文档更新
- `docs/OpenAI_TTS_集成修复.md` - 详细修复说明
- `docs/多语言TTS使用指南.md` - 多语言使用文档
- 更新 `README.md` - 外部 Prompt 配置说明

### 🐛 Bug 修复
- 移除 `agent_hybrid.py` 中误导性的 "使用 Edge TTS" 打印
- 改为警告日志：只在 fallback 时提示
- 修复 `tools.py` 中 `VoiceSelector` 的类型注解错误（`any` → `Any`）

### 🎯 配置优化
- `.env` 示例更新：支持 OpenAI/Ollama 切换
- `config.py` 统一管理 LLM 和 TTS 配置
- `main.py` 动态显示实际使用的 TTS 提供商

### 📊 Git 记录
- 提交：34ddf7e
- 分支：wrapper-updated
- 推送：✅ 已同步到远程

---

## [v1.1.0] - 2024-10-24

### ✨ 新功能

#### 1. **ConversationSession 会话管理器**
- 新增 `conversation_session.py` - 统一管理 LLM + TTS 生命周期
- 提供简洁的 API：`start()`, `chat()`, `end()`
- 支持上下文管理器（`with` 语句）
- 详细 API 文档：`docs/ConversationSession_API.md`

#### 2. **对话历史持久化**
- 自动保存对话历史到 `sessions/*.json`
- 支持会话恢复（程序重启后可恢复记忆）
- 新增方法：`save_history()`, `load_history()`, `get_history_summary()`
- 完整使用指南：`docs/SESSION_PERSISTENCE_GUIDE.md`

#### 3. **日志系统**
- 新增 `logger_config.py` - 统一日志管理
- 彩色控制台输出（INFO 级别）
- 自动写入日志文件（`logs/agent_YYYYMMDD.log`，DEBUG 级别）
- 支持模块级别的日志配置

#### 4. **超时保护机制**
- LLM 推理超时保护（防止 Ollama 推理慢卡死）
- TTS 播放超时保护（防止长回复播放卡死）
- 超时时自动保存对话历史（不丢失记忆）
- 可配置超时参数：`timeout`, `tts_wait_timeout`

### 🔧 优化

#### 1. **main.py 重构**
- 使用新的 `ConversationSession` 管理器
- 简化代码逻辑（从 ~220 行 → ~170 行）
- 新增 `history` 命令（查看对话历史摘要）
- 改进超时异常处理（超时后可继续对话）

#### 2. **agent_hybrid.py 改进**
- 集成日志系统（DEBUG 级别调试日志）
- TTS 等待循环添加超时机制
- 添加详细的状态日志（队列大小、播放状态）

#### 3. **TTS 文本清理**
- `SmartSentenceSplitter` 集成文本清理功能
- 自动移除 markdown 格式（代码块、链接等）
- 展开英文缩写（AI → 人工智能）
- 清理多余空白

#### 4. **目录结构优化**
```
agent_mvp/
├── docs/                          # 📚 文档目录（新增和整理）
│   ├── ConversationSession_API.md  # 新增：API 文档
│   ├── SESSION_PERSISTENCE_GUIDE.md # 移入：持久化指南
│   ├── U_should_know.md            # 移入：开发笔记
│   └── ...（其他文档）
├── examples/                      # 📝 示例代码（重命名）
│   ├── demo_reception.py
│   └── demo_tts_showcase.py
├── test/                          # 🧪 测试目录（整理）
│   ├── test_session.py            # 移入：会话测试
│   └── ...（其他测试）
├── sessions/                      # 💾 会话历史（新增）
├── logs/                          # 📋 日志文件（新增）
├── conversation_session.py        # 新增：会话管理器
├── logger_config.py               # 新增：日志配置
└── main.py                        # 优化：主程序
```

### 🐛 Bug 修复

#### 1. **多轮对话卡死问题**
- **问题**：TTS 播放后无法开始下一轮对话
- **原因**：每轮对话后错误地停止了 TTS 管道
- **修复**：注释掉 `streaming_pipeline.stop()`，保持管道运行
- **位置**：`agent_hybrid.py` 第 911 行

#### 2. **Ollama 模型切换**
- **问题**：默认使用 `qwen2.5:7b`，推理较慢
- **修复**：改为 `qwen2.5:3b`（速度快，质量好）
- **影响文件**：`config.py`, `.env`, `docs/Ollama使用指南.md`

### 📖 文档更新

#### 新增文档
- `docs/ConversationSession_API.md` - API 完整参考
- `docs/SESSION_PERSISTENCE_GUIDE.md` - 持久化使用指南
- `CHANGELOG.md` - 本更新日志

#### 更新文档
- `README.md` - 更新项目结构和快速开始
- `docs/Ollama使用指南.md` - 推荐 qwen2.5:3b 模型
- `.env.example` - 更新默认配置

### ⚙️ 配置变更

#### `.env` 默认配置
```bash
USE_OLLAMA=true
OLLAMA_MODEL=qwen2.5:3b  # 从 7b 改为 3b
OLLAMA_BASE_URL=http://localhost:11434/v1
```

#### `main.py` 超时配置
```python
timeout=60,           # 单轮对话超时（用户可自行调整）
tts_wait_timeout=30   # TTS 播放超时（建议调整为 120-180）
```

### 🚨 已知问题

#### 1. **长回复 TTS 超时**
- **现象**：回复超过 50 秒会被强制跳过
- **原因**：`tts_wait_timeout=30` 秒太短
- **建议**：手动修改 `main.py` 第 119 行为 `tts_wait_timeout=180`

#### 2. **`(END_CONVERSATION)` 被播放**
- **现象**：结束对话时听到 "END CONVERSATION"
- **原因**：LLM 输出的特殊标记未过滤
- **状态**：待修复

### 📦 依赖更新

无新增依赖。

### 🔄 API 变更

#### 新增 API
```python
# ConversationSession
session = ConversationSession(...)
session.start()
session.chat(user_input) -> SessionResult
session.save_history()
session.load_history() -> bool
session.get_history_summary() -> Dict
session.reset()
session.end()
```

#### 保持兼容
- `HybridReasoningAgent` API 无变化
- `StreamingTTSPipeline` API 无变化
- 所有工具 API 无变化

### 🎯 下一步计划

#### 短期（v1.2.0）
- [ ] 修复 `(END_CONVERSATION)` 被播放的问题
- [ ] 动态计算 TTS 超时时间（基于文本长度）
- [ ] 添加 TTS 禁用选项
- [ ] 优化日志输出（减少冗余信息）

#### 中期（v1.3.0）
- [ ] 支持多会话管理
- [ ] 添加会话导出/导入功能
- [ ] Web UI 界面
- [ ] 语音输入支持（ASR）

#### 长期（v2.0.0）
- [ ] 多模态支持（图像、视频）
- [ ] 插件系统
- [ ] 分布式部署
- [ ] API 服务器模式

---

## [v1.0.0] - 2024-10-20

### ✨ 初始版本

- 基础 LLM Agent 架构（OpenAI + LangChain）
- Function Calling 工具调用
- KV Cache 优化
- 流式 TTS 播放
- 17 个内置工具

---

**版本说明**：
- **主版本号**：重大架构变更或 API 不兼容
- **次版本号**：新功能添加
- **修订号**：Bug 修复和小改进

