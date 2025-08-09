import logging
from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class DifySseNodePluginProvider(ToolProvider):
    
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """
        SSE Request Tool doesn't require specific credentials validation
        as authentication is handled per-request basis through tool parameters.
        This method validates that the provider is properly configured and sets up logging.
        """
        try:
            # SSE工具不需要全局凭据，认证在每个请求中单独处理
            # 这里只需要确保provider正确配置即可
            
            # 配置日志级别
            log_level = credentials.get('log_level', 'INFO')
            self._setup_logging(log_level)
            
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
    
    def _setup_logging(self, log_level: str) -> None:
        """
        设置日志级别
        """
        # 将字符串转换为logging级别
        level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        
        level = level_mapping.get(log_level.upper(), logging.INFO)
        
        # 配置根日志记录器
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True  # 强制重新配置，覆盖之前的配置
        )
        
        # 记录日志级别设置
        logger = logging.getLogger(__name__)
        logger.info(f"日志级别已设置为: {log_level}")

    #########################################################################################
    # If OAuth is supported, uncomment the following functions.
    # Warning: please make sure that the sdk version is 0.4.2 or higher.
    #########################################################################################
    # def _oauth_get_authorization_url(self, redirect_uri: str, system_credentials: Mapping[str, Any]) -> str:
    #     """
    #     Generate the authorization URL for dify_sse_node_plugin OAuth.
    #     """
    #     try:
    #         """
    #         IMPLEMENT YOUR AUTHORIZATION URL GENERATION HERE
    #         """
    #     except Exception as e:
    #         raise ToolProviderOAuthError(str(e))
    #     return ""
        
    # def _oauth_get_credentials(
    #     self, redirect_uri: str, system_credentials: Mapping[str, Any], request: Request
    # ) -> Mapping[str, Any]:
    #     """
    #     Exchange code for access_token.
    #     """
    #     try:
    #         """
    #         IMPLEMENT YOUR CREDENTIALS EXCHANGE HERE
    #         """
    #     except Exception as e:
    #         raise ToolProviderOAuthError(str(e))
    #     return dict()

    # def _oauth_refresh_credentials(
    #     self, redirect_uri: str, system_credentials: Mapping[str, Any], credentials: Mapping[str, Any]
    # ) -> OAuthCredentials:
    #     """
    #     Refresh the credentials
    #     """
    #     return OAuthCredentials(credentials=credentials, expires_at=-1)
