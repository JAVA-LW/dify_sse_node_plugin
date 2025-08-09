import logging
from dify_plugin import Plugin, DifyPluginEnv

# 日志级别现在通过插件配置管理，在provider中设置
# 默认设置一个基础的日志配置，会被provider覆盖
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=120))

if __name__ == '__main__':
    plugin.run()
