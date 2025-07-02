import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Space,
  Descriptions
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  EyeOutlined,
  ReloadOutlined,
  RobotOutlined
} from '@ant-design/icons';
import {
  ApiService,
  type ManagedAgent,
  type AgentCreateRequest,
  type AgentUpdateRequest
} from '../services/api';
import moment from 'moment';

const { Option } = Select;
const { TextArea } = Input;

const AgentManagement: React.FC = () => {
  const [agents, setAgents] = useState<ManagedAgent[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<ManagedAgent | null>(null);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const response = await ApiService.getManagedAgents();
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

  const handleCreateAgent = async (values: AgentCreateRequest) => {
    try {
      const response = await ApiService.createAgent(values);
      if (response.success) {
        message.success('Agent创建成功');
        setCreateModalVisible(false);
        createForm.resetFields();
        fetchAgents();
      } else {
        message.error(response.message || '创建Agent失败');
      }
    } catch (error) {
      message.error('创建Agent失败');
      console.error('Create agent error:', error);
    }
  };

  const handleUpdateAgent = async (values: AgentUpdateRequest) => {
    if (!selectedAgent) return;
    
    try {
      const response = await ApiService.updateAgent(selectedAgent.name, values);
      if (response.success) {
        message.success('Agent更新成功');
        setEditModalVisible(false);
        editForm.resetFields();
        fetchAgents();
      } else {
        message.error(response.message || '更新Agent失败');
      }
    } catch (error) {
      message.error('更新Agent失败');
      console.error('Update agent error:', error);
    }
  };

  const showEditModal = (agent: ManagedAgent) => {
    setSelectedAgent(agent);
    editForm.setFieldsValue({
      display_name: agent.display_name,
      description: agent.description,
      status: agent.status,
      config: JSON.stringify(agent.config, null, 2)
    });
    setEditModalVisible(true);
  };

  const showDetailModal = (agent: ManagedAgent) => {
    setSelectedAgent(agent);
    setDetailModalVisible(true);
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'maintenance': return 'warning';
      default: return 'default';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'analysis': return 'blue';
      case 'trading': return 'green';
      case 'risk': return 'red';
      default: return 'default';
    }
  };

  const columns = [
    {
      title: 'Agent名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text: string) => (
        <code style={{ fontSize: '12px' }}>{text}</code>
      ),
    },
    {
      title: '显示名称',
      dataIndex: 'display_name',
      key: 'display_name',
      width: 200,
    },
    {
      title: '类型',
      dataIndex: 'agent_type',
      key: 'agent_type',
      width: 100,
      render: (type: string) => (
        <Tag color={getTypeColor(type)}>
          {type?.toUpperCase() || 'UNKNOWN'}
        </Tag>
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
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      render: (text: string) => text || '-',
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
      width: 200,
      render: (_: any, record: ManagedAgent) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => showDetailModal(record)}
            size="small"
          >
            详情
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => showEditModal(record)}
            size="small"
          >
            编辑
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
            <RobotOutlined /> Agent管理
          </span>
        }
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
              size="small"
            >
              创建Agent
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchAgents}
              loading={loading}
              size="small"
            >
              刷新
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={agents}
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

      {/* 创建Agent模态框 */}
      <Modal
        title="创建新Agent"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateAgent}
        >
          <Form.Item
            name="name"
            label="Agent名称"
            rules={[
              { required: true, message: '请输入Agent名称' },
              { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: '名称只能包含字母、数字和下划线，且不能以数字开头' }
            ]}
          >
            <Input placeholder="agent_name" />
          </Form.Item>

          <Form.Item
            name="display_name"
            label="显示名称"
            rules={[{ required: true, message: '请输入显示名称' }]}
          >
            <Input placeholder="Agent显示名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="Agent描述信息" />
          </Form.Item>

          <Form.Item
            name="agent_type"
            label="Agent类型"
            rules={[{ required: true, message: '请选择Agent类型' }]}
          >
            <Select>
              <Option value="analysis">分析</Option>
              <Option value="trading">交易</Option>
              <Option value="risk">风险管理</Option>
              <Option value="sentiment">情感分析</Option>
              <Option value="macro">宏观分析</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
            initialValue="active"
          >
            <Select>
              <Option value="active">激活</Option>
              <Option value="inactive">停用</Option>
              <Option value="maintenance">维护中</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
              <Button onClick={() => {
                setCreateModalVisible(false);
                createForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑Agent模态框 */}
      <Modal
        title={`编辑Agent - ${selectedAgent?.name}`}
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          editForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdateAgent}
        >
          <Form.Item
            name="display_name"
            label="显示名称"
          >
            <Input placeholder="Agent显示名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="Agent描述信息" />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
          >
            <Select>
              <Option value="active">激活</Option>
              <Option value="inactive">停用</Option>
              <Option value="maintenance">维护中</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="config"
            label="配置信息"
          >
            <TextArea rows={6} placeholder="JSON格式的配置信息" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                更新
              </Button>
              <Button onClick={() => {
                setEditModalVisible(false);
                editForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Agent详情模态框 */}
      <Modal
        title={`Agent详情 - ${selectedAgent?.name}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedAgent && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="Agent名称">
              <code>{selectedAgent.name}</code>
            </Descriptions.Item>
            <Descriptions.Item label="显示名称">
              {selectedAgent.display_name}
            </Descriptions.Item>
            <Descriptions.Item label="类型">
              <Tag color={getTypeColor(selectedAgent.agent_type)}>
                {selectedAgent.agent_type?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={getStatusColor(selectedAgent.status)}>
                {selectedAgent.status?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="描述">
              {selectedAgent.description || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="配置信息">
              <pre style={{ background: '#f5f5f5', padding: '8px', fontSize: '12px' }}>
                {selectedAgent.config ? JSON.stringify(selectedAgent.config, null, 2) : '暂无配置'}
              </pre>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedAgent.created_at 
                ? moment(selectedAgent.created_at).format('YYYY-MM-DD HH:mm:ss')
                : '-'
              }
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {selectedAgent.updated_at 
                ? moment(selectedAgent.updated_at).format('YYYY-MM-DD HH:mm:ss')
                : '-'
              }
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </>
  );
};

export default AgentManagement;