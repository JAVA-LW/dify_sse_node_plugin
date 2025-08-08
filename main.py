import logging
from dify_plugin import Plugin, DifyPluginEnv

# 配置日志级别为DEBUG，显示详细调试信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 如果你只想看到特定模块的DEBUG日志，可以使用以下配置：
# logging.basicConfig(level=logging.INFO)  # 全局设置为INFO
# logging.getLogger('tools.dify_chatflow_sse').setLevel(logging.DEBUG)  # 只对SSE工具启用DEBUG

plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=120))

if __name__ == '__main__':
    plugin.run()
