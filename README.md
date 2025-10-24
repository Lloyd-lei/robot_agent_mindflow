# AI Agent + TTS 语音助手

**- OpenAI / Ollama + LangChain + Edge TTS**

<p align="center">
  <img src="https://img.shields.io/badge/Ollama-Qwen2.5-red?style=for-the-badge&logo=ollama" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4-blue?style=for-the-badge&logo=openai" />
  <img src="https://img.shields.io/badge/LangChain-Agent-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/TTS-Edge%20TTS-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Python-3.8%2B-yellow?style=for-the-badge&logo=python" />
</p>

---

## 🎯 项目概述

这是一个**AI 语音交互系统**，结合了：

- 🦙 **Ollama + Qwen2.5** - 本地运行，完全免费，隐私保护（**推荐**）
- ☁️ **OpenAI GPT-4** - 云端 API，强大的推理能力（可选）
- 🛠️ **LangChain 工具池** - 17 个智能工具
- 🗣️ **Edge TTS** - 高质量语音合成
- ⚡ **KV Cache 优化** - 多轮对话加速 3-5 倍

> 💡 **新功能：** 现在支持 Ollama 本地模型！一行配置即可切换 OpenAI 和 Ollama。

**由于ASR推理成本过高，以及整个ASR + VAD + 打断过于负责，因此与llm + tts解藕**

### ✨ 核心特性

| 特性                  | 说明                                       | 状态 |
| --------------------- | ------------------------------------------ | ---- |
| **100% 可靠工具调用** | OpenAI 原生 API，`tool_choice` 强制调用    | ✅   |
| **17 个智能工具**     | 计算器、时间、图书馆、前台接待等           | ✅   |
| **KV Cache 优化**     | 系统提示词缓存，对话历史缓存               | ✅   |
| **TTS 语音合成**      | Edge TTS 免费高质量，支持切换 Azure/OpenAI | ✅   |
| **真实音频播放**      | pygame 实时播放，防重叠机制                | ✅   |
| **推理过程可视化**    | 完整展示工具选择和参数决策                 | ✅   |
| **范型 TTS 接口**     | 轻松切换不同 TTS 服务                      | ✅   |

## 📁 项目结构

```
robot_agent_mindflow/
├── 📄 核心文件
│   ├── agent_hybrid.py          # 混合架构 Agent（OpenAI + LangChain）
│   ├── tools.py                 # 17 个 LangChain 工具
│   ├── tts_interface.py         # TTS 范型接口（Edge/Azure/OpenAI）
│   ├── tts_optimizer.py         # TTS 文本优化 + 音频播放管理
│   ├── voice_feedback.py        # 语音反馈（思考提示）
│   └── config.py                # 配置管理
│
├── 🎬 演示程序
│   ├── main.py           # 主交互演示（推荐）✨
│   └── test_tts_integration.py  # TTS 功能测试
│
├── 📚 文档
│   ├── README.md                # 本文件
│   ├── 快速开始.md              # 5 分钟上手指南
│   ├── TTS配置说明.md           # TTS 详细配置
│   ├── TTS集成总结.md           # TTS 集成报告
│   ├── 项目结构说明.md          # 架构文档
│   ├── 混合架构优化报告.md      # 性能优化报告
│   └── 前台接待Agent说明.md     # 业务场景示例
│
├── 🗑️ 归档文件
│   └── waste/                   # 旧版本文件（已归档）
│
└── ⚙️ 配置文件
    ├── requirements.txt         # Python 依赖
    ├── .env.example             # 环境变量模板
    ├── .gitignore              # Git 忽略规则
    └── .env                    # 环境变量（需自行创建）
```

## 🏗️ 架构设计

### 混合架构流程图

