# AShare Agent 前端系统

一个基于 React + TypeScript + Ant Design 构建的现代化股票分析和投资决策平台前端系统。

## 🚀 核心功能

### 1. 股票分析模块
- **实时股票分析**: 支持单股票深度分析，集成多个智能Agent
- **分析结果可视化**: 提供详细的分析报告和推理过程展示
- **历史分析记录**: 完整的分析历史追踪和结果对比

### 2. 策略回测系统
- **智能回测引擎**: 基于历史数据的策略回测验证
- **多Agent协同**: 支持技术分析、基本面分析、情感分析等多维度策略
- **性能指标分析**: 详细的回测结果和风险指标评估

### 3. Agent管理平台
- **Agent状态监控**: 实时监控各个分析Agent的运行状态
- **Agent配置管理**: 动态配置Agent参数和执行频率
- **决策历史追踪**: 完整记录每个Agent的决策过程和推理链

### 4. 投资组合管理
- **多组合管理**: 支持创建和管理多个投资组合
- **持仓分析**: 实时持仓状态和收益分析
- **交易记录**: 完整的交易历史和统计分析

### 5. 用户权限系统
- **角色权限控制**: 基于RBAC的细粒度权限管理
- **安全认证**: JWT token认证和权限验证
- **用户配置**: 个人信息管理和偏好设置

## 🏗️ 项目结构

```
frontend/
├── public/                     # 静态资源
│   └── vite.svg
├── src/                        # 源代码目录
│   ├── components/             # React组件库
│   │   ├── AgentDashboard.tsx      # Agent管理面板
│   │   ├── AgentManagement.tsx     # Agent配置管理
│   │   ├── AgentMonitor.tsx        # Agent状态监控
│   │   ├── AnalysisForm.tsx        # 股票分析表单
│   │   ├── AnalysisStatus.tsx      # 分析状态展示
│   │   ├── BacktestForm.tsx        # 回测参数配置
│   │   ├── BacktestStatus.tsx      # 回测进度监控
│   │   ├── DecisionHistory.tsx     # 决策历史记录
│   │   ├── HistoryDashboard.tsx    # 历史数据面板
│   │   ├── LoginForm.tsx           # 用户登录表单
│   │   ├── PersonalStats.tsx       # 个人统计面板
│   │   ├── PortfolioManagement.tsx # 投资组合管理
│   │   ├── ReportView.tsx          # 报告查看器
│   │   ├── RunHistory.tsx          # 运行历史记录
│   │   ├── SystemMonitor.tsx       # 系统监控面板
│   │   ├── UserProfile.tsx         # 用户配置页面
│   │   └── index.ts                # 组件导出文件
│   ├── services/               # API服务层
│   │   └── api.ts                  # 统一API服务封装
│   ├── assets/                 # 静态资源
│   │   └── react.svg
│   ├── App.tsx                 # 主应用组件
│   ├── App.css                 # 主应用样式
│   ├── main.tsx                # 应用入口文件
│   ├── index.css               # 全局样式
│   └── vite-env.d.ts           # TypeScript声明文件
├── dist/                       # 构建输出目录
├── node_modules/               # 依赖包目录
├── eslint.config.js            # ESLint配置
├── index.html                  # HTML模板
├── package.json                # 项目配置文件
├── package-lock.json           # 依赖锁定文件
├── tsconfig.json               # TypeScript配置
├── tsconfig.app.json           # 应用TypeScript配置
├── tsconfig.node.json          # Node.js TypeScript配置
└── vite.config.ts              # Vite构建配置
```

## 🔧 核心技术栈

- **React 19**: 现代化React框架，支持最新特性
- **TypeScript**: 类型安全的JavaScript超集
- **Ant Design**: 企业级UI设计语言和组件库
- **Vite**: 快速的前端构建工具
- **Axios**: HTTP客户端库，用于API通信
- **Day.js**: 轻量级日期处理库

## 💡 核心代码示例

### 1. 主应用架构 (App.tsx:36-294)

```tsx
function App() {
  const [selectedMenu, setSelectedMenu] = useState<MenuKey>('dashboard');
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // 权限检查
  const hasPermission = (permission: string): boolean => {
    return user?.permissions?.includes(permission) || 
           user?.roles?.includes('admin') || false;
  };

  // 动态菜单生成
  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '股票分析',
    },
    ...(hasPermission('backtest:basic') ? [{
      key: 'backtest',
      icon: <ExperimentOutlined />,
      label: '策略回测',
    }] : []),
    // ... 其他菜单项
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="app-header">
        {/* 头部组件 */}
      </Header>
      <Layout>
        <Sider width={200}>
          <Menu
            mode="inline"
            selectedKeys={[selectedMenu]}
            items={menuItems}
            onSelect={({ key }) => setSelectedMenu(key as MenuKey)}
          />
        </Sider>
        <Content>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
}
```

### 2. API服务封装 (services/api.ts:5-33)

