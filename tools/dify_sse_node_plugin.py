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
        
        event_type = "message"  # SSE规范默认事件类型
        data_lines = []
        event_id = ""
        retry = 0
        all_fields = {}  # 保存所有字段，包括自定义字段
        
        # 解析所有事件行
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
                else:
                    # 保存其他自定义字段
                    if field in all_fields:
                        # 如果字段重复，转换为列表
                        if not isinstance(all_fields[field], list):
                            all_fields[field] = [all_fields[field]]
                        all_fields[field].append(value)
                    else:
                        all_fields[field] = value
        
        # 构建完整的事件数据
        # 即使没有data字段，也要创建事件对象（SSE规范允许只有event类型的事件）
        if data_lines:
            data = '\n'.join(data_lines)
        else:
            # 如果没有data字段，但有其他字段，也创建事件
            if event_type != "message" or event_id or retry or all_fields:
                data = ""  # 空数据
            else:
                return None  # 完全空的事件，不创建
        
        # 如果有自定义字段，将它们添加到data中（作为JSON格式）
        if all_fields:
            try:
                import json as json_lib
                if data:
                    # 如果已有data，尝试解析为JSON并合并自定义字段
                    try:
                        if data.strip().startswith('{') and data.strip().endswith('}'):
                            parsed_data = json_lib.loads(data)
                            if isinstance(parsed_data, dict):
                                parsed_data['_custom_fields'] = all_fields
                                data = json_lib.dumps(parsed_data, ensure_ascii=False, separators=(',', ':'))
                            else:
                                # data不是JSON对象，创建新的包装对象
                                wrapped_data = {
                                    'original_data': data,
                                    '_custom_fields': all_fields
                                }
                                data = json_lib.dumps(wrapped_data, ensure_ascii=False, separators=(',', ':'))
                        else:
                            # data不是JSON格式，创建包装对象
                            wrapped_data = {
                                'original_data': data,
                                '_custom_fields': all_fields
                            }
                            data = json_lib.dumps(wrapped_data, ensure_ascii=False, separators=(',', ':'))
                    except json_lib.JSONDecodeError:
                        # JSON解析失败，创建包装对象
                        wrapped_data = {
                            'original_data': data,
                            '_custom_fields': all_fields
                        }
                        data = json_lib.dumps(wrapped_data, ensure_ascii=False, separators=(',', ':'))
                else:
                    # 没有data，只有自定义字段
                    data = json_lib.dumps(all_fields, ensure_ascii=False, separators=(',', ':'))
            except Exception as e:
                print(f"[自定义字段处理] 处理自定义字段时出错: {e}")
                # 出错时保持原始data不变
                pass
        
        # 继续原有的Unicode解码逻辑
        if data:
            
            # 处理Unicode转义序列，将其解码为可读的中文
            try:
                # 尝试解析data中的JSON，如果包含Unicode转义序列则解码
                import json as json_lib
                
                # 检查data是否是JSON格式
                if data.strip().startswith('{') and data.strip().endswith('}'):
                    try:
                        # 解析JSON，这会自动处理Unicode转义序列
                        parsed_data = json_lib.loads(data)
                        
                        # 重新序列化，使用ensure_ascii=False确保中文字符正常显示
                        decoded_data = json_lib.dumps(parsed_data, ensure_ascii=False, separators=(',', ':'))
                        
                        print(f"[Unicode解码] 原始data: {data[:100]}...")
                        print(f"[Unicode解码] 解码后data: {decoded_data[:100]}...")
                        
                        data = decoded_data
                        
                    except json_lib.JSONDecodeError:
                        # 如果不是有效的JSON，尝试直接解码Unicode转义序列
                        try:
                            # 使用encode().decode('unicode_escape')处理Unicode转义
                            if '\\u' in data:
                                decoded_data = data.encode().decode('unicode_escape')
                                print(f"[Unicode解码] 直接解码 - 原始: {data[:100]}...")
                                print(f"[Unicode解码] 直接解码 - 结果: {decoded_data[:100]}...")
                                data = decoded_data
                        except Exception as decode_error:
                            print(f"[Unicode解码] 直接解码失败: {decode_error}")
                            # 解码失败，保持原始数据
                            pass
                            
                elif '\\u' in data:
                    # 对于非JSON格式但包含Unicode转义的数据，尝试直接解码
                    try:
                        decoded_data = data.encode().decode('unicode_escape')
                        print(f"[Unicode解码] 非JSON解码 - 原始: {data[:100]}...")
                        print(f"[Unicode解码] 非JSON解码 - 结果: {decoded_data[:100]}...")
                        data = decoded_data
                    except Exception as decode_error:
                        print(f"[Unicode解码] 非JSON解码失败: {decode_error}")
                        # 解码失败，保持原始数据
                        pass
                        
            except Exception as e:
                print(f"[Unicode解码] 处理过程中出错: {e}")
                # 出错时保持原始数据
                pass
            
            return SSEEvent(event_type, data, event_id, retry)
        
        return None
    
    def connect_and_listen(self, max_events: int = 100, max_duration: int = 300) -> Generator[SSEEvent, None, None]:
        """连接SSE服务器并监听事件"""
        start_time = time.time()
        event_count = 0
        
        # 添加调试信息的事件
        debug_event = SSEEvent("debug", json.dumps({
            "message": "开始构建SSE请求",
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "body_type": self.body_type,
            "body_length": len(self.body) if self.body else 0,
            "timeout": self.timeout
        }, ensure_ascii=False, separators=(',', ':')), "debug-start")
        yield debug_event
        
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
                        headers["Content-Type"] = "application/json"
                        # 对于JSON，先清理无效字符，再解析并重新序列化，确保格式正确
                        try:
                            import json as json_lib
                            
                            # 控制台日志：JSON处理开始
                            print(f"[JSON处理] 开始处理JSON body，长度: {len(self.body)}")
                            print(f"[JSON处理] 原始body前100字符: {repr(self.body[:100])}")
                            
                            # 第一步：清理JSON字符串中的无效字符
                            cleaned_body = self.body
                            
                            # 清理不间断空格(\xa0)和其他常见的无效字符
                            cleaned_body = cleaned_body.replace('\xa0', ' ')  # 不间断空格替换为普通空格
                            cleaned_body = cleaned_body.replace('\u00a0', ' ')  # Unicode不间断空格
                            cleaned_body = cleaned_body.replace('\u2000', ' ')  # En Quad
                            cleaned_body = cleaned_body.replace('\u2001', ' ')  # Em Quad
                            cleaned_body = cleaned_body.replace('\u2002', ' ')  # En Space
                            cleaned_body = cleaned_body.replace('\u2003', ' ')  # Em Space
                            cleaned_body = cleaned_body.replace('\u2004', ' ')  # Three-Per-Em Space
                            cleaned_body = cleaned_body.replace('\u2005', ' ')  # Four-Per-Em Space
                            cleaned_body = cleaned_body.replace('\u2006', ' ')  # Six-Per-Em Space
                            cleaned_body = cleaned_body.replace('\u2007', ' ')  # Figure Space
                            cleaned_body = cleaned_body.replace('\u2008', ' ')  # Punctuation Space
                            cleaned_body = cleaned_body.replace('\u2009', ' ')  # Thin Space
                            cleaned_body = cleaned_body.replace('\u200a', ' ')  # Hair Space
                            cleaned_body = cleaned_body.replace('\u202f', ' ')  # Narrow No-Break Space
                            cleaned_body = cleaned_body.replace('\u205f', ' ')  # Medium Mathematical Space
                            cleaned_body = cleaned_body.replace('\u3000', ' ')  # Ideographic Space
                            
                            print(f"[JSON处理] 清理后body长度: {len(cleaned_body)}")
                            print(f"[JSON处理] 清理后body前100字符: {repr(cleaned_body[:100])}")
                            
                            # 第二步：尝试解析JSON，确保格式正确
                            parsed_json = json_lib.loads(cleaned_body)
                            print(f"[JSON处理] JSON解析成功，类型: {type(parsed_json)}")
                            
                            # 第三步：重新序列化，确保格式标准化
                            normalized_json = json_lib.dumps(parsed_json, ensure_ascii=False, separators=(',', ':'))
                            print(f"[JSON处理] JSON重新序列化成功，新长度: {len(normalized_json)}")
                            print(f"[JSON处理] 序列化后前100字符: {repr(normalized_json[:100])}")
                            
                            # 第四步：使用标准化后的JSON
                            stream_kwargs["content"] = normalized_json.encode('utf-8')
                            print(f"[JSON处理] 编码为UTF-8成功，最终长度: {len(stream_kwargs['content'])}")
                            
                        except json_lib.JSONDecodeError as e:
                            # JSON格式错误，输出详细错误信息
                            error_msg = f"Invalid JSON format in body: {e}"
                            print(f"[JSON错误] {error_msg}")
                            print(f"[JSON错误] 原始body错误位置附近: {repr(self.body[max(0, e.pos-20):e.pos+20])}")
                            print(f"[JSON错误] 清理后body错误位置附近: {repr(cleaned_body[max(0, e.pos-20):e.pos+20])}")
                            raise ValueError(error_msg)
                        except Exception as e:
                            # 其他错误
                            error_msg = f"Unexpected error in JSON processing: {e}"
                            print(f"[JSON错误] {error_msg}")
                            raise ValueError(error_msg)
                    elif self.body_type == "form":
                        if "Content-Type" not in headers:
                            headers["Content-Type"] = "application/x-www-form-urlencoded"
                        stream_kwargs["content"] = self.body.encode('utf-8')
                    elif self.body_type == "xml":
                        if "Content-Type" not in headers:
                            headers["Content-Type"] = "application/xml"
                        stream_kwargs["content"] = self.body.encode('utf-8')
                    else:  # text
                        if "Content-Type" not in headers:
                            headers["Content-Type"] = "text/plain"
                        stream_kwargs["content"] = self.body.encode('utf-8')
            
            # 从stream_kwargs中提取参数，避免重复传递
            method = stream_kwargs.pop("method")
            url = stream_kwargs.pop("url")
            
            # 添加请求构建完成的调试信息
            debug_request_event = SSEEvent("debug", json.dumps({
                "message": "请求参数构建完成",
                "final_method": method,
                "final_url": url,
                "final_headers": dict(stream_kwargs.get("headers", {})),
                "has_content": "content" in stream_kwargs,
                "content_length": len(stream_kwargs.get("content", b"")) if "content" in stream_kwargs else 0,
                "stream_kwargs_keys": list(stream_kwargs.keys()),
                "body_preview": self.body[:500] if self.body else None,  # 增加预览长度
                "body_full_length": len(self.body) if self.body else 0,
                "body_type": self.body_type
            }, ensure_ascii=False, separators=(',', ':')), "debug-request")
            yield debug_request_event
                
            with httpx.stream(method, url, **stream_kwargs) as response:
                # 添加响应状态调试信息
                debug_response_event = SSEEvent("debug", json.dumps({
                    "message": "收到HTTP响应",
                    "status_code": response.status_code,
                    "response_headers": dict(response.headers),
                    "content_type": response.headers.get("content-type", ""),
                    "is_sse_response": "text/event-stream" in response.headers.get("content-type", "")
                }, ensure_ascii=False, separators=(',', ':')), "debug-response")
                yield debug_response_event
                
                if response.status_code != 200:
                    # 收集详细的错误信息
                    response_headers = dict(response.headers)
                    response_text = ""
                    
                    # 尝试读取响应内容
                    try:
                        # 首先尝试直接读取响应文本
                        response_text = response.text
                        
                        # 如果直接读取失败，尝试其他方法
                        if not response_text:
                            try:
                                # 尝试读取原始字节并解码
                                content_bytes = response.content
                                if content_bytes:
                                    response_text = content_bytes.decode('utf-8', errors='ignore')
                                else:
                                    response_text = "响应内容为空"
                            except Exception as decode_error:
                                response_text = f"解码响应内容失败: {str(decode_error)}"
                                
                    except Exception as e:
                        # 如果所有方法都失败，尝试从流中读取
                        try:
                            content_bytes = b""
                            for chunk in response.iter_bytes(chunk_size=1024):
                                content_bytes += chunk
                                if len(content_bytes) > 4096:  # 增加读取限制
                                    break
                            if content_bytes:
                                response_text = content_bytes.decode('utf-8', errors='ignore')
                            else:
                                response_text = "无法从响应流中读取内容"
                        except Exception as stream_error:
                            response_text = f"读取响应流时出错: {str(stream_error)}, 原始错误: {str(e)}"
                    
                    error_details = {
                        "status_code": response.status_code,
                        "response_headers": response_headers,
                        "response_text": response_text[:2000] if response_text else "空响应",  # 增加长度限制
                        "request_url": url,
                        "request_method": method,
                        "request_headers": dict(stream_kwargs.get("headers", {})),
                        "request_body": self.body[:1000] if self.body else None  # 增加长度限制
                    }
                    raise Exception(f"SSE连接失败，详细信息: {json.dumps(error_details, ensure_ascii=False, indent=2)}")
                
                event_lines = []
                line_count = 0
                
                for line in response.iter_lines():
                    # 检查超时和事件数量限制
                    if time.time() - start_time > max_duration:
                        print(f"[SSE监听] 达到最大时长限制 {max_duration}秒，停止监听")
                        break
                    if event_count >= max_events:
                        print(f"[SSE监听] 达到最大事件数限制 {max_events}，停止监听")
                        break
                    
                    line_count += 1
                    line = line.strip()
                    
                    # 调试：输出原始行数据
                    if line:
                        print(f"[SSE原始行#{line_count}] {repr(line)}")
                    else:
                        print(f"[SSE原始行#{line_count}] <空行，事件分隔符>")
                    
                    # 空行表示事件结束
                    if not line:
                        if event_lines:
                            print(f"[SSE事件解析] 开始解析事件，包含{len(event_lines)}行数据:")
                            for i, event_line in enumerate(event_lines, 1):
                                print(f"  行{i}: {repr(event_line)}")
                            
                            event = self.parse_sse_event(event_lines)
                            if event:
                                self.events.append(event)
                                event_count += 1
                                print(f"[SSE事件解析] 成功解析事件#{event_count}: 类型={event.event_type}, ID={event.event_id}")
                                yield event
                            else:
                                print(f"[SSE事件解析] 解析结果为空，跳过此事件")
                            event_lines = []
                        else:
                            print(f"[SSE事件解析] 空行但无待解析数据，跳过")
                    else:
                        event_lines.append(line)
                
                # 处理最后一个事件（如果没有以空行结尾）
                if event_lines:
                    print(f"[SSE事件解析] 处理最后一个事件，包含{len(event_lines)}行数据:")
                    for i, event_line in enumerate(event_lines, 1):
                        print(f"  行{i}: {repr(event_line)}")
                    
                    event = self.parse_sse_event(event_lines)
                    if event:
                        self.events.append(event)
                        event_count += 1
                        print(f"[SSE事件解析] 成功解析最后一个事件#{event_count}: 类型={event.event_type}, ID={event.event_id}")
                        yield event
                    else:
                        print(f"[SSE事件解析] 最后一个事件解析结果为空，跳过")
                
                print(f"[SSE监听] 监听结束，共处理{line_count}行原始数据，解析出{event_count}个有效事件")
                        
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
                # 清理字符串中的特殊字符（如\xa0不间断空格）
                cleaned_str = headers_str.replace('\xa0', ' ').replace('\u00a0', ' ')
                # 移除其他可能的Unicode空白字符
                cleaned_str = ''.join(char if ord(char) < 128 or not char.isspace() else ' ' for char in cleaned_str)
                cleaned_str = cleaned_str.strip()
                
                print(f"[Headers清理] 原始: {repr(headers_str)}")
                print(f"[Headers清理] 清理后: {repr(cleaned_str)}")
                
                headers = json.loads(cleaned_str)
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
                # 清理字符串中的特殊字符（如\xa0不间断空格）
                cleaned_str = params_str.replace('\xa0', ' ').replace('\u00a0', ' ')
                # 移除其他可能的Unicode空白字符
                cleaned_str = ''.join(char if ord(char) < 128 or not char.isspace() else ' ' for char in cleaned_str)
                cleaned_str = cleaned_str.strip()
                
                print(f"[Query清理] 原始: {repr(params_str)}")
                print(f"[Query清理] 清理后: {repr(cleaned_str)}")
                
                params = json.loads(cleaned_str)
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
            # 控制台日志：输出入参
            print("=" * 80)
            print("[工具调用] DifySseNodePluginTool._invoke 开始执行")
            print(f"[入参] 原始参数: {json.dumps(tool_parameters, ensure_ascii=False, indent=2)}")
            
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
            
            # 控制台日志：输出解析后的参数
            print(f"[参数解析] URL: {url}")
            print(f"[参数解析] Method: {method}")
            print(f"[参数解析] Headers字符串: {headers_str}")
            print(f"[参数解析] Query参数字符串: {query_params_str}")
            print(f"[参数解析] Body长度: {len(body) if body else 0}")
            print(f"[参数解析] Body类型: {body_type}")
            print(f"[参数解析] Body前200字符: {repr(body[:200]) if body else 'None'}")
            print(f"[参数解析] Timeout: {timeout}, Max Events: {max_events}, Max Duration: {max_duration}")
            
            # 验证必需参数
            print(f"[URL验证] 开始验证URL: {url}")
            self._validate_url(url)
            print(f"[URL验证] URL验证通过")
            
            # 解析headers和查询参数
            print(f"[Headers解析] 开始解析Headers: {headers_str}")
            headers = self._parse_headers(headers_str)
            print(f"[Headers解析] Headers解析结果: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            
            print(f"[Query解析] 开始解析Query参数: {query_params_str}")
            query_params = self._parse_query_params(query_params_str)
            print(f"[Query解析] Query参数解析结果: {json.dumps(query_params, ensure_ascii=False, indent=2)}")
            
            # 构建完整URL
            print(f"[URL构建] 开始构建完整URL")
            full_url = self._build_url_with_params(url, query_params)
            print(f"[URL构建] 完整URL: {full_url}")
            
            # 调试信息只在控制台输出，不作为工具结果返回
            print(f"[调试信息] 解析后的参数:")
            print(f"  - URL: {full_url}")
            print(f"  - Method: {method}")
            print(f"  - Headers: {json.dumps(headers, ensure_ascii=False)}")
            print(f"  - Body长度: {len(body) if body else 0}")
            print(f"  - 超时设置: {timeout}秒, 最大事件: {max_events}, 最大时长: {max_duration}秒")
            
            # 尝试连接SSE服务器
            print(f"[SSE连接] 开始尝试连接SSE服务器")
            connection_successful = False
            last_error = None
            retry_attempts = 3  # 固定重试次数
            
            for attempt in range(retry_attempts + 1):
                try:
                    print(f"[SSE连接] 第{attempt + 1}次尝试连接")
                    # 创建SSE客户端
                    sse_client = SSEClient(full_url, method, headers, body, body_type, timeout)
                    print(f"[SSE连接] SSE客户端创建成功")
                    
                    # 连接并监听事件
                    print(f"[SSE连接] 开始连接并监听事件")
                    start_time = time.time()
                    event_count = 0
                    for event in sse_client.connect_and_listen(max_events, max_duration):
                        event_count += 1
                        event_info = {
                            "event_number": event_count,
                            "event_type": event.event_type,
                            "data": event.data,
                            "event_id": event.event_id,
                            "timestamp": event.timestamp,
                            "retry": event.retry
                        }
                        yield self.create_json_message(event_info)
                    connection_successful = True
                    end_time = time.time()
                    duration = end_time - start_time
                    final_result = {
                        "status": "completed",
                        "total_events": event_count,
                        "connection_duration": round(duration, 2),
                        "summary": f"SSE连接成功，接收到{event_count}个事件，耗时{duration:.2f}秒"
                    }
                    summary_message = self.create_json_message(final_result)
                    yield summary_message
                    break
                    
                except Exception as e:
                    last_error = str(e)
                    print(f"[SSE错误] 第{attempt + 1}次尝试失败: {last_error}")
                    if attempt < retry_attempts:
                        print(f"[SSE重试] 等待2秒后进行第{attempt + 2}次重试...")
                        time.sleep(2)  # 等待2秒后重试
                    else:
                        print(f"[SSE错误] 所有重试都失败了")
                        break
            
            # 如果所有重试都失败了
            if not connection_successful:
                print(f"[SSE错误] 连接最终失败，错误: {last_error}")
                final_result = {
                    "status": "failed",
                    "total_events": 0,
                    "connection_duration": 0,
                    "events": [],
                    "summary": f"SSE连接失败，重试{retry_attempts + 1}次后仍无法连接",
                    "error": last_error or "未知错误"
                }
                error_message = self.create_json_message(final_result)
                print(f"[出参] 输出错误结果: {error_message}")
                yield error_message
            
            print(f"[工具调用] DifySseNodePluginTool._invoke 执行完成")
            print("=" * 80)
                
        except Exception as e:
            # 处理参数验证或其他错误
            error_msg = f"参数错误或系统错误: {str(e)}"
            print(f"[系统错误] {error_msg}")
            final_result = {
                "status": "error",
                "total_events": 0,
                "connection_duration": 0,
                "events": [],
                "summary": "工具执行过程中发生系统错误",
                "error": error_msg
            }
            error_message = self.create_json_message(final_result)
            print(f"[出参] 输出系统错误结果: {error_message}")
            yield error_message
            print(f"[工具调用] DifySseNodePluginTool._invoke 异常结束")
            print("=" * 80)
