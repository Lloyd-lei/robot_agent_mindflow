# 🚀 Robot Agent Mindflow

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 混合架构AI Agent - OpenAI原生 + LangChain工具池 + KV Cache优化 + 真实语音播放

---

## ✨ 特性

- 🎯 **混合架构** - OpenAI原生API + LangChain工具池
- ⚡ **KV Cache优化** - 多轮对话速度提升3-5倍，成本节省50%
- 🗣️ **真实语音** - Edge TTS免费高质量中文语音
- 🛠️ **17个工具** - 数学、时间、文本、前台接待等
- 🏗️ **新架构** - 分层设计，模块化，易维护
- 📖 **完整文档** - 架构设计 + 迁移指南

---

## 🚀 30秒快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API Key
cp .env.example .env
# 编辑 .env，设置 OPENAI_API_KEY=your-key

# 3. 启动语音Agent
python main.py
```

就这么简单！🎉

详见 [快速启动指南](QUICKSTART.md)

---

## 📖 文档

- 🚀 **[快速启动](QUICKSTART.md)** - 30秒上手
- 🏗️ **[架构设计](docs/architecture.md)** - 完整架构说明
- 🔄 **[迁移指南](docs/migration_guide.md)** - 从旧代码迁移
- 📝 **[重构总结](ARCHITECTURE_REFACTORING.md)** - 架构重构详情

---

## 🎯 核心优势

### 1. 混合架构

```
OpenAI原生API (推理引擎)
    ↓
    100%可靠的工具调用 + tool_choice控制
    ↓
LangChain工具池 (执行引擎)
    ↓
    17个强大工具 + 易于扩展
```

### 2. KV Cache优化

- **系统提示词缓存** - 节省50%成本
- **对话历史缓存** - 速度提升3-5倍
- **自动优化** - 无需手动管理

### 3. 真实语音

- **Edge TTS** - 免费、高质量
- **智能分句** - 自然流畅
- **防重叠播放** - 稳定可靠

### 4. 新架构

```
src/
├── core/         # 核心层 - Agent、Tools、Config
├── services/     # 服务层 - TTS、Voice
└── tools/        # 工具层 - Basic、Reception、System
```

- ✅ 分层清晰
- ✅ 易于维护
- ✅ 易于扩展
- ✅ 100%向后兼容

---

## 💡 使用示例

### 基础对话

```bash
$ python main.py

💬 您: 现在几点了?

🧠 混合架构推理过程...
📡 调用OpenAI API进行推理...
✅ 模型决定调用工具: time_tool
📤 工具返回结果: 14:30:25
💬 最终回答: 现在是下午2点30分25秒。

🎵 TTS音频播放
🔊 [播放] 现在是下午2点30分25秒。
✅ 完成

⚡ 响应耗时: 3.21秒
📞 工具调用: 1次
🔊 语音播放: ✅ 完成
```

### 编程API

```python
from src.core import HybridReasoningAgent
from src.tools import load_all_tools

# 加载工具
tools = load_all_tools()

# 创建Agent
agent = HybridReasoningAgent(tools=tools)

# 执行推理
result = agent.run("计算sqrt(2)保留3位小数")

print(result.output)       # 最终回答
print(result.tool_calls)   # 工具调用次数
```

---

## 🛠️ 可用工具

### 基础工具 (8个)
- ✅ Calculator - 数学计算
- ✅ TimeTool - 时间查询
- ✅ TextAnalyzer - 文本分析
- ✅ UnitConverter - 单位转换
- ✅ DataComparison - 数据比较
- ✅ LogicReasoning - 逻辑推理
- ✅ LibraryManagement - 图书馆管理
- ✅ ConversationEnd - 对话结束检测

### 前台接待工具 (6个)
- ✅ VisitorRegistration - 访客登记
- ✅ MeetingRoom - 会议室管理
- ✅ EmployeeDirectory - 员工通讯录
- ✅ DirectionGuide - 路线指引
- ✅ PackageManagement - 包裹管理
- ✅ FAQ - 常见问题

### 系统工具 (3个)
- ✅ WebSearch - 网络搜索
- ✅ FileOperation - 文件操作
- ✅ Reminder - 提醒设置

---

## 🎨 架构亮点

### 旧架构 vs 新架构

| 方面 | 旧架构 | 新架构 |
|------|--------|--------|
| 结构 | ❌ 扁平化，混乱 | ✅ 三层分层 |
| 职责 | ❌ 不清晰 | ✅ 单一职责 |
| 配置 | ❌ 简单变量 | ✅ Pydantic验证 |
| 维护 | ❌ 困难 | ✅ 易维护 |
| 扩展 | ❌ 修改困难 | ✅ 易扩展 |
| 文档 | ❌ 零散 | ✅ 完整详细 |

### 设计原则

1. **分层架构** - Core / Services / Tools
2. **依赖倒置** - 面向接口编程
3. **单一职责** - 每个模块只做一件事
4. **开闭原则** - 对扩展开放，对修改关闭

---

## 📊 性能

- ⚡ **首次调用**: ~3秒
- ⚡ **后续调用**: ~1秒 (KV Cache优化)
- 💰 **成本节省**: ~50% (系统提示词缓存)
- 🎵 **TTS延迟**: <1秒 (Edge TTS)

---

## 🔧 配置

编辑 `.env` 文件:

```bash
# OpenAI配置
OPENAI_API_KEY=your-key-here
LLM_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.0

# TTS配置
ENABLE_TTS=true
TTS_VOICE=zh-CN-XiaoxiaoNeural
TTS_RATE=+0%
TTS_VOLUME=+0%

# Agent配置
ENABLE_CACHE=true
MAX_RETRIES=3
```

---

## 🧪 测试

```bash
# 快速测试
python main.py --test

# 架构测试
python scripts/test_new_architecture.py

# 运行示例
python examples/demo_new_architecture.py
```

---

## 📝 更新日志

### v0.2.0 (2024-10-26) - 架构重构

- ✅ 新目录结构 - 分层架构
- ✅ 核心模块重构 - BaseAgent, BaseTool, Settings
- ✅ 完整文档 - 架构设计 + 迁移指南
- ✅ 主入口文件 - `main.py`
- ✅ 100%向后兼容

### v0.1.0 - MVP版本

- ✅ 混合架构 - OpenAI + LangChain
- ✅ KV Cache优化
- ✅ TTS集成

---

## 🤝 贡献

欢迎贡献！请遵循:

1. Fork本仓库
2. 创建特性分支
3. 提交更改
4. 开启Pull Request

详见 [贡献指南](docs/architecture.md#贡献指南)

---

## 📧 联系

- GitHub: [@Lloyd-lei](https://github.com/Lloyd-lei)
- Issues: [提交问题](https://github.com/Lloyd-lei/robot_agent_mindflow/issues)

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- OpenAI - GPT API
- LangChain - 工具生态
- Edge TTS - 免费TTS服务

---

**享受与AI的对话吧！🎉**

[快速开始](QUICKSTART.md) | [完整文档](docs/architecture.md) | [示例代码](examples/)
