import React, { useState, useEffect } from 'react';
import { Card, Progress, Typography, Space, Button, message, Spin, Alert } from 'antd';
import { ClockCircleOutlined, CheckCircleOutlined, ExclamationCircleOutlined, EyeOutlined } from '@ant-design/icons';
import ApiService, { type BacktestStatus as BacktestStatusType } from '../services/api';

const { Text, Title } = Typography;

interface BacktestStatusProps {
  runId: string;
  onComplete: (result: any) => void;
}

const BacktestStatus: React.FC<BacktestStatusProps> = ({ runId, onComplete }) => {
  const [status, setStatus] = useState<BacktestStatusType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const response = await ApiService.getBacktestStatus(runId);
      if (response.success && response.data) {
        setStatus(response.data);
        setError(null);
        
        // 如果任务完成，获取结果
        if (response.data.status === 'completed') {
          const resultResponse = await ApiService.getBacktestResult(runId);
          if (resultResponse.success && resultResponse.data) {
            onComplete(resultResponse.data);
          }
        }
      } else {
        setError(response.message || '获取状态失败');
      }
    } catch (error: any) {
      console.error('Get status error:', error);
      setError(error.response?.data?.message || '获取状态失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    // 如果任务正在运行，每5秒轮询一次状态
    const interval = setInterval(() => {
      if (status?.status === 'running' || status?.status === 'pending') {
        fetchStatus();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [runId, status?.status]);

  const getStatusIcon = () => {
    switch (status?.status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'running':
        return <ClockCircleOutlined style={{ color: '#1890ff' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
    }
  };

  const getStatusText = () => {
    switch (status?.status) {
      case 'completed':
        return '回测完成';
      case 'failed':
        return '回测失败';
      case 'running':
        return '回测进行中';
      case 'pending':
        return '等待开始';
      default:
        return '未知状态';
    }
  };

  const getProgress = () => {
    switch (status?.status) {
      case 'completed':
        return 100;
      case 'failed':
        return 0;
      case 'running':
        return 50; // 运行中显示50%
      case 'pending':
        return 10; // 等待中显示10%
      default:
        return 0;
    }
  };

  const handleViewResult = async () => {
    try {
      const response = await ApiService.getBacktestResult(runId);
      if (response.success && response.data) {
        onComplete(response.data);
      } else {
        message.error('获取结果失败');
      }
    } catch (error) {
      message.error('获取结果失败');
    }
  };

  if (loading) {
    return (
      <Card>
        <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '40px' }} />
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <Alert 
          message="获取回测状态失败" 
          description={error}
          type="error" 
          showIcon 
          action={
            <Button size="small" onClick={fetchStatus}>
              重试
            </Button>
          }
        />
      </Card>
    );
  }

  if (!status) {
    return (
      <Card>
        <Alert message="回测状态未找到" type="warning" showIcon />
      </Card>
    );
  }

  return (
    <Card 
      title={
        <Space>
          {getStatusIcon()}
          回测状态监控
        </Space>
      }
      extra={
        status.status === 'completed' && (
          <Button 
            type="primary" 
            icon={<EyeOutlined />}
            onClick={handleViewResult}
          >
            查看结果
          </Button>
        )
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Title level={4} style={{ margin: 0 }}>
            {status.ticker} - {getStatusText()}
          </Title>
          <Text type="secondary">
            任务ID: {status.task_id}
          </Text>
        </div>

        <div>
          <Text strong>回测周期: </Text>
          <Text>{status.start_date} 至 {status.end_date}</Text>
        </div>

        <Progress 
          percent={getProgress()} 
          status={status.status === 'failed' ? 'exception' : 'active'}
          strokeColor={
            status.status === 'completed' ? '#52c41a' : 
            status.status === 'failed' ? '#ff4d4f' : '#1890ff'
          }
        />

        <div>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div>
              <Text strong>创建时间: </Text>
              <Text>{new Date(status.created_at).toLocaleString()}</Text>
            </div>
            
            {status.started_at && (
              <div>
                <Text strong>开始时间: </Text>
                <Text>{new Date(status.started_at).toLocaleString()}</Text>
              </div>
            )}
            
            {status.completed_at && (
              <div>
                <Text strong>完成时间: </Text>
                <Text>{new Date(status.completed_at).toLocaleString()}</Text>
              </div>
            )}
          </Space>
        </div>

        {status.error_message && (
          <Alert
            message="错误信息"
            description={status.error_message}
            type="error"
            showIcon
          />
        )}

        {status.runtime_error && (
          <Alert
            message="运行时错误"
            description={status.runtime_error}
            type="error"
            showIcon
          />
        )}

        {status.is_running && (
          <Alert
            message="回测正在后台运行中"
            description="请耐心等待，系统会自动更新状态"
            type="info"
            showIcon
          />
        )}
      </Space>
    </Card>
  );
};

export default BacktestStatus;