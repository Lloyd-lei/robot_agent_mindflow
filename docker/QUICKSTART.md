# 🚀 Docker 快速开始 - 5 分钟部署

## ⚡ 最快方式（推荐）

### **在你的 MacBook 上运行：**

```bash
# 1. 进入 docker 目录
cd /Users/yudonglei/Desktop/agent_mvp/docker

# 2. 设置 G1 IP 地址（如果不是默认的 192.168.123.161）
export G1_IP=192.168.123.161

# 3. 运行一键部署脚本
./deploy_to_g1.sh
```

**完成！** 🎉

脚本会自动：
- ✅ 连接到 G1 机器人
- ✅ 安装 Docker
- ✅ 拉取 Jazzy 镜像（1.32 GB）
- ✅ 传输项目文件
- ✅ 启动容器
- ✅ 安装所有依赖

---

## 🎙️ 运行 Voice Agent

部署完成后，SSH 登录到 G1：

```bash
ssh unitree@192.168.123.161

# 运行 Voice Agent
docker exec -it voice-agent python3 /workspace/agent_mvp/main_voice.py
```

---

## 🔄 或者在 G1 上直接部署

### **1. SSH 登录到 G1**

```bash
ssh unitree@192.168.123.161
```

### **2. 克隆项目**

```bash
cd ~
git clone https://github.com/Lloyd-lei/robot_agent_mindflow.git
cd robot_agent_mindflow
```

### **3. 配置 API Key**

```bash
nano .env

# 添加：
OPENAI_API_KEY=sk-your_key_here
```

### **4. 运行部署脚本**

```bash
cd docker
chmod +x run_in_docker.sh
./run_in_docker.sh
```

### **5. 启动 Voice Agent**

```bash
docker exec -it voice-agent python3 /workspace/agent_mvp/main_voice.py
```

---

## 📋 常用命令

```bash
# 进入容器
docker exec -it voice-agent bash

# 查看日志
docker logs -f voice-agent

# 停止容器
docker stop voice-agent

# 重启容器
docker restart voice-agent

# 删除容器
docker rm -f voice-agent
```

---

## ❓ 遇到问题？

查看完整文档：`README_DOCKER.md`

或直接联系：提交 GitHub Issue

