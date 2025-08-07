#!/usr/bin/env python3
"""
SSE插件测试示例

这个示例展示了如何使用Dify SSE请求工具插件
"""

import asyncio
import json
from tools.dify_sse_node_plugin import DifySseNodePluginTool


def test_basic_sse_request():
    """测试基本的SSE请求"""
    tool = DifySseNodePluginTool()
    
    # 测试参数
    test_params = {
        'url': 'https://httpbin.org/stream/10',  # 测试SSE端点
        'headers': 'Accept: text/event-stream\nUser-Agent: Dify-SSE-Plugin/1.0',
        'query_params': 'delay: 1\ncount: 5',
        'auth_type': 'none',
        'timeout': 30,
        'max_events': 10,
        'max_duration': 60,
        'retry_attempts': 2
    }
    
    print("开始SSE请求测试...")
    print(f"URL: {test_params['url']}")
    print("-" * 50)
    
    # 执行SSE请求
    for message in tool._invoke(test_params):
        result = json.loads(message.message)
        
        if result.get('type') == 'connection_start':
            print(f"🔗 连接开始: {result['url']}")
            print(f"   超时时间: {result['timeout']}秒")
            print(f"   最大事件数: {result['max_events']}")
            
        elif result.get('type') == 'event':
            print(f"📨 事件 #{result['event_number']}: {result['event_type']}")
            print(f"   数据: {result['data'][:100]}...")  # 只显示前100个字符
            print(f"   时间: {result['timestamp']}")
            
        elif result.get('type') == 'retry':
            print(f"🔄 重试 #{result['attempt']}: {result['error']}")
            
        elif result.get('type') == 'summary':
            print(f"✅ 完成: {result['summary']}")
            print(f"   总事件数: {result['total_events']}")
            print(f"   连接时长: {result['connection_duration']}秒")
            
        elif result.get('type') == 'error':
            print(f"❌ 错误: {result['error']}")
            
        print()


def test_authenticated_sse_request():
    """测试带认证的SSE请求"""
    tool = DifySseNodePluginTool()
    
    # 带认证的测试参数
    test_params = {
        'url': 'https://api.example.com/sse/stream',
        'headers': 'Content-Type: application/json',
        'auth_type': 'bearer',
        'auth_token': 'your-test-token-here',
        'timeout': 30,
        'max_events': 50,
        'max_duration': 120,
        'retry_attempts': 3
    }
    
    print("开始认证SSE请求测试...")
    print(f"URL: {test_params['url']}")
    print(f"认证类型: {test_params['auth_type']}")
    print("-" * 50)
    
    # 执行SSE请求
    for message in tool._invoke(test_params):
        result = json.loads(message.message)
        print(f"[{result.get('type', 'unknown')}] {result}")


if __name__ == "__main__":
    print("Dify SSE插件测试")
    print("=" * 60)
    
    # 运行基本测试
    test_basic_sse_request()
    
    print("\n" + "=" * 60)
    print("测试完成")
    
    # 如果需要测试认证功能，取消下面的注释
    # print("\n" + "=" * 60)
    # test_authenticated_sse_request()