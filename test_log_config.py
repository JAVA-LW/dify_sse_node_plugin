#!/usr/bin/env python3
"""
测试日志级别配置功能
"""
import logging
from provider.dify_sse_node_plugin import DifySseNodePluginProvider

def test_log_levels():
    """测试不同日志级别的配置"""
    provider = DifySseNodePluginProvider()
    
    # 测试不同的日志级别
    test_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    
    for level in test_levels:
        print(f"\n=== 测试日志级别: {level} ===")
        
        # 模拟凭据配置
        credentials = {'log_level': level}
        
        try:
            # 验证凭据（这会设置日志级别）
            provider._validate_credentials(credentials)
            
            # 测试日志输出
            logger = logging.getLogger('test_logger')
            logger.debug(f"DEBUG 级别日志 - 当前设置: {level}")
            logger.info(f"INFO 级别日志 - 当前设置: {level}")
            logger.warning(f"WARNING 级别日志 - 当前设置: {level}")
            logger.error(f"ERROR 级别日志 - 当前设置: {level}")
            
        except Exception as e:
            print(f"配置日志级别 {level} 时出错: {e}")

def test_provider_validation():
    """测试provider凭据验证"""
    print("\n=== 测试Provider凭据验证 ===")
    
    provider = DifySseNodePluginProvider()
    
    # 测试不同日志级别的凭据验证
    test_credentials = [
        {'log_level': 'DEBUG'},
        {'log_level': 'INFO'},
        {'log_level': 'WARNING'},
        {'log_level': 'ERROR'},
        {}  # 空凭据，应该使用默认值
    ]
    
    for creds in test_credentials:
        try:
            print(f"测试凭据: {creds}")
            provider._validate_credentials(creds)
            print("✓ 凭据验证成功")
        except Exception as e:
            print(f"✗ 凭据验证失败: {e}")

if __name__ == '__main__':
    print("开始测试日志级别配置功能...")
    test_log_levels()
    test_provider_validation()
    print("\n测试完成！")