```tsx
// API基础配置
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 自动token注入
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器处理认证错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_info');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 3. 股票分析表单组件 (components/AnalysisForm.tsx:10-75)

```tsx
const AnalysisForm: React.FC<AnalysisFormProps> = ({ onAnalysisStart }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: AnalysisRequest) => {
    setLoading(true);
    try {
      const response = await ApiService.startAnalysis(values);
      if (response.success && response.data?.run_id) {
        message.success('分析任务已启动');
        onAnalysisStart(response.data.run_id);
      }
    } catch (error) {
      message.error('启动分析失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="启动股票分析">
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          show_reasoning: true,
          num_of_news: 20,
          initial_capital: 100000,
        }}
      >
        <Form.Item
          label="股票代码"
          name="ticker"
          rules={[{ required: true, message: '请输入股票代码' }]}
        >
          <Input placeholder="例如: 000001" />
        </Form.Item>
        
        <Form.Item>
          <Button 
            type="primary" 
            htmlType="submit" 
            loading={loading}
            icon={<PlayCircleOutlined />}
          >
            开始分析
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};
```

### 4. 回测系统核心代码 (components/BacktestForm.tsx:14-44)

```tsx
const BacktestForm: React.FC<BacktestFormProps> = ({ onBacktestStart }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const request: BacktestRequest = {
        ticker: values.ticker,
        start_date: values.dateRange[0].format('YYYY-MM-DD'),
        end_date: values.dateRange[1].format('YYYY-MM-DD'),
        initial_capital: values.initial_capital || 100000,
        num_of_news: values.num_of_news || 5,
        agent_frequencies: values.enable_advanced ? values.agent_frequencies : undefined,
      };

      const response = await ApiService.startBacktest(request);
      if (response.success && response.data) {
        message.success('回测任务已启动！');
        onBacktestStart(response.data.run_id);
        form.resetFields();
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '启动回测失败');
    } finally {
      setLoading(false);
    }
  };
```

### 5. TypeScript接口定义 (services/api.ts:127-196)

```tsx
// 用户信息接口
export interface UserInfo {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  roles: string[];
  permissions: string[];
  created_at: string;
}

// API响应统一格式
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 回测请求接口
export interface BacktestRequest {
  ticker: string;
  start_date: string;
  end_date: string;
  initial_capital?: number;
  num_of_news?: number;
  agent_frequencies?: Record<string, string>;
}

// 回测结果接口
export interface BacktestResult {
  task_id: string;
  ticker: string;
  start_date: string;
  end_date: string;
  completion_time: string;
  result: {
    performance_metrics: Record<string, number>;
    risk_metrics: Record<string, number>;
    trades: Array<Record<string, any>>;
    portfolio_values: {
      dates: string[];
      values: number[];
    };
    benchmark_comparison?: Record<string, any>;
  };
}
```

## 🎨 UI/UX设计特色

### 1. 响应式布局
- 支持移动端和桌面端自适应
- 侧边栏折叠和展开功能 (App.tsx:261-275)
- 灵活的栅格系统

### 2. 现代化交互
- 流畅的动画效果
- 实时状态反馈
- 友好的错误提示

### 3. 权限驱动的UI
```tsx
// 基于权限的菜单动态生成 (App.tsx:178-219)
const menuItems = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: '股票分析',
  },
  ...(hasPermission('backtest:basic') ? [{
    key: 'backtest',
    icon: <ExperimentOutlined />,
    label: '策略回测',
  }] : []),
  ...(hasPermission('portfolio:read') ? [{
    key: 'portfolios',
    icon: <FundOutlined />,
    label: '投资组合',
  }] : []),
];
```

## 🔐 安全特性

### 1. 身份认证 (App.tsx:44-64)
- JWT Token认证机制
- 自动token刷新
- 登录状态持久化

### 2. 权限控制 (App.tsx:90-93)
- 基于角色的访问控制(RBAC)
- 菜单动态渲染
- API权限验证

### 3. 数据安全 (services/api.ts:12-33)
- 请求/响应拦截器
- 自动token注入
- 401/403错误自动处理

## 🚀 快速开始

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖
```bash
cd frontend
npm install
```

### 开发模式
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 代码检查
```bash
npm run lint
```

## 🔍 开发规范

### 1. 组件规范
- 使用TypeScript编写所有组件
- 遵循函数式组件模式
- 统一的Props接口定义

### 2. 状态管理
- 使用React Hooks管理本地状态
- API数据通过ApiService统一管理
- 避免不必要的状态提升

### 3. API服务模式
所有API调用统一通过 `ApiService` 类管理 (services/api.ts:209-566):
- 分析相关API (210-224行)
- Agent管理API (227-310行)
- 认证相关API (318-337行)
- 回测系统API (339-378行)
- 投资组合API (455-512行)

## 📈 性能优化

### 1. 代码分割
- 路由级别的懒加载
- 组件按需导入
- 第三方库优化

### 2. 缓存策略
- API响应缓存
- 组件memorization
- 静态资源缓存

### 3. 构建优化
- Vite构建优化
- Tree shaking
- 代码压缩

## 🤝 贡献指南

1. Fork项目到个人仓库
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -am '添加新功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。