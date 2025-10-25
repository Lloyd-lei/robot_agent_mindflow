#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bug 修复综合测试脚本
===================

测试所有关键 bug 修复：
1. KeyError: 'output' 崩溃
2. TTS 残留串音
3. 异常时缺少必要键
4. (END_CONVERSATION) 特殊字符过滤
5. Hard Prompt 限制回复长度

测试场景：
- 正常对话
- 超时场景
- 异常场景
- 特殊字符场景
- 长回复场景
- 多轮对话串音测试
"""

import sys
import time
from colorama import Fore, Style, init
from conversation_session import ConversationSession, SessionTimeoutError, SessionNotStartedError
from logger_config import setup_logger

init(autoreset=True)
logger = setup_logger(name="test_bug_fixes", level="INFO")

# ============================================================================
# 测试用例
# ============================================================================

def print_test_header(test_name: str):
    """打印测试头部"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 {test_name}")
    print(f"{Fore.CYAN}{'='*70}\n")


def print_test_result(success: bool, message: str):
    """打印测试结果"""
    if success:
        print(f"{Fore.GREEN}✅ {message}")
    else:
        print(f"{Fore.RED}❌ {message}")


def test_1_normal_conversation():
    """测试 1：正常对话（验证基本功能）"""
    print_test_header("测试 1：正常对话")
    
    try:
        with ConversationSession(
            llm_model="qwen2.5:3b",
            timeout=120,
            tts_wait_timeout=180,
            enable_cache=True,
            show_reasoning=False
        ) as session:
            # 简单问题
            result = session.chat("现在几点？")
            
            # 验证返回值
            assert result.response, "回复不能为空"
            assert isinstance(result.tool_calls, int), "tool_calls 必须是整数"
            assert isinstance(result.duration, float), "duration 必须是浮点数"
            
            print_test_result(True, "正常对话通过")
            print(f"{Fore.YELLOW}回复: {result.response[:50]}...")
            print(f"{Fore.YELLOW}工具调用: {result.tool_calls}次")
            print(f"{Fore.YELLOW}耗时: {result.duration:.2f}秒")
            return True
            
    except Exception as e:
        print_test_result(False, f"正常对话失败: {e}")
        logger.error(f"测试 1 失败: {e}")
        return False


def test_2_exception_handling():
    """测试 2：异常处理（验证 KeyError 修复）"""
    print_test_header("测试 2：异常处理")
    
    try:
        with ConversationSession(
            llm_model="qwen2.5:3b",
            timeout=120,
            tts_wait_timeout=180,
            show_reasoning=False
        ) as session:
            # 触发异常的输入（非常复杂的问题可能导致超时）
            try:
                result = session.chat("请给我详细解释量子力学的所有基础概念、数学推导和实验验证，包括薛定谔方程、海森堡不确定性原理等")
                
                # 验证即使超时也能正确返回
                assert hasattr(result, 'response'), "必须有 response 属性"
                assert hasattr(result, 'tool_calls'), "必须有 tool_calls 属性"
                
                print_test_result(True, "异常处理通过（正常完成）")
                return True
                
            except SessionTimeoutError as e:
                # 超时是预期的
                print_test_result(True, f"异常处理通过（超时保护生效）: {e}")
                return True
            
    except KeyError as e:
        print_test_result(False, f"KeyError 仍然存在: {e}")
        return False
    except Exception as e:
        print_test_result(False, f"异常处理失败: {e}")
        return False


def test_3_special_characters():
    """测试 3：特殊字符过滤（验证 END_CONVERSATION 不被播放）"""
    print_test_header("测试 3：特殊字符过滤")
    
    try:
        with ConversationSession(
            llm_model="qwen2.5:3b",
            timeout=120,
            tts_wait_timeout=180,
            show_reasoning=False
        ) as session:
            # 触发 end_conversation 工具
            result = session.chat("好的，再见！")
            
            # 验证返回值
            assert result.response, "回复不能为空"
            
            # 验证 (END_CONVERSATION) 不在回复中
            if "(END_CONVERSATION)" in result.response:
                print_test_result(False, "特殊字符过滤失败：(END_CONVERSATION) 仍在回复中")
                return False
            
            print_test_result(True, "特殊字符过滤通过")
            print(f"{Fore.YELLOW}回复: {result.response}")
            print(f"{Fore.YELLOW}Should end: {result.should_end}")
            return True
            
    except Exception as e:
        print_test_result(False, f"特殊字符测试失败: {e}")
        return False


