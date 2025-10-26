#!/bin/bash
# 在 G1 机器人上直接运行此脚本来启动 Voice Agent

set -e

DOCKER_IMAGE="qiayuanl/unitree:jazzy-latest"
CONTAINER_NAME="voice-agent"

echo "🤖 Unitree G1 Voice Agent - Docker 运行脚本"
echo "============================================"
echo ""

# 检查容器是否已存在
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo "⚠️  容器已存在，正在删除旧容器..."
    docker rm -f $CONTAINER_NAME
fi

# 检查镜像是否存在
if ! docker images | grep -q "qiayuanl/unitree"; then
    echo "📥 拉取 Docker 镜像..."
    docker pull --platform linux/arm64 $DOCKER_IMAGE
fi

# 获取当前目录
WORK_DIR=$(cd "$(dirname "$0")/.." && pwd)

echo "📁 项目目录: $WORK_DIR"
echo ""

# 检查 .env 文件
if [ ! -f "$WORK_DIR/.env" ]; then
    echo "❌ 未找到 .env 文件！"
    echo "请创建 .env 文件并添加："
    echo "OPENAI_API_KEY=your_key_here"
    exit 1
fi

echo "🚀 启动容器..."

# 启动容器
docker run -d \
    --name $CONTAINER_NAME \
    --platform linux/arm64 \
    --network host \
    --privileged \
    --device /dev/snd \
    -v "$WORK_DIR:/workspace/agent_mvp" \
    -v "$WORK_DIR/.env:/workspace/agent_mvp/.env:ro" \
    -e PYTHONUNBUFFERED=1 \
    -w /workspace/agent_mvp \
    $DOCKER_IMAGE \
    tail -f /dev/null

echo "⏳ 等待容器启动..."
sleep 3

echo "📦 安装 Python 依赖..."
docker exec $CONTAINER_NAME bash -c "
    apt-get update -qq && \
    apt-get install -y -qq python3-pip portaudio19-dev python3-pyaudio && \
    pip3 install -q -r requirements.txt
"

echo ""
echo "✅ 容器启动成功！"
echo ""
echo "============================================"
echo "📋 快速命令"
echo "============================================"
echo ""
echo "进入容器："
echo "  docker exec -it $CONTAINER_NAME bash"
echo ""
echo "运行 Voice Agent："
echo "  docker exec -it $CONTAINER_NAME python3 /workspace/agent_mvp/main_voice.py"
echo ""
echo "查看日志："
echo "  docker logs -f $CONTAINER_NAME"
echo ""
echo "停止容器："
echo "  docker stop $CONTAINER_NAME"
echo ""
echo "============================================"
echo ""
echo "🎙️  现在可以运行 Voice Agent 了！"
echo "   docker exec -it $CONTAINER_NAME python3 /workspace/agent_mvp/main_voice.py"

