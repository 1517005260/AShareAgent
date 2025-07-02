import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Modal,
  Input,
  Select,
  message,
  Space,
  Typography,
  Descriptions,
  Row,
  Col
} from 'antd';
import {
  EyeOutlined,
  ReloadOutlined,
  HistoryOutlined,
  SearchOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import {
  ApiService,
  type AgentDecision
} from '../services/api';
import moment from 'moment';

const { Option } = Select;
const { Search } = Input;
const { Text, Paragraph } = Typography;

const DecisionHistory: React.FC = () => {
  const [decisions, setDecisions] = useState<AgentDecision[]>([]);
  const [loading, setLoading] = useState(false);
  const [executionModalVisible, setExecutionModalVisible] = useState(false);
  const [formattedModalVisible, setFormattedModalVisible] = useState(false);
  const [selectedDecision, setSelectedDecision] = useState<AgentDecision | null>(null);
  const [formattedText, setFormattedText] = useState<string>('');
  const [executionLogs, setExecutionLogs] = useState<any[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
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

  const showExecutionHistory = async (decision: AgentDecision) => {
    setSelectedDecision(decision);
    setLogsLoading(true);
    setExecutionModalVisible(true);
    
    try {
      const response = await ApiService.getLogs({
        run_id: decision.run_id
      });
      if (response.success && response.data) {
        setExecutionLogs(response.data);
      } else {
        setExecutionLogs([]);
        message.error('获取执行记录失败');
      }
    } catch (error) {
      setExecutionLogs([]);
      message.error('获取执行记录失败');
      console.error('Get execution logs error:', error);
    } finally {
      setLogsLoading(false);
    }
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

  const columns = [
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
            icon={<HistoryOutlined />}
            onClick={() => showExecutionHistory(record)}
            size="small"
          >
            执行记录
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
      <Card
        title={
          <span>
            <HistoryOutlined /> Agent执行记录
          </span>
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
          columns={columns}
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

      {/* 完整执行记录模态框 */}
      <Modal
        title={`完整执行记录 - ${selectedDecision?.run_id || ''}`}
        open={executionModalVisible}
        onCancel={() => setExecutionModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setExecutionModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={1400}
      >
        {selectedDecision && (
          <div>
            {/* 基本信息 */}
            <Descriptions bordered column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Run ID">
                <code>{selectedDecision.run_id}</code>
              </Descriptions.Item>
              <Descriptions.Item label="股票代码">
                {selectedDecision.ticker}
              </Descriptions.Item>
              <Descriptions.Item label="Agent">
                {selectedDecision.agent_display_name || selectedDecision.agent_name}
              </Descriptions.Item>
              <Descriptions.Item label="决策类型">
                <Tag color={getDecisionTypeColor(selectedDecision.decision_type)}>
                  {selectedDecision.decision_type?.toUpperCase() || 'UNKNOWN'}
                </Tag>
              </Descriptions.Item>
            </Descriptions>

            {/* 分析控制台历史记录 */}
            <div style={{ marginTop: 16 }}>
              <Text strong>分析控制台历史记录:</Text>
              <div style={{
                background: '#1e1e1e',
                color: '#d4d4d4',
                padding: '16px',
                marginTop: 8,
                borderRadius: '4px',
                fontSize: '12px',
                fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                maxHeight: '600px',
                overflow: 'auto'
              }}>
                {logsLoading ? (
                  <div style={{ textAlign: 'center', padding: '20px', color: '#888' }}>
                    加载执行记录中...
                  </div>
                ) : executionLogs.length > 0 ? (
                  executionLogs.map((log, index) => (
                    <div key={index} style={{ marginBottom: '8px', borderBottom: '1px solid #333', paddingBottom: '8px' }}>
                      <div style={{ color: '#569cd6', fontSize: '11px', marginBottom: '4px' }}>
                        [{moment(log.timestamp || log.created_at).format('YYYY-MM-DD HH:mm:ss')}]
                        {log.agent_name && ` - ${log.agent_name}`}
                        {log.level && ` - ${log.level.toUpperCase()}`}
                      </div>
                      <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {log.message || log.content || JSON.stringify(log, null, 2)}
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ textAlign: 'center', padding: '20px', color: '#888' }}>
                    暂无执行记录
                  </div>
                )}
              </div>
            </div>
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

export default DecisionHistory;