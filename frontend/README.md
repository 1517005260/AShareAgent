# A股投资Agent前端监控平台

这是一个基于React + TypeScript + Ant Design的前端应用，用于监控和管理A股投资Agent的后端API。

## 功能特性

### 1. 分析控制台
- 启动新的股票分析任务
- 实时监控分析进度
- 查看分析结果

### 2. Agent监控
- 实时查看所有Agent状态
- 查看Agent的输入输出数据
- 监控Agent推理过程

### 3. 运行历史
- 查看历史分析任务
- 查看任务详细信息
- 任务状态追踪

## 技术栈

- **React 18** - 前端框架
- **TypeScript** - 类型安全
- **Ant Design** - UI组件库
- **Axios** - HTTP客户端
- **Vite** - 构建工具

## 快速开始

### 前置要求
- Node.js >= 16
- npm 或 yarn

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

## API配置

默认后端API地址为 `http://127.0.0.1:8000`，可在 `src/services/api.ts` 中修改：

```typescript
const API_BASE_URL = 'http://127.0.0.1:8000';
```

## 主要组件

### AnalysisForm
股票分析启动表单，支持配置：
- 股票代码
- 是否显示推理过程
- 新闻数量
- 初始资金和仓位

### AnalysisStatus
实时显示分析任务状态：
- 任务进度追踪
- 结果展示
- 自动轮询更新

### AgentMonitor
Agent状态监控：
- 所有Agent列表
- Agent详细信息
- 实时状态更新

### RunHistory
历史运行记录：
- 分页显示历史任务
- 任务详情查看
- 状态筛选

## 使用说明

1. 确保后端API服务正在运行 (`http://127.0.0.1:8000`)
2. 启动前端开发服务器
3. 在"分析控制台"页面输入股票代码启动分析
4. 在"Agent监控"页面查看Agent实时状态
5. 在"运行历史"页面查看历史分析记录

## 项目结构

```
src/
├── components/          # React组件
│   ├── AnalysisForm.tsx    # 分析表单
│   ├── AnalysisStatus.tsx  # 状态监控
│   ├── AgentMonitor.tsx    # Agent监控
│   ├── RunHistory.tsx      # 运行历史
│   └── index.ts           # 组件导出
├── services/           # API服务
│   └── api.ts             # API调用封装
├── App.tsx             # 主应用组件
├── App.css             # 样式文件
└── main.tsx           # 应用入口
```

## 开发注意事项

- 所有API调用都通过 `ApiService` 类统一管理
- 使用TypeScript接口定义数据结构
- 遵循Ant Design设计规范
- 支持响应式布局
