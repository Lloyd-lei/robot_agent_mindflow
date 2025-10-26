# 📥 如何下载项目文件

## 🎯 你有3种方式获取所有文件

---

## 方式1: Git克隆（最简单）⭐

```bash
# 克隆整个项目
git clone https://github.com/Lloyd-lei/robot_agent_mindflow.git

# 进入项目目录
cd robot_agent_mindflow

# 查看所有文件
ls -la
```

**优势:**
- ✅ 一键获取所有文件
- ✅ 包含完整的Git历史
- ✅ 可以轻松更新

---

## 方式2: 下载ZIP压缩包

### 步骤：

1. 访问GitHub仓库:
   ```
   https://github.com/Lloyd-lei/robot_agent_mindflow
   ```

2. 点击绿色的 **"Code"** 按钮

3. 选择 **"Download ZIP"**

4. 解压下载的文件

**优势:**
- ✅ 不需要Git
- ✅ 直接下载
- ❌ 无法轻松更新

---

## 方式3: 文件已在本地（如果你在服务器上）

如果你已经在项目目录中，所有文件都在这里了：

```bash
# 查看当前位置
pwd
# 输出: /home/user/robot_agent_mindflow

# 列出所有文件
ls -la

# 查看新架构文件
tree src/  # 或 find src/ -type f
```

**文件都在这些位置:**
```
/home/user/robot_agent_mindflow/
├── main.py              ⭐ 主入口
├── src/                 📦 源代码
├── docs/                📖 文档
├── examples/            💡 示例
├── README.md            📄 说明
├── QUICKSTART.md        🚀 快速启动
└── requirements.txt     📋 依赖
```

---

## 📋 完整文件列表

查看 `FILES_MANIFEST.md` 了解所有文件的详细说明。

---

## 🚀 下载后怎么办？

### 1. 安装依赖

```bash
cd robot_agent_mindflow
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env，设置 OPENAI_API_KEY=your-key
```

### 3. 启动！

```bash
python main.py
```

详见 [QUICKSTART.md](QUICKSTART.md)

---

## 💾 备份建议

### 定期备份

```bash
# 方式1: Git提交
git add .
git commit -m "我的修改"
git push

# 方式2: 创建ZIP备份
zip -r backup_$(date +%Y%m%d).zip . -x "*.git*" -x "*__pycache__*"

# 方式3: 复制到其他位置
cp -r robot_agent_mindflow ~/backups/robot_agent_mindflow_backup
```

---

## 🔗 相关资源

- **GitHub仓库**: https://github.com/Lloyd-lei/robot_agent_mindflow
- **新架构分支**: `claude/review-project-structure-011CUVaP9m7uSHdn94oVsvwK`
- **问题反馈**: https://github.com/Lloyd-lei/robot_agent_mindflow/issues

---

## ❓ 常见问题

### Q: 我应该用哪种方式下载？

**A:** 
- **有Git** → 方式1（推荐）
- **没有Git** → 方式2
- **已在服务器** → 方式3

### Q: 下载后缺少文件怎么办？

**A:** 
```bash
# 查看文件清单
cat FILES_MANIFEST.md

# 对比本地文件
find . -name "*.py" | wc -l
# 应该有 25+ 个Python文件
```

### Q: 如何更新到最新版本？

**A:** 
```bash
# 如果用Git克隆
git pull origin main

# 如果下载ZIP
# 重新下载最新的ZIP
```

---

**现在就下载开始使用吧！🎉**
