#!/bin/bash
# 语音交互 Agent 启动脚本

# 进入项目根目录
cd "$(dirname "$0")"

# 激活虚拟环境
source venv/bin/activate

# 检查 PyAudio
python -c "import pyaudio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ PyAudio 未安装"
    echo "正在安装 PyAudio..."
    pip install pyaudio
fi

# 启动语音交互程序
echo ""
echo "🎤 启动语音交互 Agent..."
echo ""
python main_voice.py "$@"


