import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 添加请求拦截器以自动添加认证token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 添加响应拦截器处理认证错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      // 清除token并跳转到登录页
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_info');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API响应接口
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 分析相关接口
export interface AnalysisRequest {
  ticker: string;
  show_reasoning?: boolean;
  num_of_news?: number;
  initial_capital?: number;
  initial_position?: number;
  start_date?: string;
  end_date?: string;
  show_summary?: boolean;
}

export interface AnalysisStatus {
  run_id: string;
  status: 'running' | 'completed' | 'failed';
  progress?: string;
  result?: any;
}

// Agent接口
export interface Agent {
  name: string;
  status: string;
  latest_input?: any;
  latest_output?: any;
  reasoning?: any;
}

// 管理Agent接口
export interface ManagedAgent {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  agent_type: string;
  status: string;
  config?: any;
  created_at: string;
  updated_at: string;
}

// Agent决策记录接口
export interface AgentDecision {
  id: number;
  run_id: string;
  agent_name: string;
  agent_display_name?: string;
  ticker: string;
  decision_type: string;
  decision_data: any;
  confidence_score?: number;
  reasoning?: string;
  created_at: string;
}

// Agent创建请求接口
export interface AgentCreateRequest {
  name: string;
  display_name: string;
  description?: string;
  agent_type: string;
  status: string;
  config?: any;
}

// Agent更新请求接口
export interface AgentUpdateRequest {
  display_name?: string;
  description?: string;
  status?: string;
  config?: any;
}

// 认证相关接口
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  phone?: string;
}

export interface UserInfo {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  phone?: string;
  is_active: boolean;
  roles: string[];
  permissions: string[];
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

// 回测相关接口
export interface BacktestRequest {
  ticker: string;
  start_date: string;
  end_date: string;
  initial_capital?: number;
  num_of_news?: number;
  agent_frequencies?: Record<string, string>;
  time_granularity?: string;
  benchmark_type?: string;
  rebalance_frequency?: string;
  transaction_cost?: number;
  slippage?: number;
}

export interface BacktestResponse {
  run_id: string;
  ticker: string;
  start_date: string;
  end_date: string;
  status: string;
  message: string;
  submitted_at: string;
  completed_at?: string;
}

export interface BacktestStatus {
  task_id: string;
  ticker: string;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  is_running?: boolean;
  runtime_error?: string;
}

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
    plot_path?: string;
    plot_url?: string;
    run_id?: string;
  };
}

// Run接口
export interface Run {
  run_id: string;
  status: string;
  start_time: string;
  end_time: string;
  agents_executed: string[];
  ticker?: string;
}

// API服务类
export class ApiService {
  // 分析相关
  static async startAnalysis(request: AnalysisRequest): Promise<ApiResponse<{ run_id: string }>> {
    const response = await api.post('/api/analysis/start', request);
    return response.data;
  }

  static async getAnalysisStatus(runId: string): Promise<ApiResponse<AnalysisStatus>> {
    const response = await api.get(`/api/analysis/${runId}/status`);
    return response.data;
  }

  static async getAnalysisResult(runId: string): Promise<ApiResponse<any>> {
    const response = await api.get(`/api/analysis/${runId}/result`);
    return response.data;
  }

  // Agent相关
  static async getAgents(): Promise<ApiResponse<Agent[]>> {
    const response = await api.get('/api/agents/');
    return response.data;
  }

  static async getAgent(agentName: string): Promise<ApiResponse<Agent>> {
    const response = await api.get(`/api/agents/${agentName}`);
    return response.data;
  }

  static async getAgentLatestInput(agentName: string): Promise<ApiResponse<any>> {
    const response = await api.get(`/api/agents/${agentName}/latest_input`);
    return response.data;
  }

  static async getAgentLatestOutput(agentName: string): Promise<ApiResponse<any>> {
    const response = await api.get(`/api/agents/${agentName}/latest_output`);
    return response.data;
  }

  // Run相关
  static async getRuns(limit: number = 10): Promise<Run[]> {
    const response = await api.get(`/runs/?limit=${limit}`);
    return response.data;
  }

  static async getRun(runId: string): Promise<Run> {
    const response = await api.get(`/runs/${runId}`);
    return response.data;
  }

  // 工作流相关
  static async getWorkflowStatus(): Promise<ApiResponse<any>> {
    const response = await api.get('/api/workflow/status');
    return response.data;
  }

