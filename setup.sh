#!/bin/bash
# 自动安装脚本 - Agent MVP 项目
# 适用于 macOS/Linux

set -e  # 遇到错误立即退出

echo "========================================"
echo "🚀 Agent MVP 项目自动安装"
echo "========================================"
echo ""

# 检查 Python 版本
echo "1️⃣  检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 检查 pip
echo "2️⃣  检查 pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ 未找到 pip3，请先安装 pip"
    exit 1
fi
echo "✅ pip3 已安装"
echo ""

# 创建虚拟环境
echo "3️⃣  创建虚拟环境..."
if [ -d "venv" ]; then
    echo "⚠️  虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
fi
echo ""

# 激活虚拟环境
echo "4️⃣  激活虚拟环境..."
source venv/bin/activate
echo "✅ 虚拟环境已激活"
echo ""

# 升级 pip
echo "5️⃣  升级 pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ pip 升级完成"
echo ""

# 安装依赖
echo "6️⃣  安装项目依赖..."
echo "   这可能需要几分钟，请耐心等待..."
pip install -r requirements.txt
echo "✅ 依赖安装完成"
echo ""

# macOS 特殊依赖：PyAudio 需要 portaudio
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "7️⃣  检查 macOS 音频依赖..."
    if ! command -v brew &> /dev/null; then
        echo "⚠️  未找到 Homebrew，跳过 portaudio 安装"
        echo "   如果 PyAudio 报错，请手动运行: brew install portaudio"
    else
        if ! brew list portaudio &> /dev/null; then
            echo "   正在安装 portaudio..."
            brew install portaudio
            echo "✅ portaudio 安装完成"
        else
            echo "✅ portaudio 已安装"
        fi
    fi
    echo ""
fi

# 检查 .env 文件
echo "8️⃣  检查环境变量配置..."
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件"
    echo "   请创建 .env 文件并添加 OpenAI API Key:"
    echo "   OPENAI_API_KEY=your_api_key_here"
    echo ""
    read -p "   是否现在创建 .env 文件？(y/n): " create_env
    if [ "$create_env" == "y" ] || [ "$create_env" == "Y" ]; then
        read -p "   请输入你的 OpenAI API Key: " api_key
        echo "OPENAI_API_KEY=$api_key" > .env
        echo "✅ .env 文件已创建"
    fi
else
    echo "✅ .env 文件已存在"
fi
echo ""

# 创建必要的目录
echo "9️⃣  创建必要的目录..."
mkdir -p logs sessions temp_audio sounds prompts
echo "✅ 目录创建完成"
echo ""

# 完成
echo "========================================"
echo "✅ 安装完成！"
echo "========================================"
echo ""
echo "📋 下一步："
echo "   1. 确保 .env 文件中有正确的 OPENAI_API_KEY"
echo "   2. 运行文本模式: python main.py"
echo "   3. 运行语音模式: python main_voice.py"
echo ""
echo "💡 提示："
echo "   - 每次运行前请先激活虚拟环境: source venv/bin/activate"
echo "   - 查看文档: cat README.md"
echo "   - 查看架构: cat docs/架构与依赖分析.md"
echo ""

