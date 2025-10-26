#!/bin/bash
# Unitree G1 部署脚本 - 自动化部署到机器人

set -e  # 遇到错误立即退出

# ============== 配置区 ==============
G1_IP="${G1_IP:-192.168.123.161}"  # G1 默认 IP，可通过环境变量覆盖
G1_USER="${G1_USER:-unitree}"
G1_PASSWORD="${G1_PASSWORD:-123}"
PROJECT_NAME="agent_mvp"
DOCKER_IMAGE="qiayuanl/unitree:jazzy-latest"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "🤖 Unitree G1 Voice Agent 部署工具"
echo "========================================"
echo ""

# ============== Step 1: 检查本地环境 ==============
echo -e "${YELLOW}📦 Step 1: 检查本地环境...${NC}"

if [ ! -f "../.env" ]; then
    echo -e "${RED}❌ 未找到 .env 文件！${NC}"
    echo "请在项目根目录创建 .env 文件并添加："
    echo "OPENAI_API_KEY=your_key_here"
    exit 1
fi

if [ ! -f "../requirements.txt" ]; then
    echo -e "${RED}❌ 未找到 requirements.txt！${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 本地环境检查通过${NC}"
echo ""

# ============== Step 2: 连接 G1 机器人 ==============
echo -e "${YELLOW}📡 Step 2: 连接 G1 机器人 (${G1_IP})...${NC}"

if ! ping -c 1 -W 2 $G1_IP > /dev/null 2>&1; then
    echo -e "${RED}❌ 无法 ping 通 G1 机器人 (${G1_IP})${NC}"
    echo "请检查："
    echo "  1. G1 是否开机"
    echo "  2. 网络连接是否正常"
    echo "  3. IP 地址是否正确"
    exit 1
fi

echo -e "${GREEN}✅ 网络连接正常${NC}"
echo ""

# ============== Step 3: 检查 G1 系统信息 ==============
echo -e "${YELLOW}🔍 Step 3: 检查 G1 系统信息...${NC}"

ssh ${G1_USER}@${G1_IP} << 'EOSSH'
echo "系统版本:"
lsb_release -a 2>/dev/null || cat /etc/os-release

echo ""
echo "Docker 版本:"
docker --version 2>/dev/null || echo "❌ Docker 未安装"

echo ""
echo "磁盘空间:"
df -h / | tail -1
EOSSH

echo ""

# ============== Step 4: 在 G1 上安装 Docker（如果需要）==============
echo -e "${YELLOW}🐳 Step 4: 检查并安装 Docker...${NC}"

ssh ${G1_USER}@${G1_IP} << 'EOSSH'
if ! command -v docker &> /dev/null; then
    echo "正在安装 Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker 安装完成"
else
    echo "✅ Docker 已安装"
fi
EOSSH

echo ""

# ============== Step 5: 拉取 Docker 镜像 ==============
echo -e "${YELLOW}📥 Step 5: 拉取 Docker 镜像 (1.32 GB，请耐心等待)...${NC}"

ssh ${G1_USER}@${G1_IP} << EOSSH
echo "拉取镜像: ${DOCKER_IMAGE}"
docker pull --platform linux/arm64 ${DOCKER_IMAGE}
EOSSH

echo -e "${GREEN}✅ 镜像拉取完成${NC}"
echo ""

# ============== Step 6: 传输项目文件 ==============
echo -e "${YELLOW}📤 Step 6: 传输项目文件到 G1...${NC}"

# 打包项目（排除不必要的文件）
cd ..
tar -czf /tmp/${PROJECT_NAME}.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='logs/*' \
    --exclude='sessions/*' \
    --exclude='temp_audio/*' \
    .

# 传输到 G1
scp /tmp/${PROJECT_NAME}.tar.gz ${G1_USER}@${G1_IP}:/home/${G1_USER}/

# 解压
ssh ${G1_USER}@${G1_IP} << EOSSH
cd /home/${G1_USER}
rm -rf ${PROJECT_NAME}
mkdir -p ${PROJECT_NAME}
tar -xzf ${PROJECT_NAME}.tar.gz -C ${PROJECT_NAME}
rm ${PROJECT_NAME}.tar.gz
echo "✅ 项目文件传输完成"
EOSSH

# 清理本地临时文件
rm /tmp/${PROJECT_NAME}.tar.gz

echo -e "${GREEN}✅ 文件传输完成${NC}"
echo ""

# ============== Step 7: 配置并启动容器 ==============
echo -e "${YELLOW}🚀 Step 7: 配置并启动容器...${NC}"

ssh ${G1_USER}@${G1_IP} << EOSSH
cd /home/${G1_USER}/${PROJECT_NAME}

# 创建并启动容器
docker run -d \
    --name voice-agent \
    --platform linux/arm64 \
    --network host \
    --privileged \
    --device /dev/snd \
    -v \$(pwd):/workspace/agent_mvp \
    -v \$(pwd)/.env:/workspace/agent_mvp/.env:ro \
    -e PYTHONUNBUFFERED=1 \
    -w /workspace/agent_mvp \
    ${DOCKER_IMAGE} \
    tail -f /dev/null

# 等待容器启动
sleep 3

# 在容器内安装依赖
docker exec voice-agent bash -c "
    apt-get update && \
    apt-get install -y python3-pip portaudio19-dev python3-pyaudio && \
    pip3 install -r requirements.txt
"

echo "✅ 容器启动成功"
EOSSH

echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""

# ============== Step 8: 显示使用说明 ==============
echo "========================================"
echo "📋 使用说明"
echo "========================================"
echo ""
echo "1️⃣  进入容器："
echo "   ssh ${G1_USER}@${G1_IP}"
echo "   docker exec -it voice-agent bash"
echo ""
echo "2️⃣  运行 Voice Agent："
echo "   cd /workspace/agent_mvp"
echo "   python3 main_voice.py"
echo ""
echo "3️⃣  查看容器日志："
echo "   docker logs voice-agent"
echo ""
echo "4️⃣  停止容器："
echo "   docker stop voice-agent"
echo ""
echo "5️⃣  重启容器："
echo "   docker restart voice-agent"
echo ""
echo "6️⃣  删除容器："
echo "   docker rm -f voice-agent"
echo ""
echo "========================================"
echo -e "${GREEN}🎉 部署成功！${NC}"
echo "========================================"

