# 🦙 Ollama 本地模型使用指南

## 🎯 为什么选择 Ollama + Qwen2.5

✅ **完全免费** - 无 API 成本  
✅ **隐私保护** - 数据不出本地  
✅ **速度更快** - 本地运行，无网络延迟  
✅ **中文友好** - Qwen2.5 对中文支持极佳  
✅ **随时切换** - 一行配置即可切回 OpenAI

---

## 📦 安装步骤

### 1. 安装 Ollama

**macOS:**

```bash
brew install ollama
```

**Linux:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
下载安装包：https://ollama.com/download

### 2. 启动 Ollama 服务

```bash
ollama serve
```

> 💡 提示：这个命令会启动后台服务，保持终端打开

### 3. 下载 Qwen2.5 模型

**另开一个终端**，运行：

```bash
# 推荐：3B 版本（速度快，质量好，2GB）⭐
ollama pull qwen2.5:3b

# 或者：1.5B 版本（速度最快，1GB）
# ollama pull qwen2.5:1.5b

# 或者：7B 版本（质量更好，但较慢，4.7GB）
# ollama pull qwen2.5:7b

# 或者：14B 版本（质量最高，最慢，8.7GB）
# ollama pull qwen2.5:14b
```

### 4. 测试模型是否正常

```bash
ollama run qwen2.5:7b
```

输入 `你好`，如果模型正常回复，说明安装成功！按 `/bye` 退出。

---

## ⚙️ 配置项目

项目已经自动配置好了，`.env` 文件默认使用 Ollama：

```bash
USE_OLLAMA=true
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_BASE_URL=http://localhost:11434/v1
```

如果你下载了其他模型，修改 `OLLAMA_MODEL` 即可：

```bash
# 例如使用 7B 版本（更高质量）
OLLAMA_MODEL=qwen2.5:7b

# 或使用 1.5B 版本（更快速度）
OLLAMA_MODEL=qwen2.5:1.5b

# 或使用 Llama 3.1
OLLAMA_MODEL=llama3.1:8b
```

---

## 🚀 运行项目

确保 Ollama 服务正在运行（`ollama serve`），然后：

```bash
cd /Users/yudonglei/Desktop/agent_mvp
python demo_hybrid.py streaming
```

---

## 🔄 切换回 OpenAI

只需修改 `.env` 文件：

```bash
USE_OLLAMA=false
OPENAI_API_KEY=sk-your-actual-key
```

---

## 📊 模型性能对比

| 模型         | 大小  | 速度       | 质量       | 推荐场景                  |
| ------------ | ----- | ---------- | ---------- | ------------------------- |
| qwen2.5:1.5b | 1GB   | ⚡⚡⚡⚡⚡ | ⭐⭐⭐     | 快速测试、低配机器        |
| qwen2.5:3b   | 2GB   | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐   | **日常使用（推荐）** ⭐   |
| qwen2.5:7b   | 4.7GB | ⚡⚡⚡⚡   | ⭐⭐⭐⭐   | 高质量需求、配置较好机器  |
| qwen2.5:14b  | 8.7GB | ⚡⚡⚡     | ⭐⭐⭐⭐⭐ | 最高质量、高配机器        |
| llama3.2:3b  | 2GB   | ⚡⚡⚡⚡   | ⭐⭐⭐     | 英文为主                  |
| llama3.1:8b  | 4.7GB | ⚡⚡⚡     | ⭐⭐⭐⭐   | 通用场景                  |

---

## 🛠️ 常见问题

### Q1: Ollama 服务未启动

**错误信息：** `Connection refused` 或 `Failed to connect`

**解决方法：**

```bash
# 启动 Ollama 服务
ollama serve
```

### Q2: 模型未下载

**错误信息：** `model not found`

**解决方法：**

```bash
ollama pull qwen2.5:7b
```

### Q3: 端口被占用

**错误信息：** `address already in use`

**解决方法：**

```bash
# 检查占用进程
lsof -i :11434

# 杀死进程（替换 PID）
kill -9 <PID>

# 或修改 .env 中的端口
OLLAMA_BASE_URL=http://localhost:11435/v1
```

### Q4: 如何查看已下载的模型

```bash
ollama list
```

### Q5: 如何删除模型

```bash
ollama rm qwen2.5:7b
```

---

## 🎨 高级配置

### 自定义系统资源

```bash
# 限制 GPU 使用（如果有独显）
CUDA_VISIBLE_DEVICES=0 ollama serve

# 限制 CPU 核心数
OMP_NUM_THREADS=4 ollama serve
```

### 使用其他 Ollama 服务器

如果你在远程服务器上运行 Ollama：

```bash
# .env
OLLAMA_BASE_URL=http://192.168.1.100:11434/v1
```

---

## 🔍 架构说明

项目使用了 **OpenAI 兼容接口**，所以切换非常简单：

```python
# agent_hybrid.py
if config.LLM_BASE_URL:
    # 使用 Ollama（或其他兼容服务）
    self.client = OpenAI(api_key="ollama", base_url=config.LLM_BASE_URL)
else:
    # 使用 OpenAI 官方服务
    self.client = OpenAI(api_key=config.OPENAI_API_KEY)
```

**所有工具、TTS、流式输出都完全兼容！**

---

## 📝 总结

1. ✅ 安装 Ollama：`brew install ollama`
2. ✅ 启动服务：`ollama serve`
3. ✅ 下载模型：`ollama pull qwen2.5:7b`
4. ✅ 运行项目：`python demo_hybrid.py streaming`

**就这么简单！**🎉
