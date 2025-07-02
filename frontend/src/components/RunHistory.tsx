import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, message, Modal, Descriptions } from 'antd';
import { ReloadOutlined, EyeOutlined, HistoryOutlined } from '@ant-design/icons';
import { ApiService, type Run } from '../services/api';
import moment from 'moment';

const RunHistory: React.FC = () => {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const runs = await ApiService.getRuns(20);
      setRuns(runs || []);
    } catch (error) {
      message.error('获取运行历史失败');
      console.error('Fetch runs error:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewRunDetails = async (run: Run) => {
    try {
      const runDetails = await ApiService.getRun(run.run_id);
      setSelectedRun(runDetails);
      setModalVisible(true);
    } catch (error) {
      message.error('获取运行详情失败');
      console.error('Fetch run details error:', error);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed': return 'success';
      case 'running': return 'processing';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const columns = [
    {
      title: 'Run ID',
      dataIndex: 'run_id',
      key: 'run_id',
      width: 200,
      render: (text: string) => (
        <code style={{ fontSize: '12px' }}>{text}</code>
      ),
    },
    {
      title: '股票代码',
      dataIndex: 'ticker',
      key: 'ticker',
      width: 100,
      render: (text: string) => text || '-',
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
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 150,
      render: (start_time: string) => 
        start_time ? moment(start_time).format('MM-DD HH:mm:ss') : '-',
    },
    {
      title: 'Agent数量',
      dataIndex: 'agents_executed',
      key: 'agents_count',
      width: 100,
      render: (agents: string[]) => agents?.length || 0,
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: Run) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => viewRunDetails(record)}
          size="small"
        >
          查看详情
        </Button>
      ),
    },
  ];

  return (
    <>
      <Card
        title={
          <span>
            <HistoryOutlined /> 运行历史
          </span>
        }
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchRuns}
            loading={loading}
            size="small"
          >
            刷新
          </Button>
        }
      >
        <Table
          dataSource={runs}
          columns={columns}
          rowKey="run_id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: false,
            showQuickJumper: true,
          }}
          size="small"
        />
      </Card>

      <Modal
        title={`运行详情 - ${selectedRun?.run_id}`}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedRun && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="Run ID">
              <code>{selectedRun.run_id}</code>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={getStatusColor(selectedRun.status)}>
                {selectedRun.status?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="股票代码">
              {selectedRun.ticker || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="开始时间">
              {selectedRun.start_time 
                ? moment(selectedRun.start_time).format('YYYY-MM-DD HH:mm:ss')
                : '-'
              }
            </Descriptions.Item>
            <Descriptions.Item label="结束时间">
              {selectedRun.end_time 
                ? moment(selectedRun.end_time).format('YYYY-MM-DD HH:mm:ss')
                : '-'
              }
            </Descriptions.Item>
            <Descriptions.Item label="执行的Agent">
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {selectedRun.agents_executed?.map((agent) => (
                  <Tag key={agent} size="small">{agent}</Tag>
                ))}
              </div>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </>
  );
};

export default RunHistory;