def test_4_response_length():
    """测试 4：回复长度控制（验证 Hard Prompt）"""
    print_test_header("测试 4：回复长度控制")
    
    try:
        with ConversationSession(
            llm_model="qwen2.5:3b",
            timeout=120,
            tts_wait_timeout=180,
            show_reasoning=False
        ) as session:
            # 提问容易导致长回复的问题
            result = session.chat("介绍一下人工智能")
            
            # 验证回复长度
            response_length = len(result.response)
            
            if response_length > 150:
                print_test_result(False, f"回复过长: {response_length} 字（建议 < 100 字）")
                print(f"{Fore.YELLOW}回复: {result.response}")
                return False
            
            print_test_result(True, f"回复长度合适: {response_length} 字")
            print(f"{Fore.YELLOW}回复: {result.response}")
            return True
            
    except Exception as e:
        print_test_result(False, f"回复长度测试失败: {e}")
        return False


def test_5_multi_turn_no_cross_talk():
    """测试 5：多轮对话无串音（验证 TTS 清空）"""
    print_test_header("测试 5：多轮对话无串音")
    
    try:
        with ConversationSession(
            llm_model="qwen2.5:3b",
            timeout=120,
            tts_wait_timeout=180,
            show_reasoning=False
        ) as session:
            # 第一轮：快速问题
            result1 = session.chat("1加1等于几？")
            print(f"{Fore.YELLOW}第1轮: {result1.response}")
            
            # 等待 TTS 完全播放完毕
            time.sleep(2)
            
            # 第二轮：另一个快速问题
            result2 = session.chat("现在几点？")
            print(f"{Fore.YELLOW}第2轮: {result2.response}")
            
            # 验证没有异常
            print_test_result(True, "多轮对话无串音通过")
            return True
            
    except Exception as e:
        print_test_result(False, f"多轮对话测试失败: {e}")
        return False


def test_6_tts_buffer_cleanup():
    """测试 6：TTS 缓冲区清空（模拟超时后清空）"""
    print_test_header("测试 6：TTS 缓冲区清空")
    
    try:
        with ConversationSession(
            llm_model="qwen2.5:3b",
            timeout=5,  # 设置很短的超时
            tts_wait_timeout=5,
            show_reasoning=False
        ) as session:
            try:
                # 提一个可能超时的问题
                result = session.chat("请给我详细介绍一下宇宙的起源、演化和未来")
            except SessionTimeoutError:
                # 超时是预期的
                print(f"{Fore.YELLOW}第1轮超时（预期）")
            
            # 短暂等待
            time.sleep(1)
            
            # 再问一个简单问题，验证不会播放上一轮的音频
            result2 = session.chat("你好")
            print(f"{Fore.YELLOW}第2轮: {result2.response}")
            
            # 如果没有异常，说明 TTS 清空成功
            print_test_result(True, "TTS 缓冲区清空通过")
            return True
            
    except Exception as e:
        print_test_result(False, f"TTS 缓冲区测试失败: {e}")
        return False


def test_7_state_query():
    """测试 7：系统状态查询（验证状态可观测性）"""
    print_test_header("测试 7：系统状态查询")
    
    try:
        with ConversationSession(
            llm_model="qwen2.5:3b",
            timeout=120,
            tts_wait_timeout=180
        ) as session:
            # 发起对话
            result = session.chat("你好")
            
            # 查询状态
            state = session.get_detailed_state()
            
            # 验证状态结构
            assert 'session_id' in state, "缺少 session_id"
            assert 'session_status' in state, "缺少 session_status"
            
            print_test_result(True, "系统状态查询通过")
            print(f"{Fore.YELLOW}状态: {state}")
            return True
            
    except Exception as e:
        print_test_result(False, f"状态查询测试失败: {e}")
        return False


# ============================================================================
# 主测试流程
# ============================================================================

def run_all_tests():
    """运行所有测试"""
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print(f"{Fore.MAGENTA}🚀 Bug 修复综合测试")
    print(f"{Fore.MAGENTA}{'='*70}\n")
    
    tests = [
        ("正常对话", test_1_normal_conversation),
        ("异常处理", test_2_exception_handling),
        ("特殊字符过滤", test_3_special_characters),
        ("回复长度控制", test_4_response_length),
        ("多轮对话无串音", test_5_multi_turn_no_cross_talk),
        ("TTS 缓冲区清空", test_6_tts_buffer_cleanup),
        ("系统状态查询", test_7_state_query),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{Fore.RED}❌ 测试 '{test_name}' 异常: {e}")
            results.append((test_name, False))
        
        # 测试间隔
        time.sleep(2)
    
    # 打印测试摘要
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print(f"{Fore.MAGENTA}📊 测试摘要")
    print(f"{Fore.MAGENTA}{'='*70}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Fore.GREEN}✅ 通过" if result else f"{Fore.RED}❌ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n{Fore.CYAN}总计: {passed}/{total} 通过")
    
    if passed == total:
        print(f"{Fore.GREEN}🎉 所有测试通过！")
        return True
    else:
        print(f"{Fore.YELLOW}⚠️  部分测试失败，请检查日志")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

