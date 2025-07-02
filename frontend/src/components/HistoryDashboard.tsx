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
  Badge
} from 'antd';
import {
  EyeOutlined,
  ReloadOutlined,
  SearchOutlined,
  FileTextOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import {
  ApiService,
  type AgentDecision
} from '../services/api';
import moment from 'moment';

const { Option } = Select;
const { Search } = Input;
const { Text, Paragraph } = Typography;

const HistoryDashboard: React.FC = () => {
  const [decisions, setDecisions] = useState<AgentDecision[]>([]);
  const [loading, setLoading] = useState(false);
  const [decisionDetailModalVisible, setDecisionDetailModalVisible] = useState(false);
  const [formattedModalVisible, setFormattedModalVisible] = useState(false);
  const [selectedDecision, setSelectedDecision] = useState<AgentDecision | null>(null);
  const [formattedText, setFormattedText] = useState<string>('');
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


  const showDecisionDetailModal = (decision: AgentDecision) => {
    setSelectedDecision(decision);
    setDecisionDetailModalVisible(true);
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
      render: (score: number) => 
        score ? `${(score * 100).toFixed(1)}%` : '-',
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

  return (
    <>
      <Row gutter={16}>
        <Col span={24}>
          <Card
            title={
              <Space>
                <DatabaseOutlined />
                <span>Agent决策历史</span>
                <Badge count={decisions.length} />
              </Space>
            }
            extra={
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchDecisions}
                loading={loading}
                size="small"
              >
                刷新
              </Button>
            }
          >
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
          </Card>
        </Col>
      </Row>


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
                {selectedDecision.confidence_score 
                  ? `${(selectedDecision.confidence_score * 100).toFixed(1)}%`
                  : '-'
                }
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

      {/* 格式化决策显示模态框 */}
      <Modal
        title="格式化决策显示"
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
    </>
  );
};

export default HistoryDashboard;