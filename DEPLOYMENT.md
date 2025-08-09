# Dify SSE 请求工具插件 - 部署指南

## 📦 插件安装

### 方法1：从源码安装

1. **克隆或下载插件代码**
   ```bash
   git clone https://github.com/JAVA-LW/dify_sse_node_plugin.git
   cd dify_sse_node_plugin
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **在Dify中安装插件**
   - 将插件文件夹复制到Dify的插件目录
   - 或者通过Dify管理界面上传插件包

### 方法2：通过Dify插件市场安装

1. 打开Dify管理界面
2. 进入插件市场
3. 搜索"SSE Request Tool"
4. 点击安装

## 🚀 快速开始

### 1. 创建工作流

在Dify中创建一个新的工作流，添加SSE请求工具节点。

### 2. 基本配置

```yaml
# 最简配置
URL: https://your-sse-server.com/stream
认证类型: none
超时时间: 30
```

### 3. 高级配置

```yaml
# 完整配置示例
URL: https://api.example.com/sse/events
认证类型: bearer
认证令牌: your-bearer-token
请求头: |
  Content-Type: application/json
  X-Custom-Header: custom-value
查询参数: |
  stream: true
  topic: updates
  format: json
超时时间: 60
最大事件数: 200
最大持续时间: 300
重试次数: 3
```

## 🔧 配置说明

### URL配置
- 必须是有效的HTTP/HTTPS URL
- 支持查询参数
- 示例：`https://api.example.com/sse?stream=true`

### 认证配置

#### 无认证 (none)
```yaml
认证类型: none
```

#### Bearer Token认证
```yaml
认证类型: bearer
认证令牌: your-bearer-token
```

#### API Key认证
```yaml
认证类型: api_key
认证令牌: your-api-key
认证头名称: X-API-Key
```

### 请求头配置
每行一个头部，格式：`key: value`
```
Content-Type: application/json
Accept: text/event-stream
X-Custom-Header: custom-value
```

### 查询参数配置
每行一个参数，格式：`key: value`
```
stream: true
format: json
topic: updates
```

## 📊 输出处理

### 实时事件处理
插件会实时输出接收到的每个SSE事件：
```json
{
  "type": "event",
  "event_number": 1,
  "event_type": "message",
  "data": "实时数据",
  "event_id": "event-123",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 最终汇总
连接结束后输出汇总信息：
```json
{
  "type": "summary",
  "status": "completed",
  "total_events": 50,
  "connection_duration": 25.5,
  "events": [...],
  "summary": "SSE连接成功，接收到50个事件，耗时25.5秒"
}
```

## 🛠️ 故障排除

### 常见问题

#### 1. 连接超时
**问题**：连接建立失败或超时
**解决方案**：
- 检查URL是否正确
- 增加超时时间
- 检查网络连接
- 验证服务器是否支持SSE

#### 2. 认证失败
**问题**：401或403错误
**解决方案**：
- 检查认证令牌是否正确
- 确认认证类型配置
- 验证认证头名称

#### 3. 无事件接收
**问题**：连接成功但没有接收到事件
**解决方案**：
- 检查服务器是否正在发送事件
- 增加最大持续时间
- 检查事件格式是否符合SSE规范

#### 4. 事件解析错误
**问题**：接收到事件但解析失败
**解决方案**：
- 检查服务器发送的事件格式
- 确认Content-Type为text/event-stream
- 查看错误日志获取详细信息

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **使用测试端点**
   ```bash
   # 使用curl测试SSE端点
   curl -N -H "Accept: text/event-stream" https://your-sse-server.com/stream
   ```

3. **检查网络连接**
   ```bash
   # 测试基本连接
   curl -I https://your-sse-server.com/stream
   ```

## 🔒 安全注意事项

1. **保护认证令牌**
   - 不要在日志中记录敏感信息
   - 使用环境变量存储令牌
   - 定期轮换API密钥

2. **验证SSL证书**
   - 确保使用HTTPS连接
   - 验证服务器证书有效性

3. **限制连接时间**
   - 设置合理的超时时间
   - 限制最大事件数量
   - 避免无限期连接

## 📈 性能优化

1. **连接管理**
   - 合理设置超时时间
   - 使用连接池（如果支持）
   - 及时关闭不需要的连接

2. **事件处理**
   - 限制最大事件数量
   - 使用流式处理避免内存溢出
   - 定期清理事件缓存

3. **错误处理**
   - 实现指数退避重试
   - 设置最大重试次数
   - 记录错误统计信息

## 📞 技术支持

如遇到问题，请：
1. 查看插件日志
2. 检查配置是否正确
3. 参考故障排除指南
4. 联系技术支持：lw@example.com

## 🔄 更新日志

### v0.0.1 (2024-01-01)
- 初始版本发布
- 支持基本SSE连接
- 实现多种认证方式
- 添加自动重试机制