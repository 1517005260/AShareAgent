import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Progress,
  Statistic,
  Table,
  Tag,
  Button,
  Tabs,
  Alert,
  Spin,
  Switch,
  Badge
} from 'antd';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  ApiOutlined,
  MonitorOutlined,
  WarningOutlined
} from '@ant-design/icons';
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

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}天 ${hours}小时 ${minutes}分钟`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'warning':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'critical':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <WarningOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'INFO': return 'blue';
      case 'WARNING': return 'orange';
      case 'ERROR': return 'red';
      case 'DEBUG': return 'purple';
      default: return 'default';
    }
  };

  const getUsageColor = (usage: number) => {
    if (usage > 80) return '#ff4d4f';
    if (usage > 60) return '#faad14';
    return '#52c41a';
  };

  const logColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string) => new Date(timestamp).toLocaleString('zh-CN'),
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => (
        <Tag color={getLogLevelColor(level)}>
          {level}
        </Tag>
      ),
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      width: 120,
      render: (module: string) => module || '-',
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
  ];

  if (loading && !health && !metrics) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16, color: '#666' }}>加载系统监控数据中...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* 头部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>系统监控</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>自动刷新</span>
            <Switch checked={autoRefresh} onChange={setAutoRefresh} />
          </div>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadSystemData}
            loading={loading}
          >
            手动刷新
          </Button>
        </div>
      </div>

      {error && (
        <Alert
          message="监控数据获取失败"
          description={error}
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <Tabs
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key as any)}
        items={[
          {
            key: 'health',
            label: (
              <span>
                <CheckCircleOutlined />
                系统健康
              </span>
            ),
            children: (
              <div>
                {health ? (
                  <>
                    {/* 总体状态卡片 */}
                    <Card style={{ marginBottom: 16 }}>
                      <Row gutter={16}>
                        <Col span={6}>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '48px', marginBottom: 8 }}>
                              {getStatusIcon(health.status || 'unknown')}
                            </div>
                            <Badge
                              status={getStatusColor(health.status || 'unknown') as any}
                              text={
                                health.status === 'healthy' ? '系统健康' :
                                  health.status === 'warning' ? '系统警告' :
                                    health.status === 'critical' ? '系统严重' : '状态未知'
                              }
                              style={{ fontSize: '16px', fontWeight: 'bold' }}
                            />
                          </div>
                        </Col>
                        <Col span={6}>
                          <Statistic
                            title="运行时间"
                            value={formatUptime(health.uptime || 0)}
                            prefix={<CloudServerOutlined />}
                          />
                        </Col>
                        <Col span={6}>
                          <Statistic
                            title="系统版本"
                            value={health.version || 'Unknown'}
                            prefix={<ApiOutlined />}
                          />
                        </Col>
                        <Col span={6}>
                          <Statistic
                            title="最后更新"
                            value={new Date().toLocaleTimeString('zh-CN')}
                            prefix={<ReloadOutlined />}
                          />
                        </Col>
                      </Row>
                    </Card>

                    {/* 服务状态 */}
                    <Card title="服务状态">
                      <Row gutter={16}>
                        {Object.entries(health.services || {}).map(([service, status]) => (
                          <Col span={8} key={service}>
                            <Card size="small" style={{ textAlign: 'center' }}>
                              <div style={{ fontSize: '32px', marginBottom: 8 }}>
                                {service === 'database' && <DatabaseOutlined style={{ color: status ? '#52c41a' : '#ff4d4f' }} />}
                                {service === 'redis' && <CloudServerOutlined style={{ color: status ? '#52c41a' : '#ff4d4f' }} />}
                                {service === 'workers' && <ApiOutlined style={{ color: status ? '#52c41a' : '#ff4d4f' }} />}
                              </div>
                              <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                                {service === 'database' ? '数据库' :
                                  service === 'redis' ? 'Redis缓存' :
                                    service === 'workers' ? '后台任务' : service}
                              </div>
                              <Badge
                                status={status ? 'success' : 'error'}
                                text={status ? '正常运行' : '服务异常'}
                              />
                            </Card>
                          </Col>
                        ))}
                      </Row>
                    </Card>
                  </>
                ) : (
                  <Card>
                    <div style={{ textAlign: 'center', padding: '60px', color: '#999' }}>
                      <MonitorOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                      <div>无法获取系统健康状态数据</div>
                    </div>
                  </Card>
                )}
              </div>
            ),
          },
          {
            key: 'metrics',
            label: (
              <span>
                <MonitorOutlined />
                性能指标
              </span>
            ),
            children: (
              <div>
                {metrics ? (
                  <>
                    {/* 系统资源使用 */}
                    <Card title="系统资源使用" style={{ marginBottom: 16 }}>
                      <Row gutter={16}>
                        <Col span={8}>
                          <div style={{ textAlign: 'center' }}>
                            <Progress
                              type="circle"
                              percent={Math.round(metrics.cpu_usage || 0)}
                              strokeColor={getUsageColor(metrics.cpu_usage || 0)}
                              format={percent => `${percent}%`}
                            />
                            <div style={{ marginTop: 16, fontWeight: 'bold' }}>CPU使用率</div>
                          </div>
                        </Col>
                        <Col span={8}>
                          <div style={{ textAlign: 'center' }}>
                            <Progress
                              type="circle"
                              percent={Math.round(metrics.memory_usage || 0)}
                              strokeColor={getUsageColor(metrics.memory_usage || 0)}
                              format={percent => `${percent}%`}
                            />
                            <div style={{ marginTop: 16, fontWeight: 'bold' }}>内存使用率</div>
                          </div>
                        </Col>
                        <Col span={8}>
                          <div style={{ textAlign: 'center' }}>
                            <Progress
                              type="circle"
                              percent={Math.round(metrics.disk_usage || 0)}
                              strokeColor={getUsageColor(metrics.disk_usage || 0)}
                              format={percent => `${percent}%`}
                            />
                            <div style={{ marginTop: 16, fontWeight: 'bold' }}>磁盘使用率</div>
                          </div>
                        </Col>
                      </Row>
                    </Card>

                    {/* 应用性能指标 */}
                    <Card title="应用性能指标">
                      <Row gutter={16}>
                        <Col span={6}>
                          <Statistic
                            title="活跃连接数"
                            value={metrics.active_connections || 0}
                            prefix={<ApiOutlined style={{ color: '#1890ff' }} />}
                            valueStyle={{ color: '#1890ff' }}
                          />
                        </Col>
                        <Col span={6}>
                          <Statistic
                            title="24小时请求数"
                            value={(metrics.request_count_24h || 0).toLocaleString()}
                            prefix={<CloudServerOutlined style={{ color: '#52c41a' }} />}
                            valueStyle={{ color: '#52c41a' }}
                          />
                        </Col>
                        <Col span={6}>
                          <Statistic
                            title="24小时错误数"
                            value={metrics.error_count_24h || 0}
                            prefix={<ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
                            valueStyle={{ color: '#ff4d4f' }}
                          />
                        </Col>
                        <Col span={6}>
                          <Statistic
                            title="平均响应时间"
                            value={metrics.average_response_time || 0}
                            suffix="ms"
                            prefix={<MonitorOutlined style={{ color: '#722ed1' }} />}
                            valueStyle={{ color: '#722ed1' }}
                          />
                        </Col>
                      </Row>
                    </Card>
                  </>
                ) : (
                  <Card>
                    <div style={{ textAlign: 'center', padding: '60px', color: '#999' }}>
                      <MonitorOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                      <div>无法获取性能指标数据</div>
                    </div>
                  </Card>
                )}
              </div>
            ),
          },
          {
            key: 'logs',
            label: (
              <span>
                <DatabaseOutlined />
                系统日志
              </span>
            ),
            children: (
              <Card title="系统日志">
                {logs.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '60px', color: '#999' }}>
                    <DatabaseOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                    <div>暂无系统日志数据</div>
                  </div>
                ) : (
                  <Table
                    dataSource={logs}
                    columns={logColumns}
                    rowKey="id"
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                    }}
                    scroll={{ y: 400 }}
                    size="small"
                  />
                )}
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
};

export default SystemMonitor;