```
┌────────────────────────────────────────────────────────┐
│                    用户语音/文本输入                      │
└────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────┐
│               混合架构 Agent (agent_hybrid.py)           │
│                                                          │
│  ┌────────────────┐          ┌──────────────────┐     │
│  │  OpenAI API    │          │  LangChain Tools │     │
│  │  • Function    │  ◄────►  │  • 17 个工具     │     │
│  │    Calling     │          │  • 即插即用      │     │
│  │  • GPT-4推理   │          │  • 独立执行      │     │
│  └────────────────┘          └──────────────────┘     │
│          ↓                           ↓                  │
│  ┌────────────────────────────────────────────┐       │
│  │        KV Cache 优化 (自动缓存)            │       │
│  │  • 系统提示词缓存 (50% off)                 │       │
│  │  • 对话历史缓存 (多轮加速)                  │       │
│  └────────────────────────────────────────────┘       │
└────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────┐
│                TTS 优化器 (tts_optimizer.py)             │
│  • 文本清理 + 智能分句                                   │
│  • 异步音频生成 + 防重叠播放                             │
│  • 失败重试 + 降级策略                                   │
└────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────┐
│              TTS 引擎 (tts_interface.py)                 │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐            │
│  │Edge TTS │  │Azure TTS │  │OpenAI TTS │            │
│  │(默认)   │  │(付费)    │  │(付费)     │            │
│  └─────────┘  └──────────┘  └───────────┘            │
└────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────┐
│               音频播放 (pygame)                          │
│  • 阻塞式播放 • 精确停顿 • 支持中断                      │
└────────────────────────────────────────────────────────┘
```

### 核心优势

1. **OpenAI 原生 API** → 100% 可靠的工具调用
2. **LangChain 工具池** → 丰富的工具生态
3. **KV Cache 优化** → 自动缓存，成本减半
4. **范型 TTS 接口** → 一行代码切换服务

## 🚀 快速开始

### 方案一：使用 Ollama 本地模型（推荐，免费）

```bash
# 1. 克隆项目
git clone https://github.com/Lloyd-lei/robot_agent_mindflow.git
cd robot_agent_mindflow

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装并启动 Ollama
brew install ollama          # macOS
ollama serve                 # 启动服务（保持运行）

# 4. 下载模型（另开一个终端）
ollama pull qwen2.5:3b       # 下载 Qwen2.5 3B 模型（2GB，推荐）

# 5. 测试 Ollama 配置
python test_ollama.py        # 验证配置是否正确

# 6. 启动 AI Agent（流式 TTS 模式）
python demo_hybrid.py streaming
```

### 方案二：使用 OpenAI API（需要付费）

```bash
# 1-2. 克隆项目并安装依赖（同上）

# 3. 配置 OpenAI API
cp .env.example .env
# 编辑 .env 文件：
# USE_OLLAMA=false
# OPENAI_API_KEY=sk-your-key-here

# 4. 启动 AI Agent
python demo_hybrid.py streaming
```

> 📖 详细说明：参见 [Ollama 使用指南.md](./Ollama使用指南.md)

### 环境变量配置

编辑 `.env` 文件：

```env
# OpenAI API 配置
OPENAI_API_KEY=sk-proj-你的密钥

# 模型配置
LLM_MODEL=gpt-4-turbo-preview
TEMPERATURE=0
```

💡 **获取 OpenAI API 密钥**: https://platform.openai.com/api-keys

### 试试这些命令

启动 `demo_hybrid.py` 后，试试：

```
现在几点了？
计算 sqrt(2) 保留 3 位小数
图书馆有关于 Python 的书吗？
帮我登记访客信息
再见（自动结束对话）
```

📖 **详细教程**: 查看 `快速开始.md`

## 💡 核心功能演示

### 测试：计算 sqrt(2) 保留 3 位小数

```python
from agent import ReasoningAgent

# 创建Agent
agent = ReasoningAgent(verbose=True)

# 运行测试
result = agent.run("计算sqrt(2)保留3位小数")

# 输出
# LLM推理过程：
# 1. 理解问题：需要计算2的平方根并保留3位小数
# 2. 决策：这是数学计算，需要使用calculator工具
# 3. 工具调用：calculator("round(sqrt(2), 3)")
# 4. 获取结果：1.414
# 5. 生成答案：sqrt(2)保留3位小数等于1.414
```

## 🛠️ 工具系统

### CalculatorTool（计算器工具）

