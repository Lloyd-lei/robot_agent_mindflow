# System Prompt 配置说明

## 📁 文件说明

- `system_prompt.txt`: 主系统提示词文件
  - Agent 启动时会**自动加载**此文件
  - 修改后**无需重启代码**，只需重新运行程序即可生效
  - 如果文件不存在或读取失败，会使用 `agent_hybrid.py` 中的默认 prompt 作为备份

## 🛠️ 如何修改 Prompt

### 方式 1：直接编辑文件（推荐）

```bash
# 使用任何文本编辑器打开
vim prompts/system_prompt.txt
# 或
code prompts/system_prompt.txt
# 或
nano prompts/system_prompt.txt
```

修改后保存，重新运行 `python main.py` 即可生效！

### 方式 2：创建多版本 Prompt（高级）

如果你想测试不同的 prompt 策略，可以创建多个文件：

```bash
prompts/
├── system_prompt.txt           # 默认版本
├── system_prompt_aggressive.txt # 更强制的语言切换
├── system_prompt_gentle.txt     # 更温和的交互风格
└── system_prompt_debug.txt      # 调试专用版本
```

然后在代码中切换（需要修改 `agent_hybrid.py` 的 `_create_system_prompt()` 方法）。

## 📝 Prompt 编写建议

### ✅ 优秀的 Prompt 特征

1. **清晰的角色定位**：明确 AI 的身份和能力
2. **结构化规范**：使用标题、列表、示例等组织内容
3. **明确的禁止项**：告诉 AI 什么**不能做**（如禁止输出 emoji）
4. **工具使用强制规则**：明确何时**必须调用**某个工具
5. **示例驱动**：提供正例和反例对比

### ❌ 常见的 Prompt 陷阱

1. **过于啰嗦**：LLM 会模仿 prompt 的风格，冗长的 prompt 导致冗长的回复
2. **规则冲突**：不同规则互相矛盾（如"简洁回答"和"详细解释"）
3. **缺少强制标记**：关键规则没有用"必须"/"强制"/"绝对"等词强调
4. **缺少示例**：复杂规则需要配上具体示例

## 🔧 针对多语言切换的优化建议

如果你发现小语种（日文、法语等）切换不准确，可以尝试：

### 优化 1：强化语言检测规则

在 `system_prompt.txt` 的"重要规则"部分添加：

```txt
🔴 **语言检测强制规则（优先级最高）**：
- 检测到日文假名（ひらがな/カタカナ）→ 立即调用 voiceSelector(language="japanese")
- 检测到西班牙语特征（¿?/Hola/Gracias）→ 立即调用 voiceSelector(language="spanish")
- 检测到法语特征（ç/é/è）→ 立即调用 voiceSelector(language="french")
- 检测到越南语特征（ơ/ư/â）→ 立即调用 voiceSelector(language="vietnamese")

⚠️ 此规则优先级高于其他所有规则！
```

### 优化 2：添加更多示例

在 `system_prompt.txt` 的"示例"部分添加小语种案例：

```txt
用户："こんにちは、今何時ですか？"
→ 第一步：检测到日文假名 → 强制调用 voiceSelector(language="japanese", reason="检测到日文")
→ 第二步：调用 time_tool
→ 第三步：用日文回答
```

### 优化 3：使用更强大的 LLM

如果你有 OpenAI API Key，临时切换到 GPT-4o 测试：

```bash
# 临时切换到 GPT-4o
USE_OLLAMA=false OPENAI_MODEL=gpt-4o-mini python main.py
```

GPT-4o 的多语言识别能力远超 Qwen2.5:3b，能更准确地切换语音。

## 📊 Prompt 版本管理建议

### Git 管理

```bash
# 提交 prompt 修改时，写清楚改动原因
git add prompts/system_prompt.txt
git commit -m "优化 prompt：强化日文语音切换规则"
```

### 回滚到之前的版本

```bash
# 查看历史版本
git log -- prompts/system_prompt.txt

# 恢复到某个版本
git checkout <commit-hash> -- prompts/system_prompt.txt
```

## 🧪 测试你的 Prompt

修改 prompt 后，运行测试验证效果：

```bash
# 测试多语言切换
python test/test_multilingual_voice.py

# 手动测试
python main.py
```

建议测试场景：

- ✅ 中英文混合对话
- ✅ 纯日文/法语/西班牙语输入
- ✅ 长回复是否超过限制
- ✅ 是否还在输出 emoji/markdown
- ✅ "再见"是否正确触发对话结束

## 💡 高级技巧：动态 Prompt

如果你想根据不同场景自动选择 prompt，可以修改 `agent_hybrid.py`：

```python
def _create_system_prompt(self) -> str:
    """根据环境变量选择 prompt 版本"""
    import os
    version = os.getenv("PROMPT_VERSION", "default")  # 支持环境变量
    prompt_file = f"system_prompt_{version}.txt"
    # ... 加载逻辑
```

然后：

```bash
# 使用温和版本
PROMPT_VERSION=gentle python main.py

# 使用激进版本（强制工具调用）
PROMPT_VERSION=aggressive python main.py
```

---

**祝你调试愉快！🚀**
