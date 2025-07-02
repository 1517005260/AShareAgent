import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
}

export default ApiService;