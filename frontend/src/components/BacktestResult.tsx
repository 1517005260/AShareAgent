import React, { useState } from 'react';
import { Card, Typography, Space, Row, Col, Statistic, Table, Image, message, Spin, Alert } from 'antd';
import { 
  TrophyOutlined, 
  FallOutlined, 
  RiseOutlined, 
  DollarCircleOutlined,
  PictureOutlined,
  BarChartOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface BacktestResultProps {
  result: any;
}

const BacktestResult: React.FC<BacktestResultProps> = ({ result }) => {
  const [imageLoading, setImageLoading] = useState(true);
  const [imageError, setImageError] = useState(false);

  if (!result || !result.result) {
    return (
      <Alert 
        message="无回测结果数据" 
        description="请先运行回测任务"
        type="warning" 
        showIcon 
      />
    );
  }

  const data = result.result;
  const performanceMetrics = data.performance_metrics || {};
  const riskMetrics = data.risk_metrics || {};
  const trades = data.trades || [];
  const plotUrl = data.plot_url;

  // 交易记录表格列定义
  const tradeColumns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
    },
    {
      title: '动作',
      dataIndex: 'action',
      key: 'action',
      render: (action: string) => (
        <Text type={action === 'buy' ? 'danger' : action === 'sell' ? 'success' : undefined}>
          {action === 'buy' ? '买入' : action === 'sell' ? '卖出' : '持有'}
        </Text>
      ),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${price?.toFixed(2) || 'N/A'}`,
    },
    {
      title: '总金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (amount: number) => `¥${amount?.toFixed(2) || 'N/A'}`,
    },
  ];

  const formatPercentage = (value: number | null) => {
    if (value === null || value === undefined) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatNumber = (value: number | null, decimals: number = 2) => {
    if (value === null || value === undefined) return 'N/A';
    return value.toFixed(decimals);
  };

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>
        <BarChartOutlined /> 回测结果 - {result.ticker}
      </Title>
      
      <Text type="secondary" style={{ marginBottom: '24px', display: 'block' }}>
        回测周期: {result.start_date} 至 {result.end_date}
      </Text>

      {/* 回测图表 */}
      {plotUrl && (
        <Card 
          title={
            <Space>
              <PictureOutlined />
              回测图表
            </Space>
          }
          style={{ marginBottom: '24px' }}
        >
          <div style={{ textAlign: 'center' }}>
            {imageLoading && <Spin size="large" />}
            <Image
              src={`http://localhost:8000${plotUrl}`}
              alt="回测图表"
              style={{ 
                maxWidth: '100%',
                display: imageLoading ? 'none' : 'block'
              }}
              onLoad={() => setImageLoading(false)}
              onError={() => {
                setImageLoading(false);
                setImageError(true);
                message.error('图表加载失败');
              }}
              preview={{
                mask: '点击查看大图'
              }}
            />
            {imageError && (
              <Alert 
                message="图表加载失败" 
                description="请检查图表文件是否存在"
                type="error" 
                showIcon 
                style={{ margin: '20px 0' }}
              />
            )}
          </div>
        </Card>
      )}

      {/* 性能指标 */}
      <Card title="性能指标" style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="总收益率"
              value={formatPercentage(performanceMetrics.total_return)}
              prefix={<RiseOutlined />}
              valueStyle={{ color: (performanceMetrics.total_return || 0) >= 0 ? '#cf1322' : '#3f8600' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="年化收益率"
              value={formatPercentage(performanceMetrics.annualized_return)}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: (performanceMetrics.annualized_return || 0) >= 0 ? '#cf1322' : '#3f8600' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="夏普比率"
              value={formatNumber(performanceMetrics.sharpe_ratio)}
              prefix={<DollarCircleOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="最大回撤"
              value={formatPercentage(performanceMetrics.max_drawdown)}
              prefix={<FallOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
        </Row>
      </Card>

      {/* 风险指标 */}
      <Card title="风险指标" style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="VaR (95%)"
              value={formatPercentage(riskMetrics.var_95)}
              suffix=""
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="预期亏损"
              value={formatPercentage(riskMetrics.expected_shortfall)}
              suffix=""
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Beta系数"
              value={formatNumber(riskMetrics.beta)}
              suffix=""
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Alpha系数"
              value={formatNumber(riskMetrics.alpha)}
              suffix=""
            />
          </Col>
        </Row>
      </Card>

      {/* 交易记录 */}
      {trades.length > 0 && (
        <Card title="交易记录">
          <Table
            dataSource={trades.map((trade: any, index: number) => ({ ...trade, key: index }))}
            columns={tradeColumns}
            pagination={{ pageSize: 10 }}
            size="middle"
            scroll={{ x: true }}
          />
        </Card>
      )}
    </div>
  );
};

export default BacktestResult;