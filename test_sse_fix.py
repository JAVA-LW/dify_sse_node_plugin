#!/usr/bin/env python3
"""
测试 SSE 工具修复后的功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.dify_sse_node_plugin import DifySseNodePluginTool

def test_sse_tool():
    """测试 SSE 工具"""
    tool = DifySseNodePluginTool()
    
    # 测试参数（与用户提供的相同）
    test_params = {
        "url": " `https://dify.tdcktz.com/workflows/run` ",  # 包含空格和反引号
        "method": "POST",
        "headers": '{"Content-Type": "application/json", "Accept": "text/event-stream","Authorization": "Bearer app-IWdTN4TsCpJdXzx4PFQvJszK"}',
        "query_params": "{}",
        "body": '''{\n    "inputs": {\n        "projectName":"立安智能立体停车库",\n        "name":"立体停车库",\n        "industry":"大消费/大数据/新能源/新材料/智能制造",\n        "customer":"大型停车场、商城、医院、机场、CBD",\n        "applicationScenarios":"1，通过立体化来解决停车场车位不足问题2，用户取车的时候可以自动将车辆起来然后直接开出车位，实现自动停车",\n        "coreTechnology":"无",\n        "mainProducts":"无"\n    },\n    "response_mode": "streaming",\n    "user": "你好"\n}''',
        "body_type": "json",
        "timeout": 30,
        "max_events": 100,
        "max_duration": 300
    }
    
    print("🚀 开始测试 SSE 工具...")
    print(f"📍 URL: {test_params['url']}")
    print(f"🔧 方法: {test_params['method']}")
    print(f"📦 请求体类型: {test_params['body_type']}")
    print("-" * 50)
    
    try:
        # 执行工具
        for message in tool._invoke(test_params):
            if hasattr(message, 'message'):
                import json
                try:
                    data = json.loads(message.message)
                    print(f"📨 {data.get('type', 'unknown')}: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"📨 消息: {message.message}")
            else:
                print(f"📨 消息: {message}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sse_tool()