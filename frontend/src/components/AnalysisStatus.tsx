import React, { useState, useEffect } from 'react';
import { Card, Progress, Alert, Button, Spin, Tag, Collapse, Tabs } from 'antd';
import { ReloadOutlined, EyeOutlined, FileTextOutlined } from '@ant-design/icons';
import { ApiService, type AnalysisStatus as Status } from '../services/api';
import ReportView from './ReportView';

interface AnalysisStatusProps {
  runId: string;
  onComplete?: (result: any) => void;
}

const AnalysisStatus: React.FC<AnalysisStatusProps> = ({ runId, onComplete }) => {
  const [status, setStatus] = useState<Status | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await ApiService.getAnalysisStatus(runId);
      if (response.success && response.data) {
        setStatus(response.data);
        
        // 如果分析完成，获取结果
        if (response.data.status === 'completed') {
          const resultResponse = await ApiService.getAnalysisResult(runId);
          if (resultResponse.success && resultResponse.data) {
            // Extract the actual result from the nested structure
            const actualResult = resultResponse.data.result || resultResponse.data;
            // Add ticker and task info from status response if not present in result
            if (!actualResult.ticker && (response.data as any).ticker) {
              actualResult.ticker = (response.data as any).ticker;
            }
            if (!actualResult.task_id && resultResponse.data.task_id) {
              actualResult.task_id = resultResponse.data.task_id;
            }
            setResult(actualResult);
            onComplete?.(actualResult);
          }
        }
      }
    } catch (error) {
      console.error('Fetch status error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    
    // 如果任务还在运行，定期轮询状态
    let interval: number;
    if (status?.status === 'running') {
      interval = setInterval(fetchStatus, 3000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [runId, status?.status]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'processing';
      case 'completed': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getProgress = () => {
    if (!status) return 0;
    
    // 如果有进度信息，尝试从中解析进度
    if (status.progress && typeof status.progress === 'string') {
      // 尝试从进度文本中提取百分比
      const progressMatch = status.progress.match(/(\d+)%/);
      if (progressMatch) {
        return parseInt(progressMatch[1]);
      }
      
      // 根据关键词估算进度
      const progress = status.progress.toLowerCase();
      if (progress.includes('开始') || progress.includes('初始化')) return 10;
      if (progress.includes('数据收集') || progress.includes('market_data')) return 20;
      if (progress.includes('技术分析') || progress.includes('technical')) return 30;
      if (progress.includes('基本面') || progress.includes('fundamental')) return 40;
      if (progress.includes('情感分析') || progress.includes('sentiment')) return 50;
      if (progress.includes('估值') || progress.includes('valuation')) return 60;
      if (progress.includes('风险') || progress.includes('risk')) return 70;
      if (progress.includes('宏观') || progress.includes('macro')) return 80;
      if (progress.includes('投资组合') || progress.includes('portfolio')) return 90;
      if (progress.includes('完成') || progress.includes('结束')) return 100;
    }
    
    switch (status.status) {
      case 'running': return 50;
      case 'completed': return 100;
      case 'failed': return 0;
      default: return 0;
    }
  };

  return (
    <Card
      title={`分析任务 - ${runId}`}
      extra={
        <Button
          icon={<ReloadOutlined />}
          onClick={fetchStatus}
          loading={loading}
          size="small"
          className="secondary-button"
        >
          刷新
        </Button>
      }
      className="feature-card mb-4"
    >
      {status && (
        <>
          <div className="mb-4">
            <Tag color={getStatusColor(status.status)} className="mb-2">
              {status.status.toUpperCase()}
            </Tag>
            <Progress
              percent={getProgress()}
              status={status.status === 'failed' ? 'exception' : 'normal'}
              strokeColor={status.status === 'completed' ? '#52c41a' : undefined}
            />
          </div>

          {status.progress && (
            <Alert
              message="进度信息"
              description={status.progress}
              type="info"
              className="mb-4"
            />
          )}

          {status.status === 'completed' && result && (
            <Collapse
              items={[
                {
                  key: '1',
                  label: (
                    <span>
                      <EyeOutlined /> 查看分析结果
                    </span>
                  ),
                  children: (
                    <Tabs
                      defaultActiveKey="report"
                      items={[
                        {
                          key: 'report',
                          label: (
                            <span>
                              <FileTextOutlined /> 投资分析报告
                            </span>
                          ),
                          children: <ReportView data={result} />,
                        },
                        {
                          key: 'json',
                          label: (
                            <span>
                              <EyeOutlined /> 原始数据 (JSON)
                            </span>
                          ),
                          children: (
                            <pre style={{ 
                              background: '#f5f5f5', 
                              padding: '16px', 
                              borderRadius: '4px',
                              maxHeight: '400px',
                              overflow: 'auto'
                            }}>
                              {JSON.stringify(result, null, 2)}
                            </pre>
                          ),
                        },
                      ]}
                    />
                  ),
                },
              ]}
            />
          )}

          {status.status === 'failed' && (
            <Alert
              message="分析失败"
              description="任务执行过程中发生错误，请检查日志或重新启动分析。"
              type="error"
              showIcon
            />
          )}
        </>
      )}

      {!status && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin size="large" />
          <p>正在获取任务状态...</p>
        </div>
      )}
    </Card>
  );
};

export default AnalysisStatus;