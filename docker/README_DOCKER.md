# 🐳 Docker 部署指南 - Unitree G1

## 📋 目录

1. [快速开始](#快速开始)
2. [手动部署](#手动部署)
3. [Docker 镜像说明](#docker-镜像说明)
4. [故障排除](#故障排除)
5. [常用命令](#常用命令)

---

## 🚀 快速开始

### **方案 A: 一键自动部署**（推荐）

在你的**开发机**（MacBook）上运行：

```bash
cd agent_mvp/docker

# 设置 G1 IP 地址（如果不是默认的）
export G1_IP=192.168.123.161

# 运行部署脚本
chmod +x deploy_to_g1.sh
./deploy_to_g1.sh
```

脚本会自动：
- ✅ 检查网络连接
- ✅ 安装 Docker（如果需要）
- ✅ 拉取镜像（1.32 GB）
- ✅ 传输项目文件
- ✅ 启动容器
- ✅ 安装依赖

---

### **方案 B: 在 G1 上手动运行**

1. **SSH 登录到 G1：**
   ```bash
   ssh unitree@192.168.123.161
   ```

2. **下载项目：**
   ```bash
   cd ~
   git clone https://github.com/Lloyd-lei/robot_agent_mindflow.git
   cd robot_agent_mindflow
   ```

3. **配置环境变量：**
   ```bash
   nano .env
   # 添加：OPENAI_API_KEY=sk-your_key_here
   ```

4. **运行部署脚本：**
   ```bash
   cd docker
   chmod +x run_in_docker.sh
   ./run_in_docker.sh
   ```

5. **启动 Voice Agent：**
   ```bash
   docker exec -it voice-agent python3 /workspace/agent_mvp/main_voice.py
   ```

---

## 📦 Docker 镜像说明

### **qiayuanl/unitree:jazzy-latest**

| 属性 | 值 |
|------|-----|
| **镜像名称** | `qiayuanl/unitree:jazzy-latest` |
| **平台** | `linux/arm64` |
| **大小** | 1.32 GB |
| **基础系统** | Ubuntu 24.04 LTS |
| **ROS 版本** | ROS 2 Jazzy |
| **架构** | ARM64（适配 Unitree G1） |

### **包含内容：**
- ✅ ROS 2 Jazzy 完整环境
- ✅ Unitree SDK
- ✅ Python 3.12
- ✅ 常用开发工具

---

## 🔧 手动部署（分步骤）

### **Step 1: 安装 Docker**

在 G1 上：

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 重新登录使用户组生效
exit
# 重新 SSH 登录
```

### **Step 2: 拉取镜像**

```bash
# 拉取 ARM64 镜像（1.32 GB）
docker pull --platform linux/arm64 qiayuanl/unitree:jazzy-latest

# 验证
docker images | grep unitree
```

### **Step 3: 创建并运行容器**

```bash
cd ~/robot_agent_mindflow

# 启动容器
docker run -d \
    --name voice-agent \
    --platform linux/arm64 \
    --network host \
    --privileged \
    --device /dev/snd \
    -v $(pwd):/workspace/agent_mvp \
    -v $(pwd)/.env:/workspace/agent_mvp/.env:ro \
    -e PYTHONUNBUFFERED=1 \
    -w /workspace/agent_mvp \
    qiayuanl/unitree:jazzy-latest \
    tail -f /dev/null
```

### **Step 4: 安装依赖**

```bash
# 进入容器
docker exec -it voice-agent bash

# 在容器内
apt-get update
apt-get install -y python3-pip portaudio19-dev python3-pyaudio
pip3 install -r requirements.txt

# 退出容器
exit
```

### **Step 5: 运行 Voice Agent**

```bash
# 从宿主机直接运行
docker exec -it voice-agent python3 /workspace/agent_mvp/main_voice.py

# 或进入容器交互式运行
docker exec -it voice-agent bash
cd /workspace/agent_mvp
python3 main_voice.py
```

---

## 🐛 故障排除

### **问题 1: 拉取镜像超时**

```bash
# 使用国内镜像源
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker
```

### **问题 2: 权限错误**

```bash
# 添加用户到 docker 组
sudo usermod -aG docker $USER

# 重新登录
exit
# SSH 重新登录
```

### **问题 3: 音频设备不可用**

```bash
# 检查音频设备
ls -l /dev/snd/

# 给容器足够的权限
docker run --privileged --device /dev/snd ...
```

### **问题 4: 网络连接失败**

```bash
# 进入容器测试
docker exec -it voice-agent bash
ping -c 3 api.openai.com
curl -I https://api.openai.com

# 检查 DNS
cat /etc/resolv.conf

# 如果 DNS 有问题，手动设置
docker run --dns 8.8.8.8 --dns 8.8.4.4 ...
```

### **问题 5: Python 依赖安装失败**

```bash
# 更新 pip
docker exec voice-agent pip3 install --upgrade pip

# 使用国内源
docker exec voice-agent pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 📝 常用命令

### **容器管理**

```bash
# 查看运行中的容器
docker ps

# 查看所有容器
docker ps -a

# 启动容器
docker start voice-agent

# 停止容器
docker stop voice-agent

# 重启容器
docker restart voice-agent

# 删除容器
docker rm -f voice-agent
```

### **容器交互**

```bash
# 进入容器（交互式）
docker exec -it voice-agent bash

# 在容器中执行命令
docker exec voice-agent python3 -c "print('Hello')"

# 查看容器日志
docker logs voice-agent
docker logs -f voice-agent  # 实时查看

# 查看容器资源使用
docker stats voice-agent
```

### **文件操作**

```bash
# 从容器复制文件到宿主机
docker cp voice-agent:/workspace/agent_mvp/logs/agent.log ./

# 从宿主机复制文件到容器
docker cp ./config.py voice-agent:/workspace/agent_mvp/
```

### **调试**

```bash
# 查看容器详细信息
docker inspect voice-agent

# 查看容器进程
docker top voice-agent

# 查看容器网络
docker exec voice-agent ip addr show
```

---

## 🔄 更新项目

### **方法 1: 卷挂载自动同步**

项目目录已挂载到容器，直接在宿主机修改文件即可：

```bash
# 在 G1 上
cd ~/robot_agent_mindflow
git pull

# 容器内立即生效，重启 Python 程序即可
```

### **方法 2: 重新部署**

```bash
# 删除旧容器
docker rm -f voice-agent

# 重新运行部署脚本
./docker/run_in_docker.sh
```

---

## 📊 性能优化

### **1. 限制资源使用**

```bash
docker run \
    --memory="2g" \
    --cpus="2.0" \
    ...
```

### **2. 使用 Docker Compose**

```bash
cd docker
docker-compose up -d
docker-compose logs -f
```

---

## 🎯 生产环境建议

1. **使用 systemd 管理容器**
   ```bash
   sudo docker run -d --restart=always ...
   ```

2. **配置日志轮转**
   ```bash
   docker run --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 ...
   ```

3. **监控容器健康**
   ```bash
   docker run --health-cmd="python3 -c 'import openai'" ...
   ```

---

## 📚 参考资源

- [Docker 官方文档](https://docs.docker.com/)
- [ROS 2 Jazzy 文档](https://docs.ros.org/en/jazzy/)
- [Unitree Robotics 官方](https://www.unitree.com/)

---

**遇到问题？**
- 查看日志：`docker logs voice-agent`
- 进入容器调试：`docker exec -it voice-agent bash`
- 提交 Issue：[GitHub Issues](https://github.com/Lloyd-lei/robot_agent_mindflow/issues)

