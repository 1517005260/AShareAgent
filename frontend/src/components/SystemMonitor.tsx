import React, { useState, useEffect } from 'react';
import { ApiService } from '../services/api';

interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  services: {
    database: boolean;
    redis: boolean;
    workers: boolean;
  };
  uptime: number;
  version: string;
}

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
  request_count_24h: number;
  error_count_24h: number;
  average_response_time: number;
}

interface LogEntry {
  id: number;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  message: string;
  timestamp: string;
  module?: string;
}

const SystemMonitor: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'health' | 'metrics' | 'logs'>('health');
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadSystemData();
    
    let interval: number;
    if (autoRefresh) {
      interval = setInterval(loadSystemData, 30000); // 30秒刷新一次
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const loadSystemData = async () => {
    try {
      setError(null);
      
      // 并行加载数据
      const [healthResponse, metricsResponse, logsResponse] = await Promise.allSettled([
        ApiService.getSystemHealth(),
        ApiService.getSystemMetrics(),
        ApiService.getSystemLogs()
      ]);

      if (healthResponse.status === 'fulfilled' && healthResponse.value.success) {
        setHealth(healthResponse.value.data);
      }

      if (metricsResponse.status === 'fulfilled' && metricsResponse.value.success) {
        setMetrics(metricsResponse.value.data);
      }

      if (logsResponse.status === 'fulfilled' && logsResponse.value.success) {
        setLogs(logsResponse.value.data || []);
      }

      // 如果所有请求都失败，显示错误
      if (
        healthResponse.status === 'rejected' && 
        metricsResponse.status === 'rejected' && 
        logsResponse.status === 'rejected'
      ) {
        setError('无法获取系统监控数据，可能权限不足');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '获取系统数据失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'critical':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'INFO':
        return 'text-blue-600 bg-blue-100';
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-100';
      case 'ERROR':
        return 'text-red-600 bg-red-100';
      case 'DEBUG':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}天 ${hours}小时 ${minutes}分钟`;
  };


  if (loading && !health && !metrics) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-lg">加载系统监控数据中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">系统监控</h2>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded text-sm ${
              autoRefresh
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-gray-600 text-white hover:bg-gray-700'
            }`}
          >
            {autoRefresh ? '自动刷新开启' : '自动刷新关闭'}
          </button>
          <button
            onClick={loadSystemData}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '刷新中...' : '手动刷新'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded">
          ⚠️ {error}
        </div>
      )}

      {/* 标签页导航 */}
      <div className="border-b mb-6">
        <nav className="flex space-x-8">
          {[
            { key: 'health', label: '系统健康' },
            { key: 'metrics', label: '性能指标' },
            { key: 'logs', label: '系统日志' }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* 系统健康状态 */}
      {activeTab === 'health' && (
        <div className="space-y-6">
          {health ? (
            <>
              {/* 总体状态 */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">系统总体状态</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="text-center">
                    <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(health.status || 'unknown')}`}>
                      {health.status === 'healthy' ? '健康' : 
                       health.status === 'warning' ? '警告' : health.status === 'critical' ? '严重' : '未知'}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">系统状态</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {formatUptime(health.uptime || 0)}
                    </div>
                    <div className="text-sm text-gray-600">运行时间</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {health.version || 'Unknown'}
                    </div>
                    <div className="text-sm text-gray-600">系统版本</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {new Date().toLocaleTimeString('zh-CN')}
                    </div>
                    <div className="text-sm text-gray-600">最后更新</div>
                  </div>
                </div>
              </div>

              {/* 服务状态 */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">服务状态</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {Object.entries(health.services || {}).map(([service, status]) => (
                    <div key={service} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <div className="font-medium capitalize">
                          {service === 'database' ? '数据库' : 
                           service === 'redis' ? 'Redis缓存' : 
                           service === 'workers' ? '后台任务' : service}
                        </div>
                        <div className="text-sm text-gray-600">
                          {service === 'database' ? 'PostgreSQL/SQLite' : 
                           service === 'redis' ? 'Redis服务' : 
                           service === 'workers' ? 'Celery Workers' : ''}
                        </div>
                      </div>
                      <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                        status ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'
                      }`}>
                        {status ? '正常' : '异常'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-center text-gray-500 py-8">
                无法获取系统健康状态数据
              </div>
            </div>
          )}
        </div>
      )}

      {/* 性能指标 */}
      {activeTab === 'metrics' && (
        <div className="space-y-6">
          {metrics ? (
            <>
              {/* 系统资源使用 */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">系统资源使用</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="relative w-24 h-24 mx-auto mb-2">
                      <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="transparent"
                          className="text-gray-200"
                        />
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="transparent"
                          strokeDasharray={`${(metrics.cpu_usage || 0) * 2.51} 251`}
                          className={`${(metrics.cpu_usage || 0) > 80 ? 'text-red-500' : 
                                     (metrics.cpu_usage || 0) > 60 ? 'text-yellow-500' : 'text-green-500'}`}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-xl font-bold">{(metrics.cpu_usage || 0).toFixed(1)}%</div>
                      </div>
                    </div>
                    <div className="text-sm text-gray-600">CPU使用率</div>
                  </div>

                  <div className="text-center">
                    <div className="relative w-24 h-24 mx-auto mb-2">
                      <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="transparent"
                          className="text-gray-200"
                        />
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="transparent"
                          strokeDasharray={`${(metrics.memory_usage || 0) * 2.51} 251`}
                          className={`${(metrics.memory_usage || 0) > 80 ? 'text-red-500' : 
                                     (metrics.memory_usage || 0) > 60 ? 'text-yellow-500' : 'text-blue-500'}`}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-xl font-bold">{(metrics.memory_usage || 0).toFixed(1)}%</div>
                      </div>
                    </div>
                    <div className="text-sm text-gray-600">内存使用率</div>
                  </div>

                  <div className="text-center">
                    <div className="relative w-24 h-24 mx-auto mb-2">
                      <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="transparent"
                          className="text-gray-200"
                        />
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="transparent"
                          strokeDasharray={`${(metrics.disk_usage || 0) * 2.51} 251`}
                          className={`${(metrics.disk_usage || 0) > 80 ? 'text-red-500' : 
                                     (metrics.disk_usage || 0) > 60 ? 'text-yellow-500' : 'text-purple-500'}`}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-xl font-bold">{(metrics.disk_usage || 0).toFixed(1)}%</div>
                      </div>
                    </div>
                    <div className="text-sm text-gray-600">磁盘使用率</div>
                  </div>
                </div>
              </div>

              {/* 应用指标 */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">应用性能指标</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {metrics.active_connections || 0}
                    </div>
                    <div className="text-sm text-gray-600">活跃连接数</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {(metrics.request_count_24h || 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">24小时请求数</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-red-600">
                      {metrics.error_count_24h || 0}
                    </div>
                    <div className="text-sm text-gray-600">24小时错误数</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-600">
                      {metrics.average_response_time || 0}ms
                    </div>
                    <div className="text-sm text-gray-600">平均响应时间</div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-center text-gray-500 py-8">
                无法获取性能指标数据
              </div>
            </div>
          )}
        </div>
      )}

      {/* 系统日志 */}
      {activeTab === 'logs' && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold">系统日志</h3>
          </div>
          
          {logs.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              暂无系统日志数据
            </div>
          ) : (
            <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
              {logs.map((log) => (
                <div key={log.id} className="p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getLogLevelColor(log.level)}`}>
                          {log.level}
                        </span>
                        {log.module && (
                          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                            {log.module}
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-900 break-all">
                        {log.message}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 ml-4 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString('zh-CN')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SystemMonitor;