**功能**：支持各种数学运算和函数

**支持的操作**：

- 基础运算：`+`, `-`, `*`, `/`, `**`
- 数学函数：`sqrt`, `sin`, `cos`, `tan`, `log`, `exp`, `abs`, `round`
- 数学常量：`pi`, `e`

**示例**：

```python
# 直接使用工具
from tools import CalculatorTool

calc = CalculatorTool()
result = calc._run("round(sqrt(2), 3)")
print(result)  # 输出: 1.414
```

### 添加新工具

解耦设计让添加新工具变得非常简单：

```python
from langchain.tools import BaseTool

# 1. 定义新工具
class MyNewTool(BaseTool):
    name = "my_tool"
    description = "工具描述"

    def _run(self, input):
        # 实现逻辑
        return "result"

# 2. 添加到Agent
agent = ReasoningAgent()
agent.add_tool(MyNewTool())

# 3. LLM会自动学会使用新工具！
```

## 🧠 推理能力展示

Agent 能够：

1. **理解不同表达方式**

   - "计算 sqrt(2)保留 3 位小数"
   - "求 2 的平方根，保留 3 位小数"
   - "sqrt(2)的值是多少？保留小数点后 3 位"

2. **自主决策是否需要工具**

   - 数学问题 → 调用 calculator
   - 普通对话 → 直接回答
   - 复杂任务 → 多步推理

3. **多步推理**
   - 分析问题
   - 规划步骤
   - 执行工具
   - 综合答案

## 📊 测试结果

```bash
$ python test_agent.py

✅ 核心测试通过
✅ 扩展测试通过
✅ 推理能力验证通过

特性验证成功：
   • LLM具有推理能力 ✓
   • 能够自主决策何时调用工具 ✓
   • 工具调用准确无误 ✓
   • 解耦设计，架构清晰 ✓
```

## 🔧 配置说明

### config.py

```python
OPENAI_API_KEY = "your_key"      # OpenAI API密钥
LLM_MODEL = "gpt-4-turbo-preview"  # 使用的模型
TEMPERATURE = 0                     # 温度（0=确定性）
```

### 模型选择

- **gpt-4-turbo-preview**: 最强推理能力（推荐）
- **gpt-4**: 稳定版本
- **gpt-3.5-turbo**: 更快但推理能力稍弱

## 🎓 核心概念

### 1. Function Calling

OpenAI 的 Function Calling 让 LLM 能够：

- 识别何时需要外部工具
- 生成正确的函数调用参数
- 理解函数返回结果

### 2. ReAct 模式

**Re**asoning + **Act**ing：

1. **Think**: LLM 思考问题
2. **Act**: LLM 决定调用工具
3. **Observe**: LLM 观察结果
4. **Repeat**: 重复直到解决问题

### 3. 解耦设计

```
┌─────────┐         ┌─────────┐
│   LLM   │ ◄────► │  Tools  │
│ (推理)  │         │ (执行)  │
└─────────┘         └─────────┘
    ↑                    ↑
    └──── 完全解耦 ────┘
```

**优势**：

- LLM 可以换成任何模型
- 工具可以独立升级
- 新工具可以即插即用

## 🚀 扩展方向

### 未来可以添加的工具

1. **图像识别工具**

   ```python
   class VisionTool(BaseTool):
       name = "image_analyzer"
       # 使用GPT-4V或其他视觉模型
   ```

2. **网络搜索工具**

   ```python
   class SearchTool(BaseTool):
       name = "web_search"
       # 集成搜索API
   ```

3. **数据库查询工具**
   ```python
   class DatabaseTool(BaseTool):
       name = "db_query"
       # 执行SQL查询
   ```

## 📝 技术栈

- **LangChain**: Agent 框架
- **OpenAI GPT-4**: 推理 LLM
- **Python 3.8+**: 开发语言

## 🤝 贡献

欢迎提交 Issue 和 PR！

## 📄 许可证

MIT License

---

**作者**: AI Agent Team  
**版本**: 1.0.0  
**更新时间**: 2025-10-23
