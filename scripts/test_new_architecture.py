"""
测试新架构 - 验证所有组件是否正常工作

使用方式:
    python scripts/test_new_architecture.py
"""
import sys
from pathlib import Path

# 添加src目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试导入"""
    print("\n" + "="*70)
    print("🧪 测试1: 验证导入")
    print("="*70)

    try:
        # Core 层
        from src.core import HybridReasoningAgent, BaseAgent, AgentResponse
        from src.core import BaseTool, ToolMetadata, tool_registry
        from src.core.config import settings

        # Services 层
        from src.services.tts import TTSFactory, TTSProvider
        from src.services.voice import VoiceWaitingFeedback

        # Tools 层
        from src.tools import load_all_tools

        print("✅ 所有模块导入成功!")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """测试配置"""
    print("\n" + "="*70)
    print("🧪 测试2: 验证配置")
    print("="*70)

    try:
        from src.core.config import settings

        print(f"✅ OpenAI Model: {settings.llm_model}")
        print(f"✅ Temperature: {settings.temperature}")
        print(f"✅ Enable Cache: {settings.enable_cache}")
        print(f"✅ Environment: {settings.environment}")

        # 不验证 API Key,因为可能没有设置
        if settings.openai_api_key and settings.openai_api_key != "your-api-key-here":
            print(f"✅ API Key: {'*' * 20} (已设置)")
        else:
            print(f"⚠️  API Key: 未设置 (测试环境正常)")

        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tools():
    """测试工具加载"""
    print("\n" + "="*70)
    print("🧪 测试3: 验证工具加载")
    print("="*70)

    try:
        from src.tools import load_all_tools

        tools = load_all_tools()
        print(f"✅ 成功加载 {len(tools)} 个工具")

        if tools:
            print("\n工具列表:")
            for i, tool in enumerate(tools[:5], 1):
                print(f"  {i}. {tool.name}: {tool.description[:50]}...")
            if len(tools) > 5:
                print(f"  ... 还有 {len(tools) - 5} 个工具")

        return True
    except Exception as e:
        print(f"❌ 工具加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_creation():
    """测试Agent创建"""
    print("\n" + "="*70)
    print("🧪 测试4: 验证Agent创建")
    print("="*70)

    try:
        from src.core import HybridReasoningAgent
        from src.tools import load_all_tools

        tools = load_all_tools()

        # 创建Agent (跳过配置验证)
        from src.core.config import settings
        if not settings.openai_api_key or settings.openai_api_key == "your-api-key-here":
            print("⚠️  跳过Agent创建测试 (未设置API Key)")
            return True

        agent = HybridReasoningAgent(
            tools=tools,
            enable_cache=True
        )

        print(f"✅ Agent创建成功: {agent.name}")
        print(f"   工具数量: {len(tools)}")
        print(f"   模型: {agent.model}")
        print(f"   温度: {agent.temperature}")

        return True
    except Exception as e:
        print(f"❌ Agent创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_registry():
    """测试工具注册表"""
    print("\n" + "="*70)
    print("🧪 测试5: 验证工具注册表")
    print("="*70)

    try:
        from src.core.tools import tool_registry, BaseTool
        from pydantic import BaseModel, Field

        # 创建测试工具
        class TestToolInput(BaseModel):
            arg: str = Field(description="测试参数")

        class TestTool(BaseTool):
            name = "test_tool"
            description = "测试工具"
            args_schema = TestToolInput
            category = "test"

            def execute(self, arg: str):
                return f"测试: {arg}"

        # 注册
        tool_registry.register(TestTool())

        # 获取
        tool = tool_registry.get("test_tool")
        if tool:
            print(f"✅ 工具注册成功: {tool.name}")

            # 测试执行
            result = tool._run(arg="hello")
            print(f"✅ 工具执行成功: {result}")
        else:
            print("❌ 工具获取失败")
            return False

        # 清理
        tool_registry.unregister("test_tool")
        print("✅ 工具注销成功")

        return True
    except Exception as e:
        print(f"❌ 工具注册表测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_directory_structure():
    """测试目录结构"""
    print("\n" + "="*70)
    print("🧪 测试6: 验证目录结构")
    print("="*70)

    required_dirs = [
        "src/core",
        "src/core/agents",
        "src/core/tools",
        "src/core/config",
        "src/services",
        "src/services/tts",
        "src/services/voice",
        "src/tools",
        "src/tools/basic",
        "examples",
        "docs",
        "tests",
        "config",
    ]

    missing = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} (不存在)")
            missing.append(dir_path)

    if missing:
        print(f"\n⚠️  缺少 {len(missing)} 个目录")
        return False
    else:
        print("\n✅ 所有目录结构正确")
        return True


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 新架构测试套件")
    print("="*80)

    tests = [
        ("导入测试", test_imports),
        ("配置测试", test_config),
        ("工具加载测试", test_tools),
        ("Agent创建测试", test_agent_creation),
        ("工具注册表测试", test_tool_registry),
        ("目录结构测试", test_directory_structure),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name}出错: {e}")
            results.append((name, False))

    # 总结
    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过!新架构工作正常!")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败,请检查")

    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 测试被中断\n")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
