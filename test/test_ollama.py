#!/usr/bin/env python
"""
Ollama 配置测试脚本

功能：
1. 检查 Ollama 服务是否运行
2. 检查模型是否已下载
3. 测试基础对话功能
4. 测试工具调用功能
"""

import sys
import requests
from colorama import Fore, Style, init

init(autoreset=True)

def check_ollama_service():
    """检查 Ollama 服务是否运行"""
    print(f"\n{Fore.CYAN}【步骤 1】检查 Ollama 服务状态{Style.RESET_ALL}")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"{Fore.GREEN}✅ Ollama 服务正在运行！{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Ollama 服务状态异常（状态码：{response.status_code}）{Style.RESET_ALL}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ 无法连接到 Ollama 服务{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 请运行: ollama serve{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ 检查服务时出错: {e}{Style.RESET_ALL}")
        return False


def check_model_exists(model_name="qwen2.5:7b"):
    """检查模型是否已下载"""
    print(f"\n{Fore.CYAN}【步骤 2】检查模型 {model_name} 是否存在{Style.RESET_ALL}")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            if model_name in model_names:
                print(f"{Fore.GREEN}✅ 模型 {model_name} 已下载！{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}❌ 模型 {model_name} 未找到{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}📋 已下载的模型: {', '.join(model_names) if model_names else '(无)'}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}💡 请运行: ollama pull {model_name}{Style.RESET_ALL}")
                return False
        else:
            print(f"{Fore.RED}❌ 获取模型列表失败{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ 检查模型时出错: {e}{Style.RESET_ALL}")
        return False


def test_basic_chat():
    """测试基础对话功能"""
    print(f"\n{Fore.CYAN}【步骤 3】测试基础对话{Style.RESET_ALL}")
    
    try:
        from openai import OpenAI
        import config
        
        print(f"📊 使用模型: {config.LLM_MODEL}")
        print(f"📊 使用地址: {config.LLM_BASE_URL}")
        
        # 创建客户端
        if config.LLM_BASE_URL:
            client = OpenAI(api_key="ollama", base_url=config.LLM_BASE_URL)
        else:
            client = OpenAI(api_key=config.LLM_API_KEY)
        
        # 测试对话
        print(f"{Fore.YELLOW}⏳ 正在测试基础对话（这可能需要几秒钟）...{Style.RESET_ALL}")
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "user", "content": "请用一句话介绍你自己"}
            ],
            temperature=0
        )
        
        answer = response.choices[0].message.content
        print(f"{Fore.GREEN}✅ 基础对话测试成功！{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🤖 模型回复: {answer}{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ 基础对话测试失败: {e}{Style.RESET_ALL}")
        return False


def test_function_calling():
    """测试工具调用功能"""
    print(f"\n{Fore.CYAN}【步骤 4】测试工具调用（Function Calling）{Style.RESET_ALL}")
    
    try:
        from openai import OpenAI
        import config
        
        # 创建客户端
        if config.LLM_BASE_URL:
            client = OpenAI(api_key="ollama", base_url=config.LLM_BASE_URL)
        else:
            client = OpenAI(api_key=config.LLM_API_KEY)
        
        # 定义一个简单的工具
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "获取当前时间",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
        
        # 测试工具调用
        print(f"{Fore.YELLOW}⏳ 正在测试工具调用...{Style.RESET_ALL}")
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "user", "content": "现在几点了？"}
            ],
            tools=tools,
            tool_choice="auto"
        )
        
        # 检查是否调用了工具
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            print(f"{Fore.GREEN}✅ 工具调用测试成功！{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🔧 调用的工具: {tool_call.function.name}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.YELLOW}⚠️  模型没有调用工具（可能不支持 Function Calling）{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 建议：部分 Ollama 模型可能不完全支持工具调用，但基础对话功能正常{Style.RESET_ALL}")
            return False
        
    except Exception as e:
        print(f"{Fore.RED}❌ 工具调用测试失败: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 说明：部分 Ollama 模型可能不支持 OpenAI 的 Function Calling 格式{Style.RESET_ALL}")
        return False


def main():
    """主测试流程"""
    print(f"\n{Fore.GREEN}{'='*60}")
    print(f"  🦙 Ollama 配置测试工具")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # 步骤 1: 检查服务
    if not check_ollama_service():
        print(f"\n{Fore.RED}❌ 测试终止：Ollama 服务未运行{Style.RESET_ALL}")
        return False
    
    # 步骤 2: 检查模型
    if not check_model_exists():
        print(f"\n{Fore.RED}❌ 测试终止：模型未下载{Style.RESET_ALL}")
        return False
    
    # 步骤 3: 测试基础对话
    if not test_basic_chat():
        print(f"\n{Fore.RED}❌ 测试终止：基础对话失败{Style.RESET_ALL}")
        return False
    
    # 步骤 4: 测试工具调用（不影响整体结果）
    test_function_calling()
    
    # 总结
    print(f"\n{Fore.GREEN}{'='*60}")
    print(f"  ✅ Ollama 配置测试完成！")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}📝 下一步：{Style.RESET_ALL}")
    print(f"   python demo_hybrid.py streaming")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  测试被用户中断{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ 测试过程中出现异常: {e}{Style.RESET_ALL}")
        sys.exit(1)

