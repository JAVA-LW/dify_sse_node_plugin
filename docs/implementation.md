# Dify SSE 请求工具插件实现文档

## 官方插件目录结构
参考：https://docs.dify.ai/plugin-dev-zh/0211-getting-started-by-prompt

```
your_plugin/
├── _assets/             # 图标和视觉资源
├── provider/            # 提供者定义和验证
│   ├── your_plugin.py   # 凭证验证逻辑
│   └── your_plugin.yaml # 提供者配置
├── tools/               # 工具实现
│   ├── feature_one.py   # 工具功能实现
│   ├── feature_one.yaml # 工具参数和描述
│   ├── feature_two.py   # 另一个工具实现
│   └── feature_two.yaml # 另一个工具配置
├── utils/               # 辅助函数
│   └── helpers.py       # 通用功能逻辑
├── working/             # 进度记录和工作文件
├── .env.example         # 环境变量模板
├── main.py              # 入口文件
├── manifest.yaml        # 插件主配置
├── README.md            # 文档
└── requirements.txt     # 依赖列表
```

## 参考资料
- 工具插件开发的官方文档：https://docs.dify.ai/plugin-dev-zh/0222-tool-plugin
- Dify HTTP请求节点源码：`e:\code\tongdaCode\dify\api\core\workflow\nodes\http_request`

## SSE 请求工具实现思路

### 1. 功能需求分析
基于HTTP请求节点的设计，SSE请求工具需要支持：
- **基础SSE连接**：建立长连接，接收服务器推送的事件流
- **请求配置**：URL、Headers、Query参数、认证方式
- **连接管理**：超时设置、重连机制、连接状态监控
- **数据处理**：实时接收SSE事件，解析event-stream格式
- **结果输出**：流式输出接收到的数据，最终汇总完整结果

### 2. 核心技术要点

#### 2.1 SSE协议特点
- Content-Type: `text/event-stream`
- 数据格式：`data: {content}\n\n` 或 `event: {type}\ndata: {content}\n\n`
- 长连接保持，服务器主动推送数据
- 支持断线重连机制

#### 2.2 与HTTP请求节点的差异
| 特性 | HTTP请求 | SSE请求 |
|------|----------|---------|
| 连接类型 | 短连接 | 长连接 |
| 数据接收 | 一次性响应 | 流式接收 |
| 处理方式 | 同步等待 | 异步监听 |
| 输出格式 | 完整响应体 | 实时事件流 + 最终汇总 |

### 3. 实现架构设计

#### 3.1 参数配置（参考HTTP请求节点）
```yaml
parameters:
  - name: url
    type: string
    required: true
    label: "SSE服务器URL"
    
  - name: headers
    type: string
    required: false
    label: "请求头"
    form: llm
    
  - name: query_params
    type: string
    required: false
    label: "查询参数"
    
  - name: timeout
    type: number
    required: false
    default: 30
    label: "连接超时时间(秒)"
    
  - name: max_events
    type: number
    required: false
    default: 100
    label: "最大事件数量"
    
  - name: auth_type
    type: select
    required: false
    default: "none"
    options:
      - value: "none"
        label: "无认证"
      - value: "bearer"
        label: "Bearer Token"
      - value: "api_key"
        label: "API Key"
        
  - name: auth_token
    type: string
    required: false
    label: "认证令牌"
```

#### 3.2 核心实现逻辑
```python
class SSEClient:
    def __init__(self, url, headers=None, timeout=30):
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        self.events = []
        
    def connect(self):
        """建立SSE连接"""
        # 设置SSE专用headers
        self.headers.update({
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache'
        })
        
    def listen(self, max_events=100):
        """监听SSE事件流"""
        # 使用httpx或requests的stream模式
        # 解析event-stream格式
        # 实时yield事件数据
        
    def parse_sse_event(self, line):
        """解析SSE事件格式"""
        # 处理 data:, event:, id:, retry: 等字段
```

### 4. 输出格式设计

#### 4.1 实时流式输出
```json
{
  "type": "event",
  "event_type": "message",
  "data": "实时接收的数据",
  "timestamp": "2024-01-01T12:00:00Z",
  "event_id": "1"
}
```

#### 4.2 最终汇总输出
```json
{
  "status": "completed",
  "total_events": 50,
  "connection_duration": 25.5,
  "events": [
    {
      "event_type": "message",
      "data": "事件数据1",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "summary": "连接成功，接收到50个事件，耗时25.5秒"
}
```

### 5. 错误处理机制

#### 5.1 连接错误
- 网络连接失败
- 认证失败
- 服务器拒绝连接

#### 5.2 数据处理错误
- SSE格式解析错误
- 数据编码问题
- 超时处理

#### 5.3 重连机制
- 自动重连策略
- 重连间隔设置
- 最大重连次数限制

### 6. 依赖库选择
- **httpx**: 支持异步HTTP请求和流式处理
- **sseclient-py**: 专门的SSE客户端库
- **asyncio**: 异步处理支持

### 7. 测试计划
- 单元测试：SSE事件解析、连接管理
- 集成测试：与真实SSE服务器的连接测试
- 性能测试：长连接稳定性、内存使用情况

### 8. 实现步骤
1. ✅ 完善参数配置文件 (dify_sse_node_plugin.yaml)
2. ⏳ 实现核心SSE客户端逻辑
3. ⏳ 添加认证和错误处理
4. ⏳ 实现流式输出机制
5. ⏳ 添加配置验证和测试
6. ⏳ 完善文档和示例