  // 日志相关
  static async getLogs(params?: {
    agent_name?: string;
    run_id?: string;
    limit?: number;
  }): Promise<ApiResponse<any[]>> {
    const queryParams = new URLSearchParams();
    if (params?.agent_name) queryParams.append('agent_name', params.agent_name);
    if (params?.run_id) queryParams.append('run_id', params.run_id);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    
    const response = await api.get(`/logs/?${queryParams.toString()}`);
    return response.data;
  }

  // Agent管理相关
  static async getManagedAgents(): Promise<ApiResponse<ManagedAgent[]>> {
    const response = await api.get('/api/agents/manage');
    return response.data;
  }

  static async createAgent(request: AgentCreateRequest): Promise<ApiResponse<any>> {
    const response = await api.post('/api/agents/manage', request);
    return response.data;
  }

  static async updateAgent(agentName: string, request: AgentUpdateRequest): Promise<ApiResponse<any>> {
    const response = await api.put(`/api/agents/manage/${agentName}`, request);
    return response.data;
  }

  // Agent决策记录相关
  static async getAgentDecisions(params?: {
    run_id?: string;
    agent_name?: string;
    ticker?: string;
    limit?: number;
  }): Promise<ApiResponse<AgentDecision[]>> {
    const queryParams = new URLSearchParams();
    if (params?.run_id) queryParams.append('run_id', params.run_id);
    if (params?.agent_name) queryParams.append('agent_name', params.agent_name);
    if (params?.ticker) queryParams.append('ticker', params.ticker);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    
    const response = await api.get(`/api/agents/decisions?${queryParams.toString()}`);
    return response.data;
  }

  static async getFormattedDecision(runId: string): Promise<ApiResponse<string>> {
    const response = await api.get(`/api/agents/decisions/${runId}/formatted`);
    return response.data;
  }

  // 认证相关
  static async login(request: LoginRequest): Promise<ApiResponse<Token>> {
    const response = await api.post('/api/auth/login', request);
    return response.data;
  }

  static async register(request: RegisterRequest): Promise<ApiResponse<UserInfo>> {
    const response = await api.post('/api/auth/register', request);
    return response.data;
  }

  static async getCurrentUser(): Promise<ApiResponse<UserInfo>> {
    const response = await api.get('/api/auth/me');
    return response.data;
  }

  static async logout(): Promise<void> {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  }

  // 回测相关
  static async startBacktest(request: BacktestRequest): Promise<ApiResponse<BacktestResponse>> {
    const response = await api.post('/api/backtest/start', request);
    return response.data;
  }

  static async getBacktestStatus(runId: string): Promise<ApiResponse<BacktestStatus>> {
    const response = await api.get(`/api/backtest/${runId}/status`);
    return response.data;
  }

  static async getBacktestResult(runId: string): Promise<ApiResponse<BacktestResult>> {
    const response = await api.get(`/api/backtest/${runId}/result`);
    return response.data;
  }

