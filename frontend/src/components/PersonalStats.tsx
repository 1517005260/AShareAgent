import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Select, Spin, Alert, Tag, Progress } from 'antd';
import {
  BarChartOutlined,
  TrophyOutlined,
  FundOutlined,
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  PieChartOutlined,
  LineChartOutlined
} from '@ant-design/icons';
import { ApiService } from '../services/api';

const { Option } = Select;

interface PersonalSummary {
  user_stats: {
    total_analyses: number;
    total_backtests: number;
    total_portfolios: number;
    success_rate: number;
    avg_return: number;
  };
  recent_activity: {
    analyses: any[];
    backtests: any[];
    portfolios: any[];
  };
  performance_summary: {
    best_return: number;
    worst_return: number;
    total_invested: number;
    current_value: number;
    profit_loss: number;
  };
}

const PersonalStats: React.FC = () => {
  const [summary, setSummary] = useState<PersonalSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');

  useEffect(() => {
    loadPersonalSummary();
  }, [timeRange]);

  const loadPersonalSummary = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await ApiService.getPersonalSummary();
      if (response.success && response.data) {
        setSummary(response.data);
      } else {
        setError('获取个人统计失败');
      }
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError('暂无权限查看统计数据');
      } else {
        setError(err.response?.data?.message || '获取个人统计失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY'
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getReturnColor = (value: number) => {
    if (value > 0) return '#ff4d4f'; // A股红涨
    if (value < 0) return '#52c41a'; // A股绿跌
    return '#d9d9d9';
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16, color: '#666' }}>加载个人统计中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="统计数据获取失败"
          description={error}
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* 头部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>个人统计摘要</h2>
        <Select
          value={timeRange}
          onChange={setTimeRange}
          style={{ width: 120 }}
        >
          <Option value="7d">7天</Option>
          <Option value="30d">30天</Option>
          <Option value="90d">90天</Option>
          <Option value="all">全部</Option>
        </Select>
      </div>

      {summary ? (
        <>
          {/* 总体统计卡片 */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={5}>
              <Card>
                <Statistic
                  title="分析次数"
                  value={summary.user_stats?.total_analyses || 0}
                  prefix={<BarChartOutlined style={{ color: '#1890ff' }} />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={5}>
              <Card>
                <Statistic
                  title="回测次数"
                  value={summary.user_stats?.total_backtests || 0}
                  prefix={<TrophyOutlined style={{ color: '#52c41a' }} />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={5}>
              <Card>
                <Statistic
                  title="投资组合"
                  value={summary.user_stats?.total_portfolios || 0}
                  prefix={<FundOutlined style={{ color: '#722ed1' }} />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col span={5}>
              <Card>
                <Statistic
                  title="成功率"
                  value={formatPercent(summary.user_stats?.success_rate || 0)}
                  prefix={<RiseOutlined style={{ color: '#faad14' }} />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="平均收益率"
                  value={formatPercent(summary.user_stats?.avg_return || 0)}
                  prefix={
                    (summary.user_stats?.avg_return || 0) >= 0
                      ? <RiseOutlined style={{ color: '#52c41a' }} />
                      : <FallOutlined style={{ color: '#ff4d4f' }} />
                  }
                  valueStyle={{ color: getReturnColor(summary.user_stats?.avg_return || 0) }}
                />
              </Card>
            </Col>
          </Row>

          {/* 投资表现 */}
          <Card title="投资表现" style={{ marginBottom: 24 }}>
            <Row gutter={16}>
              <Col span={5}>
                <Statistic
                  title="总投资金额"
                  value={formatCurrency(summary.performance_summary?.total_invested || 0)}
                  prefix={<DollarOutlined style={{ color: '#1890ff' }} />}
                />
              </Col>
              <Col span={5}>
                <Statistic
                  title="当前总价值"
                  value={formatCurrency(summary.performance_summary?.current_value || 0)}
                  prefix={<DollarOutlined style={{ color: '#52c41a' }} />}
                />
              </Col>
              <Col span={5}>
                <Statistic
                  title="总盈亏"
                  value={formatCurrency(summary.performance_summary?.profit_loss || 0)}
                  valueStyle={{ color: getReturnColor(summary.performance_summary?.profit_loss || 0) }}
                />
              </Col>
              <Col span={5}>
                <Statistic
                  title="最佳收益率"
                  value={formatPercent(summary.performance_summary?.best_return || 0)}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="最差收益率"
                  value={formatPercent(summary.performance_summary?.worst_return || 0)}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
            </Row>

            {/* 收益率进度条 */}
            <div style={{ marginTop: 24 }}>
              <div style={{ marginBottom: 8, fontWeight: 500 }}>收益率区间</div>
              <Progress
                percent={50}
                showInfo={false}
                strokeColor={{
                  '0%': '#ff4d4f',
                  '50%': '#faad14',
                  '100%': '#52c41a',
                }}
                style={{ marginBottom: 8 }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#666' }}>
                <span>最差: {formatPercent(summary.performance_summary?.worst_return || 0)}</span>
                <span>平均: {formatPercent(summary.user_stats?.avg_return || 0)}</span>
                <span>最佳: {formatPercent(summary.performance_summary?.best_return || 0)}</span>
              </div>
            </div>
          </Card>

          {/* 最近活动 */}
          <Row gutter={16}>
            <Col span={8}>
              <Card
                title={
                  <span>
                    <BarChartOutlined style={{ marginRight: 8 }} />
                    最近分析
                  </span>
                }
                size="small"
              >
                {(summary.recent_activity?.analyses || []).length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                    <PieChartOutlined style={{ fontSize: '32px', marginBottom: '8px' }} />
                    <div>暂无分析记录</div>
                  </div>
                ) : (
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {(summary.recent_activity?.analyses || []).slice(0, 5).map((analysis, index) => (
                      <div key={index} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <div style={{ fontWeight: 'bold', fontSize: '13px' }}>
                              {analysis.ticker || analysis.stock_code}
                            </div>
                            <div style={{ fontSize: '11px', color: '#666' }}>
                              {analysis.created_at ? new Date(analysis.created_at).toLocaleDateString('zh-CN') : ''}
                            </div>
                          </div>
                          <Tag
                            color={
                              analysis.status === 'completed' ? 'success' :
                                analysis.status === 'running' ? 'processing' : 'error'
                            }
                          >
                            {analysis.status === 'completed' ? '完成' :
                              analysis.status === 'running' ? '运行中' : '失败'}
                          </Tag>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </Col>

            <Col span={8}>
              <Card
                title={
                  <span>
                    <TrophyOutlined style={{ marginRight: 8 }} />
                    最近回测
                  </span>
                }
                size="small"
              >
                {(summary.recent_activity?.backtests || []).length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                    <LineChartOutlined style={{ fontSize: '32px', marginBottom: '8px' }} />
                    <div>暂无回测记录</div>
                  </div>
                ) : (
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {(summary.recent_activity?.backtests || []).slice(0, 5).map((backtest, index) => (
                      <div key={index} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <div style={{ fontWeight: 'bold', fontSize: '13px' }}>
                              {backtest.ticker}
                            </div>
                            <div style={{ fontSize: '11px', color: '#666' }}>
                              {backtest.created_at ? new Date(backtest.created_at).toLocaleDateString('zh-CN') : ''}
                            </div>
                          </div>
                          <Tag
                            color={
                              backtest.status === 'completed' ? 'success' :
                                backtest.status === 'running' ? 'processing' : 'error'
                            }
                          >
                            {backtest.status === 'completed' ? '完成' :
                              backtest.status === 'running' ? '运行中' : '失败'}
                          </Tag>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </Col>

            <Col span={8}>
              <Card
                title={
                  <span>
                    <FundOutlined style={{ marginRight: 8 }} />
                    投资组合状态
                  </span>
                }
                size="small"
              >
                {(summary.recent_activity?.portfolios || []).length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                    <FundOutlined style={{ fontSize: '32px', marginBottom: '8px' }} />
                    <div>暂无投资组合</div>
                  </div>
                ) : (
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {(summary.recent_activity?.portfolios || []).slice(0, 5).map((portfolio, index) => (
                      <div key={index} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                        <div style={{ marginBottom: '4px' }}>
                          <div style={{ fontWeight: 'bold', fontSize: '13px' }}>
                            {portfolio.name}
                          </div>
                          <div style={{ fontSize: '11px', color: '#666' }}>
                            {formatCurrency(portfolio.current_value || 0)}
                          </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div style={{ fontSize: '11px' }}>
                            收益:
                            <span style={{ color: getReturnColor(portfolio.profit_loss_percent || 0), marginLeft: 4 }}>
                              {formatPercent(portfolio.profit_loss_percent || 0)}
                            </span>
                          </div>
                          <Tag color="blue">
                            {portfolio.risk_level === 'high' ? '高风险' :
                              portfolio.risk_level === 'medium' ? '中风险' : '低风险'}
                          </Tag>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </>
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: '60px', color: '#999' }}>
            <BarChartOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
            <div>暂无统计数据</div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default PersonalStats;