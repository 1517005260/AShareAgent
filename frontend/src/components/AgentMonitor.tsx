import React, { useState, useEffect } from 'react';
import { Card, List, Tag, Collapse, Button, Spin, message } from 'antd';
import { ReloadOutlined, RobotOutlined } from '@ant-design/icons';
import { ApiService, type Agent } from '../services/api';

const AgentMonitor: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [agentDetails, setAgentDetails] = useState<any>({});

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const response = await ApiService.getAgents();
      if (response.success && response.data) {
        setAgents(response.data);
      }
    } catch (error) {
      message.error('获取Agent列表失败');
      console.error('Fetch agents error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAgentDetails = async (agentName: string) => {
    try {
      const [inputRes, outputRes, reasoningRes] = await Promise.all([
        ApiService.getAgentLatestInput(agentName).catch(() => ({ success: false, data: null })),
        ApiService.getAgentLatestOutput(agentName).catch(() => ({ success: false, data: null })),
        ApiService.getAgent(agentName).catch(() => ({ success: false, data: null }))
      ]);

      setAgentDetails({
        ...agentDetails,
        [agentName]: {
          input: inputRes.success ? inputRes.data : null,
          output: outputRes.success ? outputRes.data : null,
          reasoning: reasoningRes.success ? reasoningRes.data : null
        }
      });
    } catch (error) {
      console.error('Fetch agent details error:', error);
    }
  };

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 5000); // 每5秒刷新
    return () => clearInterval(interval);
  }, []);

  const handleAgentClick = (agentName: string) => {
    setSelectedAgent(agentName);
    if (!agentDetails[agentName]) {
      fetchAgentDetails(agentName);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
      case 'running': return 'success';
      case 'idle': return 'default';
      case 'error': return 'error';
      default: return 'processing';
    }
  };

  return (
    <Card
      title="Agent监控"
      extra={
        <Button
          icon={<ReloadOutlined />}
          onClick={fetchAgents}
          loading={loading}
          size="small"
        >
          刷新
        </Button>
      }
    >
      {loading && agents.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin size="large" />
          <p>正在加载Agent信息...</p>
        </div>
      ) : (
        <List
          dataSource={agents}
          renderItem={(agent) => (
            <List.Item
              key={agent.name}
              style={{ cursor: 'pointer' }}
              onClick={() => handleAgentClick(agent.name)}
            >
              <List.Item.Meta
                avatar={<RobotOutlined style={{ fontSize: '24px', color: '#1890ff' }} />}
                title={
                  <span>
                    {agent.name}
                    <Tag color={getStatusColor(agent.status)} style={{ marginLeft: 8 }}>
                      {agent.status || 'Unknown'}
                    </Tag>
                  </span>
                }
                description={`Agent状态监控 - 点击查看详情`}
              />
            </List.Item>
          )}
        />
      )}

      {selectedAgent && agentDetails[selectedAgent] && (
        <Card
          title={`${selectedAgent} 详情`}
          size="small"
          style={{ marginTop: 16 }}
        >
          <Collapse
            items={[
              {
                key: 'input',
                label: '最新输入',
                children: agentDetails[selectedAgent].input ? (
                  <pre style={{ 
                    background: '#f5f5f5', 
                    padding: '12px', 
                    borderRadius: '4px',
                    maxHeight: '200px',
                    overflow: 'auto',
                    fontSize: '12px'
                  }}>
                    {JSON.stringify(agentDetails[selectedAgent].input, null, 2)}
                  </pre>
                ) : (
                  <p>暂无输入数据</p>
                ),
              },
              {
                key: 'output',
                label: '最新输出',
                children: agentDetails[selectedAgent].output ? (
                  <pre style={{ 
                    background: '#f5f5f5', 
                    padding: '12px', 
                    borderRadius: '4px',
                    maxHeight: '200px',
                    overflow: 'auto',
                    fontSize: '12px'
                  }}>
                    {JSON.stringify(agentDetails[selectedAgent].output, null, 2)}
                  </pre>
                ) : (
                  <p>暂无输出数据</p>
                ),
              },
              {
                key: 'reasoning',
                label: '推理信息',
                children: agentDetails[selectedAgent].reasoning ? (
                  <pre style={{ 
                    background: '#f5f5f5', 
                    padding: '12px', 
                    borderRadius: '4px',
                    maxHeight: '200px',
                    overflow: 'auto',
                    fontSize: '12px'
                  }}>
                    {JSON.stringify(agentDetails[selectedAgent].reasoning, null, 2)}
                  </pre>
                ) : (
                  <p>暂无推理数据</p>
                ),
              },
            ]}
          />
        </Card>
      )}
    </Card>
  );
};

export default AgentMonitor;