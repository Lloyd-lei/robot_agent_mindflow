# 多模态 AI Agent MVP - 推理与函数调用架构

## 🎯 项目概述

这是一个**具有推理能力和自主函数调用的 LLM Agent 架构**，采用解耦设计，LLM 负责推理决策，工具负责具体执行。

### 核心特性

✅ **推理能力**: 基于 OpenAI GPT-4 的强大推理能力  
✅ **自主工具调用**: LLM 自主决策何时调用哪个工具  
✅ **解耦架构**: LLM 与工具完全解耦，易于扩展  
✅ **Function Calling**: 使用 OpenAI 原生 Function Calling  
✅ **ReAct 模式**: Reasoning + Acting 循环推理

## 📁 项目结构

```
agent_mvp/
├── config.py           # 配置管理
├── tools.py            # 工具模块（计算器等）
├── agent.py            # Agent核心逻辑
├── test_agent.py       # 测试脚本
├── requirements.txt    # 依赖包
└── README.md          # 本文件
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────┐
│           用户输入 (User Input)              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│      Agent 编排层 (ReasoningAgent)          │
│      • 接收输入                              │
│      • 管理推理流程                          │
│      • 协调LLM和工具                         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│       LLM 推理核心 (GPT-4)                  │
│       • 理解问题                             │
│       • 推理分析                             │
│       • 决策调用哪个工具                     │
│       • 生成最终答案                         │
└─────────────────────────────────────────────┘
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
┌───────────────┐      ┌────────────────┐
│ 计算器工具     │      │  未来工具...    │
│ (独立模块)     │      │  (可扩展)       │
└───────────────┘      └────────────────┘
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件（已提供 API Key 在 config.py 中）：

```bash
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-4-turbo-preview
TEMPERATURE=0
```

### 3. 运行测试

```bash
# 完整测试
python test_agent.py

# 或者直接测试Agent
python agent.py

# 或者测试工具
python tools.py
```

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