  static async getBacktestHistory(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    ticker?: string;
  }): Promise<ApiResponse<{
    tasks: BacktestStatus[];
    total: number;
    skip: number;
    limit: number;
  }>> {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.ticker) queryParams.append('ticker', params.ticker);
    
    const response = await api.get(`/api/backtest/history?${queryParams.toString()}`);
    return response.data;
  }

  static async deleteBacktestTask(taskId: string): Promise<ApiResponse<boolean>> {
    const response = await api.delete(`/api/backtest/${taskId}`);
    return response.data;
  }

  static async getAnalysisHistory(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    ticker?: string;
  }): Promise<ApiResponse<{
    tasks: any[];
    total: number;
    skip: number;
    limit: number;
  }>> {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.ticker) queryParams.append('ticker', params.ticker);
    
    const response = await api.get(`/api/analysis/history?${queryParams.toString()}`);
    return response.data;
  }

  // 用户管理相关API
  static async updateCurrentUser(userData: {
    full_name?: string;
    email?: string;
    phone?: string;
  }): Promise<ApiResponse<UserInfo>> {
    const response = await api.put('/api/auth/me', userData);
    return response.data;
  }

  static async changePassword(passwordData: {
    current_password: string;
    new_password: string;
  }): Promise<ApiResponse<boolean>> {
    const response = await api.post('/api/auth/change-password', passwordData);
    return response.data;
  }

  static async getUserList(): Promise<ApiResponse<UserInfo[]>> {
    const response = await api.get('/api/auth/users');
    return response.data;
  }

  static async getUserById(userId: number): Promise<ApiResponse<UserInfo>> {
    const response = await api.get(`/api/auth/users/${userId}`);
    return response.data;
  }

  static async getRoles(): Promise<ApiResponse<string[]>> {
    const response = await api.get('/api/auth/roles');
    return response.data;
  }

  static async getPermissions(): Promise<ApiResponse<string[]>> {
    const response = await api.get('/api/auth/permissions');
    return response.data;
  }

  static async getUserLogs(): Promise<ApiResponse<any[]>> {
    const response = await api.get('/api/auth/logs/me');
    return response.data;
  }

  static async assignUserRole(userId: number, roleName: string): Promise<ApiResponse<boolean>> {
    const response = await api.post(`/api/auth/users/${userId}/roles/${roleName}`);
    return response.data;
  }

  static async removeUserRole(userId: number, roleName: string): Promise<ApiResponse<boolean>> {
    const response = await api.delete(`/api/auth/users/${userId}/roles/${roleName}`);
    return response.data;
  }

  // 投资组合管理API
  static async createPortfolio(portfolioData: {
    name: string;
    description?: string;
    initial_capital: number;
    risk_level?: string;
  }): Promise<ApiResponse<any>> {
    const response = await api.post('/api/portfolios/', portfolioData);
    return response.data;
  }

  static async getPortfolios(): Promise<ApiResponse<any[]>> {
    const response = await api.get('/api/portfolios/');
    return response.data;
  }

  static async getPortfolio(portfolioId: number): Promise<ApiResponse<any>> {
    const response = await api.get(`/api/portfolios/${portfolioId}`);
    return response.data;
  }

  static async updatePortfolio(portfolioId: number, portfolioData: {
    name?: string;
    description?: string;
    risk_level?: string;
  }): Promise<ApiResponse<any>> {
    const response = await api.put(`/api/portfolios/${portfolioId}`, portfolioData);
    return response.data;
  }

  static async deletePortfolio(portfolioId: number): Promise<ApiResponse<boolean>> {
    const response = await api.delete(`/api/portfolios/${portfolioId}`);
    return response.data;
  }

  static async getPortfolioSummary(portfolioId: number): Promise<ApiResponse<any>> {
    const response = await api.get(`/api/portfolios/${portfolioId}/summary`);
    return response.data;
  }

  static async getPortfolioHoldings(portfolioId: number): Promise<ApiResponse<any[]>> {
    const response = await api.get(`/api/portfolios/${portfolioId}/holdings`);
    return response.data;
  }

  static async addTransaction(portfolioId: number, transactionData: any): Promise<ApiResponse<any>> {
    const response = await api.post(`/api/portfolios/${portfolioId}/transactions`, transactionData);
    return response.data;
  }

  static async getTransactions(portfolioId: number): Promise<ApiResponse<any[]>> {
    const response = await api.get(`/api/portfolios/${portfolioId}/transactions`);
    return response.data;
  }

  static async getPortfolioStats(): Promise<ApiResponse<any>> {
    const response = await api.get('/api/portfolios/stats/overview');
    return response.data;
  }

  // 系统监控API
  static async getSystemHealth(): Promise<ApiResponse<any>> {
    const response = await api.get('/api/monitor/health');
    return response.data;
  }

  static async getSystemMetrics(): Promise<ApiResponse<any>> {
    const response = await api.get('/api/monitor/metrics');
    return response.data;
  }

  static async getSystemLogs(): Promise<ApiResponse<any[]>> {
    const response = await api.get('/api/monitor/logs');
    return response.data;
  }

  static async getMonitorDashboard(): Promise<ApiResponse<any>> {
    const response = await api.get('/api/monitor/dashboard');
    return response.data;
  }

  // 统计API
  static async getSystemStats(): Promise<ApiResponse<any>> {
    const response = await api.get('/api/stats/overview');
    return response.data;
  }

  static async getDashboardStats(): Promise<ApiResponse<any>> {
    const response = await api.get('/api/stats/dashboard');
    return response.data;
  }

  static async getPersonalSummary(): Promise<ApiResponse<any>> {
    const response = await api.get('/api/stats/my/summary');
    return response.data;
  }

  // 系统配置API
  static async getConfigs(): Promise<ApiResponse<any[]>> {
    const response = await api.get('/api/config/');
    return response.data;
  }

  static async getConfigCategories(): Promise<ApiResponse<string[]>> {
    const response = await api.get('/api/config/categories');
    return response.data;
  }

  static async getSystemInfo(): Promise<ApiResponse<any>> {
    const response = await api.get('/api/config/system/info');
    return response.data;
  }
}

export default ApiService;