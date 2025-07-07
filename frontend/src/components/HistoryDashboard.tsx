import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tag,
  Button,
  message,
  Space,
  Modal,
  Input,
  Select,
  Descriptions,
  Typography,
  Row,
  Col,
  Badge,
  Tabs
} from 'antd';
import {
  EyeOutlined,
  ReloadOutlined,
  SearchOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  BarChartOutlined,
  TrophyOutlined,
  PictureOutlined
} from '@ant-design/icons';
import {
  ApiService,
  type AgentDecision
} from '../services/api';
import moment from 'moment';

const { Option } = Select;
const { Search } = Input;
const { Text, Paragraph } = Typography;
// Removed unused TabPane import

const HistoryDashboard: React.FC = () => {
  const [decisions, setDecisions] = useState<AgentDecision[]>([]);
  const [analysisHistory, setAnalysisHistory] = useState<any[]>([]);
  const [backtestHistory, setBacktestHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('decisions');
  const [decisionDetailModalVisible, setDecisionDetailModalVisible] = useState(false);
  const [formattedModalVisible, setFormattedModalVisible] = useState(false);
  const [analysisDetailModalVisible, setAnalysisDetailModalVisible] = useState(false);
  const [backtestDetailModalVisible, setBacktestDetailModalVisible] = useState(false);
  const [chartModalVisible, setChartModalVisible] = useState(false);
  const [selectedDecision, setSelectedDecision] = useState<AgentDecision | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<any>(null);
  const [selectedBacktest, setSelectedBacktest] = useState<any>(null);
  const [formattedText, setFormattedText] = useState<string>('');
  const [chartImageUrl, setChartImageUrl] = useState<string>('');
  const [filters, setFilters] = useState({
    run_id: '',
    agent_name: '',
    ticker: '',
    limit: 50
  });


  const fetchDecisions = async () => {
    setLoading(true);
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== '' && v !== undefined)
      );
      
      const response = await ApiService.getAgentDecisions(params);
      if (response.success && response.data) {
        setDecisions(response.data);
      }
    } catch (error) {
      message.error('获取决策历史失败');
      console.error('Fetch decisions error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalysisHistory = async () => {
    setLoading(true);
    try {
      const response = await ApiService.getAnalysisHistory({ limit: 50 });
      if (response.success && response.data) {
        setAnalysisHistory(response.data.tasks || []);
      }
    } catch (error) {
      message.error('获取分析历史失败');
      console.error('Fetch analysis history error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBacktestHistory = async () => {
    setLoading(true);
    try {
      const response = await ApiService.getBacktestHistory({ limit: 50 });
      if (response.success && response.data) {
        setBacktestHistory(response.data.tasks || []);
      }
    } catch (error) {
      message.error('获取回测历史失败');
      console.error('Fetch backtest history error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrentTabData = () => {
    switch (activeTab) {
      case 'decisions':
        fetchDecisions();
        break;
      case 'analysis':
        fetchAnalysisHistory();
        break;
      case 'backtest':
        fetchBacktestHistory();
        break;
    }
  };


  const showDecisionDetailModal = (decision: AgentDecision) => {
    setSelectedDecision(decision);
    setDecisionDetailModalVisible(true);
  };

  const showAnalysisDetailModal = (analysis: any) => {
    setSelectedAnalysis(analysis);
    setAnalysisDetailModalVisible(true);
  };

  const showBacktestDetailModal = (backtest: any) => {
    setSelectedBacktest(backtest);
    setBacktestDetailModalVisible(true);
  };

  const showFormattedDecision = async (runId: string) => {
    try {
      const response = await ApiService.getFormattedDecision(runId);
      if (response.success && response.data) {
        setFormattedText(response.data);
        setFormattedModalVisible(true);
      } else {
        message.error('获取格式化决策失败');
      }
    } catch (error) {
      message.error('获取格式化决策失败');
      console.error('Get formatted decision error:', error);
    }
  };

  const viewAnalysisResult = async (taskId: string) => {
    try {
      const response = await ApiService.getAnalysisResult(taskId);
      if (response.success && response.data) {
        setFormattedText(JSON.stringify(response.data.result, null, 2));
        setFormattedModalVisible(true);
      } else {
        message.error('获取分析结果失败');
      }
    } catch (error) {
      message.error('获取分析结果失败');
      console.error('Get analysis result error:', error);
    }
  };

  const viewBacktestResult = async (taskId: string) => {
    try {
      const response = await ApiService.getBacktestResult(taskId);
      if (response.success && response.data) {
        setFormattedText(JSON.stringify(response.data.result, null, 2));
        setFormattedModalVisible(true);
      } else {
        message.error('获取回测结果失败');
      }
    } catch (error) {
      message.error('获取回测结果失败');
      console.error('Get backtest result error:', error);
    }
  };

  const viewBacktestChart = async (taskId: string) => {
    try {
      const response = await ApiService.getBacktestResult(taskId);
      if (response.success && response.data && response.data.result) {
        const plotPath = response.data.result.plot_path;
        if (plotPath) {
          // 假设后端在8000端口，plots目录可通过 /plots 路径访问
          const filename = plotPath.split('/').pop(); // 获取文件名
          const imageUrl = `http://localhost:8000/plots/${filename}`;
          setChartImageUrl(imageUrl);
          setChartModalVisible(true);
        } else {
          message.warning('该回测任务没有生成图表');
        }
      } else {
        message.error('获取回测结果失败');
      }
    } catch (error) {
      message.error('获取回测结果失败');
      console.error('Get backtest chart error:', error);
    }
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const clearFilters = () => {
    setFilters({
      run_id: '',
      agent_name: '',
      ticker: '',
      limit: 50
    });
  };

  useEffect(() => {
    fetchCurrentTabData();
  }, [activeTab]);

  useEffect(() => {
    fetchDecisions();
  }, []);


  const getDecisionTypeColor = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'buy': return 'success';
      case 'sell': return 'error';
      case 'hold': return 'warning';
      case 'analysis': return 'blue';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed': return 'success';
      case 'running': return 'processing';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };


  const decisionColumns = [
    {
      title: 'Run ID',
      dataIndex: 'run_id',
      key: 'run_id',
      width: 150,
      render: (text: string) => (
        <code style={{ fontSize: '11px' }}>{text.substring(0, 8)}...</code>
      ),
    },
    {
      title: 'Agent',
      dataIndex: 'agent_display_name',
      key: 'agent_display_name',
      width: 120,
      render: (text: string, record: AgentDecision) => text || record.agent_name,
    },
    {
      title: '股票代码',
      dataIndex: 'ticker',
      key: 'ticker',
      width: 100,
    },
    {
      title: '决策类型',
      dataIndex: 'decision_type',
      key: 'decision_type',
      width: 100,
      render: (type: string) => (
        <Tag color={getDecisionTypeColor(type)}>
          {type?.toUpperCase() || 'UNKNOWN'}
        </Tag>
      ),
    },
    {
      title: '置信度',
      dataIndex: 'confidence_score',
      key: 'confidence_score',
      width: 100,
      render: (score: number) => {
        if (score === null || score === undefined) return '-';
        if (typeof score === 'number') {
          if (score >= 0 && score <= 1) {
            return `${(score * 100).toFixed(1)}%`;
          } else if (score > 1 && score <= 100) {
            return `${score.toFixed(1)}%`;
          }
        }
        return score ? score.toString() : '-';
      },
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (timestamp: string) => 
        timestamp ? moment(timestamp).format('MM-DD HH:mm:ss') : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: any, record: AgentDecision) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => showDecisionDetailModal(record)}
            size="small"
          >
            详情
          </Button>
          <Button
            type="link"
            icon={<FileTextOutlined />}
            onClick={() => showFormattedDecision(record.run_id)}
            size="small"
          >
            格式化视图
          </Button>
        </Space>
      ),
    },
  ];

  const analysisColumns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 150,
      render: (text: string) => (
        <code style={{ fontSize: '11px' }}>{text.substring(0, 8)}...</code>
      ),
    },
    {
      title: '股票代码',
      dataIndex: 'ticker',
      key: 'ticker',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status?.toUpperCase() || 'UNKNOWN'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (timestamp: string) => 
        timestamp ? moment(timestamp).format('MM-DD HH:mm:ss') : '-',
    },
    {
      title: '完成时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 150,
      render: (timestamp: string) => 
        timestamp ? moment(timestamp).format('MM-DD HH:mm:ss') : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => showAnalysisDetailModal(record)}
            size="small"
          >
            详情
          </Button>
          {record.status === 'completed' && (
            <Button
              type="link"
              icon={<FileTextOutlined />}
              onClick={() => viewAnalysisResult(record.task_id)}
              size="small"
            >
              查看报告
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const backtestColumns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 150,
      render: (text: string) => (
        <code style={{ fontSize: '11px' }}>{text.substring(0, 8)}...</code>
      ),
    },
    {
      title: '股票代码',
      dataIndex: 'ticker',
      key: 'ticker',
      width: 100,
    },
    {
      title: '回测期间',
      key: 'period',
      width: 200,
      render: (_: any, record: any) => (
        <span>{record.start_date} 至 {record.end_date}</span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status?.toUpperCase() || 'UNKNOWN'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (timestamp: string) => 
        timestamp ? moment(timestamp).format('MM-DD HH:mm:ss') : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 250,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => showBacktestDetailModal(record)}
            size="small"
          >
            详情
          </Button>
          {record.status === 'completed' && (
            <>
              <Button
                type="link"
                icon={<BarChartOutlined />}
                onClick={() => viewBacktestResult(record.task_id)}
                size="small"
              >
                查看结果
              </Button>
              <Button
                type="link"
                icon={<PictureOutlined />}
                onClick={() => viewBacktestChart(record.task_id)}
                size="small"
              >
                查看图表
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <>
      <Card
        title={
          <Space>
            <DatabaseOutlined />
            历史记录
          </Space>
        }
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchCurrentTabData}
            loading={loading}
            size="small"
          >
            刷新
          </Button>
        }
      >
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: 'decisions',
              label: (
                <Space>
                  <TrophyOutlined />
                  <span>Agent决策历史</span>
                  <Badge count={decisions.length} />
                </Space>
              ),
              children: (
                <div>
                  {/* 过滤器 */}
                  <Row gutter={16} style={{ marginBottom: 16 }}>
                    <Col span={6}>
                      <Search
                        placeholder="Run ID"
                        value={filters.run_id}
                        onChange={(e) => handleFilterChange('run_id', e.target.value)}
                        onSearch={fetchDecisions}
                        size="small"
                      />
                    </Col>
                    <Col span={6}>
                      <Input
                        placeholder="Agent名称"
                        value={filters.agent_name}
                        onChange={(e) => handleFilterChange('agent_name', e.target.value)}
                        size="small"
                      />
                    </Col>
                    <Col span={4}>
                      <Input
                        placeholder="股票代码"
                        value={filters.ticker}
                        onChange={(e) => handleFilterChange('ticker', e.target.value)}
                        size="small"
                      />
                    </Col>
                    <Col span={4}>
                      <Select
                        placeholder="数量限制"
                        value={filters.limit}
                        onChange={(value) => handleFilterChange('limit', value)}
                        size="small"
                        style={{ width: '100%' }}
                      >
                        <Option value={20}>20</Option>
                        <Option value={50}>50</Option>
                        <Option value={100}>100</Option>
                        <Option value={200}>200</Option>
                      </Select>
                    </Col>
                    <Col span={4}>
                      <Space>
                        <Button
                          type="primary"
                          icon={<SearchOutlined />}
                          onClick={fetchDecisions}
                          size="small"
                        >
                          搜索
                        </Button>
                        <Button onClick={clearFilters} size="small">
                          清空
                        </Button>
                      </Space>
                    </Col>
                  </Row>

                  <Table
                    dataSource={decisions}
                    columns={decisionColumns}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: false,
                      showQuickJumper: true,
                    }}
                    size="small"
                  />
                </div>
              )
            },
            {
              key: 'analysis',
              label: (
                <Space>
                  <FileTextOutlined />
                  <span>股票分析历史</span>
                  <Badge count={analysisHistory.length} />
                </Space>
              ),
              children: (
                <Table
                  dataSource={analysisHistory}
                  columns={analysisColumns}
                  rowKey="task_id"
                  loading={loading}
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: false,
                    showQuickJumper: true,
                  }}
                  size="small"
                />
              )
            },
            {
              key: 'backtest',
              label: (
                <Space>
                  <BarChartOutlined />
                  <span>回测历史</span>
                  <Badge count={backtestHistory.length} />
                </Space>
              ),
              children: (
                <Table
                  dataSource={backtestHistory}
                  columns={backtestColumns}
                  rowKey="task_id"
                  loading={loading}
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: false,
                    showQuickJumper: true,
                  }}
                  size="small"
                />
              )
            }
          ]}
        />
      </Card>


      {/* 决策详情模态框 */}
      <Modal
        title={`决策详情`}
        open={decisionDetailModalVisible}
        onCancel={() => setDecisionDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDecisionDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedDecision && (
          <div>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Run ID">
                <code>{selectedDecision.run_id}</code>
              </Descriptions.Item>
              <Descriptions.Item label="Agent">
                {selectedDecision.agent_display_name || selectedDecision.agent_name}
              </Descriptions.Item>
              <Descriptions.Item label="股票代码">
                {selectedDecision.ticker}
              </Descriptions.Item>
              <Descriptions.Item label="决策类型">
                <Tag color={getDecisionTypeColor(selectedDecision.decision_type)}>
                  {selectedDecision.decision_type?.toUpperCase() || 'UNKNOWN'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="置信度">
                {(() => {
                  const score = selectedDecision.confidence_score;
                  if (score === null || score === undefined) return '-';
                  if (typeof score === 'number') {
                    if (score >= 0 && score <= 1) {
                      return `${(score * 100).toFixed(1)}%`;
                    } else if (score > 1 && score <= 100) {
                      return `${score.toFixed(1)}%`;
                    }
                  }
                  return score ? score.toString() : '-';
                })()}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {selectedDecision.created_at 
                  ? moment(selectedDecision.created_at).format('YYYY-MM-DD HH:mm:ss')
                  : '-'
                }
              </Descriptions.Item>
            </Descriptions>

            {selectedDecision.reasoning && (
              <div style={{ marginTop: 16 }}>
                <Text strong>推理过程:</Text>
                <Paragraph style={{ 
                  background: '#f5f5f5', 
                  padding: '12px', 
                  marginTop: 8,
                  whiteSpace: 'pre-wrap'
                }}>
                  {selectedDecision.reasoning}
                </Paragraph>
              </div>
            )}

            {selectedDecision.decision_data && (
              <div style={{ marginTop: 16 }}>
                <Text strong>决策数据:</Text>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: '12px', 
                  fontSize: '12px',
                  marginTop: 8,
                  overflow: 'auto',
                  maxHeight: '300px'
                }}>
                  {JSON.stringify(selectedDecision.decision_data, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* 分析详情模态框 */}
      <Modal
        title="分析任务详情"
        open={analysisDetailModalVisible}
        onCancel={() => setAnalysisDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setAnalysisDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedAnalysis && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="任务ID">
              <code>{selectedAnalysis.task_id}</code>
            </Descriptions.Item>
            <Descriptions.Item label="股票代码">
              {selectedAnalysis.ticker}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={getStatusColor(selectedAnalysis.status)}>
                {selectedAnalysis.status?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedAnalysis.created_at 
                ? moment(selectedAnalysis.created_at).format('YYYY-MM-DD HH:mm:ss')
                : '-'
              }
            </Descriptions.Item>
            <Descriptions.Item label="完成时间">
              {selectedAnalysis.completed_at 
                ? moment(selectedAnalysis.completed_at).format('YYYY-MM-DD HH:mm:ss')
                : '-'
              }
            </Descriptions.Item>
            {selectedAnalysis.error_message && (
              <Descriptions.Item label="错误信息">
                <Text type="danger">{selectedAnalysis.error_message}</Text>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>

      {/* 回测详情模态框 */}
      <Modal
        title="回测任务详情"
        open={backtestDetailModalVisible}
        onCancel={() => setBacktestDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setBacktestDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedBacktest && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="任务ID">
              <code>{selectedBacktest.task_id}</code>
            </Descriptions.Item>
            <Descriptions.Item label="股票代码">
              {selectedBacktest.ticker}
            </Descriptions.Item>
            <Descriptions.Item label="回测期间">
              {selectedBacktest.start_date} 至 {selectedBacktest.end_date}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={getStatusColor(selectedBacktest.status)}>
                {selectedBacktest.status?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedBacktest.created_at 
                ? moment(selectedBacktest.created_at).format('YYYY-MM-DD HH:mm:ss')
                : '-'
              }
            </Descriptions.Item>
            <Descriptions.Item label="完成时间">
              {selectedBacktest.completed_at 
                ? moment(selectedBacktest.completed_at).format('YYYY-MM-DD HH:mm:ss')
                : '-'
              }
            </Descriptions.Item>
            {selectedBacktest.parameters && (
              <Descriptions.Item label="参数配置">
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: '8px', 
                  fontSize: '12px',
                  maxHeight: '200px',
                  overflow: 'auto'
                }}>
                  {JSON.stringify(selectedBacktest.parameters, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
            {selectedBacktest.error_message && (
              <Descriptions.Item label="错误信息">
                <Text type="danger">{selectedBacktest.error_message}</Text>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>

      {/* 格式化决策显示模态框 */}
      <Modal
        title="格式化显示"
        open={formattedModalVisible}
        onCancel={() => setFormattedModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setFormattedModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={1200}
      >
        <pre style={{ 
          background: '#000', 
          color: '#00ff00',
          padding: '16px', 
          fontSize: '12px',
          overflow: 'auto',
          maxHeight: '600px',
          fontFamily: 'Consolas, Monaco, "Courier New", monospace'
        }}>
          {formattedText}
        </pre>
      </Modal>

      {/* 回测图表显示模态框 */}
      <Modal
        title="回测图表"
        open={chartModalVisible}
        onCancel={() => setChartModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setChartModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={1000}
        centered
      >
        {chartImageUrl && (
          <div style={{ textAlign: 'center' }}>
            <img 
              src={chartImageUrl} 
              alt="回测图表" 
              style={{ 
                maxWidth: '100%', 
                maxHeight: '70vh',
                objectFit: 'contain'
              }}
              onError={(e) => {
                message.error('图片加载失败，请检查图表是否存在');
                console.error('Chart image load error:', e);
              }}
            />
          </div>
        )}
      </Modal>
    </>
  );
};

export default HistoryDashboard;