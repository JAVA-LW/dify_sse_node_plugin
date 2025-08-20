# Dify SSE 请求工具插件

**orgtinal:** tdcktz
**Author:** 老文
**Type:** tool

## 📖 描述

这是一个为Dify工作流设计的Server-Sent Events (SSE) 请求工具插件。它允许你在Dify工作流中建立长连接，接收服务器实时推送的事件流数据，并提供流式输出和最终汇总结果。

### 当前请求工具分类：

当前支持两种sse请求方式：

1. 通用SSE 请求，会返回所有事件
2. Dify Chatflow SSE 请求，仅仅会返回关键事件也就是最后节点大模型的直接回复内容，那些切块事件不会都返回。


## 背景说明：
在进行工作流时候，需要调用一些接口，但是这些接口返回的是一个流，需要实时接收数据，所以需要一个插件来支持。


## ✨ 主要功能

- 🔗 **长连接支持**: 建立并维护SSE长连接
- 📡 **实时数据流**: 接收服务器推送的实时事件数据
- 🔐 **多种认证方式**: 支持Bearer Token、API Key等认证方式
- ⚙️ **灵活配置**: 自定义Headers、查询参数、超时设置等
- 🔄 **自动重连**: 连接失败时自动重试机制
- 📊 **流式输出**: 实时输出接收到的事件，同时提供最终汇总
- 🛡️ **错误处理**: 完善的错误处理和状态监控

## 🚀 快速开始

### 基本用法

在Dify工作流中添加SSE请求工具，配置以下参数：

```yaml
URL: https://your-sse-server.com/stream
认证类型: none
超时时间: 30
最大事件数: 100
最大持续时间: 300
```

### 带认证的请求

```yaml
URL: https://api.example.com/sse/events
认证类型: bearer
认证令牌: your-bearer-token
请求头: |
  Content-Type: application/json
  X-Custom-Header: custom-value
查询参数: |
  stream: true
  topic: updates
```

## 📋 参数说明

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `url` | string | ✅ | - | SSE服务器端点URL |
| `headers` | string | ❌ | - | 自定义HTTP头，每行一个，格式：`key: value` |
| `query_params` | string | ❌ | - | URL查询参数，每行一个，格式：`key: value` |
| `auth_type` | select | ❌ | none | 认证类型：none/bearer/api_key |
| `auth_token` | string | ❌ | - | 认证令牌或API密钥 |
| `auth_header` | string | ❌ | Authorization | API密钥认证的头名称 |
| `timeout` | number | ❌ | 30 | 连接超时时间（秒） |
| `max_events` | number | ❌ | 100 | 最大接收事件数 |
| `max_duration` | number | ❌ | 300 | 最大连接持续时间（秒） |
| `retry_attempts` | number | ❌ | 3 | 连接失败重试次数 |

## 📤 输出格式

### 实时事件输出

```json
{
  "type": "event",
  "event_number": 1,
  "event_type": "message",
  "data": "实时接收的数据",
  "event_id": "event-123",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 最终汇总输出

```json
{
  "type": "summary",
  "status": "completed",
  "total_events": 50,
  "connection_duration": 25.5,
  "events": [...],
  "summary": "SSE连接成功，接收到50个事件，耗时25.5秒",
  "timestamp": "2024-01-01T12:00:25Z"
}
```

### 错误输出

```json
{
  "type": "error",
  "status": "failed",
  "error": "连接超时",
  "timestamp": "2024-01-01T12:00:30Z"
}
```

## 🔧 技术实现

### 核心特性

- **SSE协议支持**: 完整实现SSE协议规范
- **事件解析**: 支持`data:`、`event:`、`id:`、`retry:`字段
- **流式处理**: 使用httpx的stream模式处理长连接
- **异步支持**: 支持异步事件处理和超时控制

### 依赖库

- `httpx>=0.25.0`: HTTP客户端，支持流式请求
- `dify_plugin>=0.2.0`: Dify插件框架

## 📝 使用示例

### 示例1：监听ChatGPT流式响应

```yaml
URL: https://api.openai.com/v1/chat/completions
认证类型: bearer
认证令牌: sk-your-openai-api-key
请求头: |
  Content-Type: application/json
查询参数: |
  stream: true
  model: gpt-3.5-turbo
```

### 示例2：监听实时日志流

```yaml
URL: https://your-log-server.com/logs/stream
认证类型: api_key
认证令牌: your-api-key
认证头名称: X-API-Key
查询参数: |
  level: info
  service: web-app
最大事件数: 1000
最大持续时间: 600
```


## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个插件！

## 📄 许可证

MIT License



