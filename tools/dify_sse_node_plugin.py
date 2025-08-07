import json
import time
import re
from collections.abc import Generator
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse
import httpx
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class SSEEvent:
    """SSE事件数据结构"""
    def __init__(self, event_type: str = "message", data: str = "", event_id: str = "", retry: int = 0):
        self.event_type = event_type
        self.data = data
        self.event_id = event_id
        self.retry = retry
        self.timestamp = datetime.now().isoformat()


class SSEClient:
    """SSE客户端实现"""
    
    def __init__(self, url: str, method: str = 'GET', headers: Optional[Dict[str, str]] = None, 
                 body: Optional[str] = None, body_type: str = "json", timeout: int = 30):
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.body = body
        self.body_type = body_type
        self.timeout = timeout
        self.events: List[SSEEvent] = []
        self.is_connected = False
        self.start_time = None
        
        # 设置SSE专用headers
        self.headers.update({
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
    
    def parse_sse_line(self, line: str) -> Dict[str, str]:
        """解析SSE数据行"""
        line = line.strip()
        if not line or line.startswith(':'):
            return {}
        
        if ':' in line:
            field, value = line.split(':', 1)
            return {field.strip(): value.strip()}
        else:
            return {line: ''}
    
    def parse_sse_event(self, event_lines: List[str]) -> Optional[SSEEvent]:
        """解析完整的SSE事件"""
        if not event_lines:
            return None
        
        event_type = "message"
        data_lines = []
        event_id = ""
        retry = 0
        
        for line in event_lines:
            parsed = self.parse_sse_line(line)
            for field, value in parsed.items():
                if field == 'event':
                    event_type = value
                elif field == 'data':
                    data_lines.append(value)
                elif field == 'id':
                    event_id = value
                elif field == 'retry':
                    try:
                        retry = int(value)
                    except ValueError:
                        retry = 0
        
        if data_lines:
            data = '\n'.join(data_lines)
            return SSEEvent(event_type, data, event_id, retry)
        
        return None
    
    def connect_and_listen(self, max_events: int = 100, max_duration: int = 300) -> Generator[SSEEvent, None, None]:
        """连接SSE服务器并监听事件"""
        start_time = time.time()
        event_count = 0
        
        try:
            # 根据方法和body参数构建请求
            if self.method == "GET":
                stream_kwargs = {
                    "method": "GET",
                    "url": self.url,
                    "headers": self.headers,
                    "timeout": self.timeout
                }
            else:
                # 根据body_type设置Content-Type和处理body
                headers = self.headers.copy()
                stream_kwargs = {
                    "method": self.method,
                    "url": self.url,
                    "headers": headers,
                    "timeout": self.timeout
                }
                
                if self.body:
                    if self.body_type == "json":
                        if "Content-Type" not in headers:
                            headers["Content-Type"] = "application/json"
                        # 对于JSON，尝试解析并使用json参数
                        try:
                            import json as json_lib
                            json_data = json_lib.loads(self.body)
                            stream_kwargs["json"] = json_data
                        except json_lib.JSONDecodeError:
                            # 如果解析失败，使用data参数
                            stream_kwargs["data"] = self.body
                    elif self.body_type == "form":
                        if "Content-Type" not in headers:
                            headers["Content-Type"] = "application/x-www-form-urlencoded"
                        stream_kwargs["data"] = self.body
                    elif self.body_type == "xml":
                        if "Content-Type" not in headers:
                            headers["Content-Type"] = "application/xml"
                        stream_kwargs["data"] = self.body
                    else:  # text
                        if "Content-Type" not in headers:
                            headers["Content-Type"] = "text/plain"
                        stream_kwargs["data"] = self.body
            
            # 从stream_kwargs中提取参数，避免重复传递
            method = stream_kwargs.pop("method")
            url = stream_kwargs.pop("url")
                
            with httpx.stream(method, url, **stream_kwargs) as response:
                if response.status_code != 200:
                    raise Exception(f"SSE连接失败，状态码: {response.status_code}")
                
                event_lines = []
                
                for line in response.iter_lines():
                    # 检查超时和事件数量限制
                    if time.time() - start_time > max_duration:
                        break
                    if event_count >= max_events:
                        break
                    
                    line = line.strip()
                    
                    # 空行表示事件结束
                    if not line:
                        if event_lines:
                            event = self.parse_sse_event(event_lines)
                            if event:
                                self.events.append(event)
                                event_count += 1
                                yield event
                            event_lines = []
                    else:
                        event_lines.append(line)
                
                # 处理最后一个事件（如果没有以空行结尾）
                if event_lines:
                    event = self.parse_sse_event(event_lines)
                    if event:
                        self.events.append(event)
                        yield event
                        
        except httpx.TimeoutException:
            raise Exception(f"SSE连接超时（{self.timeout}秒）")
        except httpx.RequestError as e:
            raise Exception(f"SSE连接错误: {str(e)}")


class DifySseNodePluginTool(Tool):
    """Dify SSE请求工具"""
    
    def _parse_headers(self, headers_str: str) -> Dict[str, str]:
        """Parse headers from JSON string format to dictionary"""
        headers = {}
        if headers_str:
            try:
                headers = json.loads(headers_str)
                if not isinstance(headers, dict):
                    raise ValueError("Headers must be a JSON object")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format for headers: {e}")
        return headers
    
    def _parse_query_params(self, params_str: str) -> Dict[str, str]:
        """Parse query parameters from JSON string format to dictionary"""
        params = {}
        if params_str:
            try:
                params = json.loads(params_str)
                if not isinstance(params, dict):
                    raise ValueError("Query parameters must be a JSON object")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format for query parameters: {e}")
        return params
    
    def _build_url_with_params(self, url: str, params: Dict[str, str]) -> str:
        """构建带查询参数的URL"""
        if not params:
            return url
        
        parsed_url = urlparse(url)
        query_string = urlencode(params)
        
        if parsed_url.query:
            full_query = f"{parsed_url.query}&{query_string}"
        else:
            full_query = query_string
        
        return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{full_query}"
    
    def _validate_url(self, url: str) -> None:
        """验证URL格式"""
        if not url:
            raise ValueError("URL不能为空")
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL必须以http://或https://开头")
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """执行SSE请求"""
        try:
            # 获取参数
            url = tool_parameters.get('url', '').strip()
            # 去除可能的反引号和额外空格
            url = url.strip('`').strip()
            method = tool_parameters.get('method', 'GET').strip().upper()
            headers_str = tool_parameters.get('headers', '')
            query_params_str = tool_parameters.get('query_params', '')
            body = tool_parameters.get('body', '').strip()
            body_type = tool_parameters.get('body_type', 'json')
            timeout = int(tool_parameters.get('timeout', 30))
            max_events = int(tool_parameters.get('max_events', 100))
            max_duration = int(tool_parameters.get('max_duration', 300))
            
            # 验证必需参数
            self._validate_url(url)
            
            # 解析headers和查询参数
            headers = self._parse_headers(headers_str)
            query_params = self._parse_query_params(query_params_str)
            
            # 构建完整URL
            full_url = self._build_url_with_params(url, query_params)
            
            # 输出连接开始信息
            yield self.create_json_message({
                "type": "connection_start",
                "url": full_url,
                "method": method,
                "headers": {k: v for k, v in headers.items() if k.lower() != 'authorization'},
                "has_body": bool(body) and method in ['POST', 'PUT', 'PATCH'],
                "body_type": body_type if body else None,
                "timeout": timeout,
                "max_events": max_events,
                "max_duration": max_duration,
                "timestamp": datetime.now().isoformat()
            })
            
            # 尝试连接SSE服务器
            connection_successful = False
            last_error = None
            retry_attempts = 3  # 固定重试次数
            
            for attempt in range(retry_attempts + 1):
                try:
                    # 创建SSE客户端
                    sse_client = SSEClient(full_url, method, headers, body, body_type, timeout)
                    
                    # 连接并监听事件
                    start_time = time.time()
                    event_count = 0
                    all_events = []
                    
                    for event in sse_client.connect_and_listen(max_events, max_duration):
                        event_count += 1
                        all_events.append({
                            "event_type": event.event_type,
                            "data": event.data,
                            "event_id": event.event_id,
                            "timestamp": event.timestamp
                        })
                        
                        # 输出实时事件
                        yield self.create_json_message({
                            "type": "event",
                            "event_number": event_count,
                            "event_type": event.event_type,
                            "data": event.data,
                            "event_id": event.event_id,
                            "timestamp": event.timestamp
                        })
                    
                    connection_successful = True
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    # 输出最终汇总结果
                    yield self.create_json_message({
                        "type": "summary",
                        "status": "completed",
                        "total_events": event_count,
                        "connection_duration": round(duration, 2),
                        "events": all_events,
                        "summary": f"SSE连接成功，接收到{event_count}个事件，耗时{duration:.2f}秒",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    break
                    
                except Exception as e:
                    last_error = str(e)
                    if attempt < retry_attempts:
                        yield self.create_json_message({
                            "type": "retry",
                            "attempt": attempt + 1,
                            "error": last_error,
                            "retrying_in": 2,
                            "timestamp": datetime.now().isoformat()
                        })
                        time.sleep(2)  # 等待2秒后重试
                    else:
                        break
            
            # 如果所有重试都失败了
            if not connection_successful:
                yield self.create_json_message({
                    "type": "error",
                    "status": "failed",
                    "error": last_error or "未知错误",
                    "total_attempts": retry_attempts + 1,
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            # 处理参数验证或其他错误
            yield self.create_json_message({
                "type": "error",
                "status": "failed",
                "error": f"参数错误或系统错误: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
