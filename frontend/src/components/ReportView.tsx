import React from 'react';
import { Card, Typography, Tag, Divider, Row, Col, Badge, Progress } from 'antd';
import { 
  ArrowUpOutlined, 
  ArrowDownOutlined, 
  MinusOutlined,
  RiseOutlined,
  FallOutlined,
  RobotOutlined,
  DollarOutlined
} from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

interface ReportViewProps {
  data: any;
}

const ReportView: React.FC<ReportViewProps> = ({ data }) => {
  if (!data || !data.agent_results) {
    return <div>暂无报告数据</div>;
  }

  const { agent_results } = data;

  // 获取信号图标
  const getSignalIcon = (signal: string) => {
    switch (signal?.toLowerCase()) {
      case 'bullish':
      case 'buy':
        return <ArrowUpOutlined style={{ color: '#52c41a' }} />;
      case 'bearish':
      case 'sell':
        return <ArrowDownOutlined style={{ color: '#ff4d4f' }} />;
      case 'neutral':
      case 'hold':
        return <MinusOutlined style={{ color: '#d9d9d9' }} />;
      default:
        return <MinusOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  // 获取信号颜色
  const getSignalColor = (signal: string) => {
    switch (signal?.toLowerCase()) {
      case 'bullish':
      case 'buy':
        return 'success';
      case 'bearish':
      case 'sell':
        return 'error';
      case 'neutral':
      case 'hold':
        return 'default';
      default:
        return 'default';
    }
  };

  // 格式化置信度
  const formatConfidence = (confidence: any) => {
    if (typeof confidence === 'string' && confidence.includes('%')) {
      return confidence;
    }
    if (typeof confidence === 'number') {
      return `${(confidence * 100).toFixed(1)}%`;
    }
    return confidence || '-';
  };

  return (
    <div style={{ padding: '16px 0' }}>
      {/* 标题 */}
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0, borderBottom: '4px double #1890ff', paddingBottom: '8px' }}>
          股票代码 {data.ticker || data.run_id?.split('-')[0]} 投资分析报告
        </Title>
        <Text type="secondary">
          分析区间: {agent_results.market_data?.start_date || ''} 至 {agent_results.market_data?.end_date || ''}
        </Text>
      </div>

      {/* 技术分析 */}
      {agent_results.technical_analyst && (
        <Card 
          title={
            <span>
              📈 技术分析
            </span>
          }
          style={{ marginBottom: '16px' }}
          bordered
        >
          <Row gutter={16}>
            <Col span={12}>
              <Text strong>信号: </Text>
              {getSignalIcon(agent_results.technical_analyst.signal)}
              <Tag color={getSignalColor(agent_results.technical_analyst.signal)} style={{ marginLeft: 8 }}>
                {agent_results.technical_analyst.signal?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              {formatConfidence(agent_results.technical_analyst.confidence)}
            </Col>
          </Row>
          
          {agent_results.technical_analyst.strategy_signals && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>策略信号详情</Divider>
              {Object.entries(agent_results.technical_analyst.strategy_signals).map(([strategy, data]: [string, any]) => (
                <Card key={strategy} size="small" style={{ marginBottom: '8px' }}>
                  <Text strong>{strategy.replace(/_/g, ' ').toUpperCase()}: </Text>
                  <Tag color={getSignalColor(data.signal)}>{data.signal}</Tag>
                  <span style={{ marginLeft: '8px' }}>置信度: {formatConfidence(data.confidence)}</span>
                  {data.metrics && (
                    <div style={{ marginTop: '8px', fontSize: '12px' }}>
                      {Object.entries(data.metrics).map(([key, value]: [string, any]) => (
                        <span key={key} style={{ marginRight: '16px' }}>
                          {key}: {typeof value === 'number' ? value.toFixed(4) : value}
                        </span>
                      ))}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* 基本面分析 */}
      {agent_results.fundamentals && (
        <Card 
          title={<span>📝 基本面分析</span>}
          style={{ marginBottom: '16px' }}
          bordered
        >
          <Row gutter={16}>
            <Col span={12}>
              <Text strong>信号: </Text>
              {getSignalIcon(agent_results.fundamentals.signal)}
              <Tag color={getSignalColor(agent_results.fundamentals.signal)} style={{ marginLeft: 8 }}>
                {agent_results.fundamentals.signal?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              {formatConfidence(agent_results.fundamentals.confidence)}
            </Col>
          </Row>
          {agent_results.fundamentals.reasoning && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>分析详情</Divider>
              {Object.entries(agent_results.fundamentals.reasoning).map(([key, data]: [string, any]) => (
                <div key={key} style={{ marginBottom: '8px' }}>
                  <Text strong>{key}: </Text>
                  <Tag color={getSignalColor(data.signal)}>{data.signal}</Tag>
                  <Text type="secondary" style={{ marginLeft: '8px' }}>{data.details}</Text>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* 情感分析 */}
      {agent_results.sentiment && (
        <Card 
          title={<span>🔍 情感分析</span>}
          style={{ marginBottom: '16px' }}
          bordered
        >
          <Row gutter={16}>
            <Col span={12}>
              <Text strong>信号: </Text>
              {getSignalIcon(agent_results.sentiment.signal)}
              <Tag color={getSignalColor(agent_results.sentiment.signal)} style={{ marginLeft: 8 }}>
                {agent_results.sentiment.signal?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              {formatConfidence(agent_results.sentiment.confidence)}
            </Col>
          </Row>
          {agent_results.sentiment.reasoning && (
            <Paragraph style={{ marginTop: '16px', background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
              {agent_results.sentiment.reasoning}
            </Paragraph>
          )}
        </Card>
      )}

      {/* 估值分析 */}
      {agent_results.valuation && (
        <Card 
          title={<span>💰 估值分析</span>}
          style={{ marginBottom: '16px' }}
          bordered
        >
          <Row gutter={16}>
            <Col span={12}>
              <Text strong>信号: </Text>
              {getSignalIcon(agent_results.valuation.signal)}
              <Tag color={getSignalColor(agent_results.valuation.signal)} style={{ marginLeft: 8 }}>
                {agent_results.valuation.signal?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              {formatConfidence(agent_results.valuation.confidence)}
            </Col>
          </Row>
          {agent_results.valuation.reasoning && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>估值详情</Divider>
              {Object.entries(agent_results.valuation.reasoning).map(([key, data]: [string, any]) => (
                <div key={key} style={{ marginBottom: '8px' }}>
                  <Text strong>{key}: </Text>
                  <Tag color={getSignalColor(data.signal)}>{data.signal}</Tag>
                  <Text type="secondary" style={{ marginLeft: '8px' }}>{data.details}</Text>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* 多方研究分析 */}
      {agent_results.researcher_bull && (
        <Card 
          title={<span>🐂 多方研究分析</span>}
          style={{ marginBottom: '16px' }}
          bordered
        >
          <Row gutter={16}>
            <Col span={12}>
              <Text strong>观点: </Text>
              <Tag color="green">
                <RiseOutlined /> {agent_results.researcher_bull.perspective?.toUpperCase() || 'BULL'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              {formatConfidence(agent_results.researcher_bull.confidence)}
            </Col>
          </Row>
          {agent_results.researcher_bull.thesis_points && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>论点</Divider>
              {agent_results.researcher_bull.thesis_points.map((point: string, index: number) => (
                <div key={index} style={{ marginBottom: '4px' }}>
                  <Text>+ {point}</Text>
                </div>
              ))}
            </div>
          )}
          {agent_results.researcher_bull.reasoning && (
            <Paragraph style={{ marginTop: '16px', background: '#f6ffed', padding: '12px', borderRadius: '4px' }}>
              {agent_results.researcher_bull.reasoning}
            </Paragraph>
          )}
        </Card>
      )}

      {/* 空方研究分析 */}
      {agent_results.researcher_bear && (
        <Card 
          title={<span>🐻 空方研究分析</span>}
          style={{ marginBottom: '16px' }}
          bordered
        >
          <Row gutter={16}>
            <Col span={12}>
              <Text strong>观点: </Text>
              <Tag color="red">
                <FallOutlined /> {agent_results.researcher_bear.perspective?.toUpperCase() || 'BEAR'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              {formatConfidence(agent_results.researcher_bear.confidence)}
            </Col>
          </Row>
          {agent_results.researcher_bear.thesis_points && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>论点</Divider>
              {agent_results.researcher_bear.thesis_points.map((point: string, index: number) => (
                <div key={index} style={{ marginBottom: '4px' }}>
                  <Text>- {point}</Text>
                </div>
              ))}
            </div>
          )}
          {agent_results.researcher_bear.reasoning && (
            <Paragraph style={{ marginTop: '16px', background: '#fff2e8', padding: '12px', borderRadius: '4px' }}>
              {agent_results.researcher_bear.reasoning}
            </Paragraph>
          )}
        </Card>
      )}

      {/* 辩论室分析 */}
      {agent_results.debate_room && (
        <Card 
          title={<span>🗣️ 辩论室分析</span>}
          style={{ marginBottom: '16px' }}
          bordered
        >
          <Row gutter={16}>
            <Col span={8}>
              <Text strong>信号: </Text>
              {getSignalIcon(agent_results.debate_room.signal)}
              <Tag color={getSignalColor(agent_results.debate_room.signal)} style={{ marginLeft: 8 }}>
                {agent_results.debate_room.signal?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={8}>
              <Text strong>总置信度: </Text>
              {formatConfidence(agent_results.debate_room.confidence)}
            </Col>
            <Col span={8}>
              <Text strong>LLM评分: </Text>
              {agent_results.debate_room.llm_score ? `${(agent_results.debate_room.llm_score * 100).toFixed(1)}%` : '-'}
            </Col>
          </Row>
          
          <div style={{ marginTop: '16px' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>多方置信度: </Text>
                <Progress 
                  percent={Number(formatConfidence(agent_results.debate_room.bull_confidence).replace('%', ''))} 
                  size="small" 
                  strokeColor="#52c41a"
                />
              </Col>
              <Col span={12}>
                <Text strong>空方置信度: </Text>
                <Progress 
                  percent={Number(formatConfidence(agent_results.debate_room.bear_confidence).replace('%', ''))} 
                  size="small" 
                  strokeColor="#ff4d4f"
                />
              </Col>
            </Row>
          </div>

          {agent_results.debate_room.llm_analysis && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>LLM分析</Divider>
              <Paragraph style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                {agent_results.debate_room.llm_analysis}
              </Paragraph>
            </div>
          )}

          {agent_results.debate_room.debate_summary && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>辩论总结</Divider>
              <div style={{ background: '#fafafa', padding: '12px', borderRadius: '4px' }}>
                {agent_results.debate_room.debate_summary.map((summary: string, index: number) => (
                  <div key={index} style={{ marginBottom: '4px', fontFamily: 'monospace' }}>
                    {summary}
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* 风险管理分析 */}
      {agent_results.risk_management && (
        <Card 
          title={<span>⚠️ 风险管理分析</span>}
          style={{ marginBottom: '16px' }}
          bordered
        >
          <Row gutter={16}>
            <Col span={8}>
              <Text strong>风险评分: </Text>
              <Badge count={agent_results.risk_management.risk_score} style={{ backgroundColor: '#f50' }} />
              <span style={{ marginLeft: '8px' }}>/10</span>
            </Col>
            <Col span={8}>
              <Text strong>建议操作: </Text>
              <Tag color={getSignalColor(agent_results.risk_management.trading_action)}>
                {agent_results.risk_management.trading_action?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={8}>
              <Text strong>最大仓位: </Text>
              {agent_results.risk_management.max_position_size?.toFixed(2) || '-'}
            </Col>
          </Row>

          {agent_results.risk_management.risk_metrics && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>风险指标</Divider>
              <Row gutter={16}>
                <Col span={12}>
                  <Text>波动率: {(agent_results.risk_management.risk_metrics.volatility * 100).toFixed(2)}%</Text>
                </Col>
                <Col span={12}>
                  <Text>VaR (95%): {(agent_results.risk_management.risk_metrics.value_at_risk_95 * 100).toFixed(2)}%</Text>
                </Col>
                <Col span={12}>
                  <Text>最大回撤: {(agent_results.risk_management.risk_metrics.max_drawdown * 100).toFixed(2)}%</Text>
                </Col>
                <Col span={12}>
                  <Text>市场风险评分: {agent_results.risk_management.risk_metrics.market_risk_score}/10</Text>
                </Col>
              </Row>
            </div>
          )}

          {agent_results.risk_management.reasoning && (
            <Paragraph style={{ marginTop: '16px', background: '#fff2e8', padding: '12px', borderRadius: '4px' }}>
              {agent_results.risk_management.reasoning}
            </Paragraph>
          )}
        </Card>
      )}

      {/* 宏观分析 */}
      {agent_results.macro_analyst && (
        <Card 
          title={<span>🌍 宏观分析</span>}
          style={{ marginBottom: '16px' }}
          bordered
        >
          <Row gutter={16}>
            <Col span={8}>
              <Text strong>宏观环境: </Text>
              <Tag color={getSignalColor(agent_results.macro_analyst.macro_environment)}>
                {agent_results.macro_analyst.macro_environment?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={8}>
              <Text strong>置信度: </Text>
              <Tag color={agent_results.macro_analyst.confidence > 0.7 ? 'green' : agent_results.macro_analyst.confidence > 0.4 ? 'orange' : 'red'}>
                {agent_results.macro_analyst.confidence ? `${(agent_results.macro_analyst.confidence * 100).toFixed(0)}%` : 'N/A'}
              </Tag>
            </Col>
            <Col span={8}>
              <Text strong>股票影响: </Text>
              <Tag color={getSignalColor(agent_results.macro_analyst.impact_on_stock)}>
                {agent_results.macro_analyst.impact_on_stock?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
          </Row>

          {/* 经济指标 */}
          {agent_results.macro_analyst.economic_indicators && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>经济指标</Divider>
              <Row gutter={[16, 8]}>
                {Object.entries(agent_results.macro_analyst.economic_indicators).map(([indicator, data]: [string, any]) => (
                  <Col span={8} key={indicator}>
                    <Card size="small" style={{ textAlign: 'center' }}>
                      <Text strong style={{ fontSize: '12px' }}>{indicator}</Text>
                      <div style={{ marginTop: '4px' }}>
                        {typeof data === 'object' && data !== null ? (
                          <>
                            <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                              {data.value || data.current || 'N/A'}
                            </div>
                            {data.trend && (
                              <Tag size="small" color={data.trend === 'up' ? 'green' : data.trend === 'down' ? 'red' : 'blue'}>
                                {data.trend}
                              </Tag>
                            )}
                          </>
                        ) : (
                          <div style={{ fontSize: '14px' }}>{String(data)}</div>
                        )}
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          )}

          {agent_results.macro_analyst.key_factors && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>关键因素</Divider>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {agent_results.macro_analyst.key_factors.map((factor: string, index: number) => (
                  <Tag 
                    key={index} 
                    style={{ 
                      marginBottom: '4px',
                      padding: '4px 8px',
                      borderRadius: '8px'
                    }}
                    color="blue"
                  >
                    {factor}
                  </Tag>
                ))}
              </div>
            </div>
          )}

          {/* 政策影响 */}
          {agent_results.macro_analyst.policy_impact && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>政策影响</Divider>
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>货币政策: </Text>
                  <Tag color={getSignalColor(agent_results.macro_analyst.policy_impact.monetary)}>
                    {agent_results.macro_analyst.policy_impact.monetary?.toUpperCase() || 'UNKNOWN'}
                  </Tag>
                </Col>
                <Col span={12}>
                  <Text strong>财政政策: </Text>
                  <Tag color={getSignalColor(agent_results.macro_analyst.policy_impact.fiscal)}>
                    {agent_results.macro_analyst.policy_impact.fiscal?.toUpperCase() || 'UNKNOWN'}
                  </Tag>
                </Col>
              </Row>
            </div>
          )}

          {agent_results.macro_analyst.reasoning && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>分析推理</Divider>
              {typeof agent_results.macro_analyst.reasoning === 'string' ? (
                <Paragraph style={{ 
                  marginTop: '8px', 
                  background: '#f6f8ff', 
                  padding: '12px', 
                  borderRadius: '8px',
                  border: '1px solid #e6f0ff'
                }}>
                  {agent_results.macro_analyst.reasoning}
                </Paragraph>
              ) : (
                Object.entries(agent_results.macro_analyst.reasoning).map(([key, reasoning]: [string, any]) => (
                  <div key={key} style={{ marginBottom: '12px' }}>
                    <Text strong style={{ color: '#1890ff' }}>{key.replace(/_/g, ' ').toUpperCase()}: </Text>
                    <Paragraph style={{ 
                      marginTop: '4px', 
                      marginLeft: '16px',
                      background: '#fafafa',
                      padding: '8px',
                      borderRadius: '4px',
                      borderLeft: '3px solid #1890ff'
                    }}>
                      {typeof reasoning === 'object' ? JSON.stringify(reasoning, null, 2) : String(reasoning)}
                    </Paragraph>
                  </div>
                ))
              )}
            </div>
          )}
        </Card>
      )}

      {/* 投资组合管理分析 */}
      {agent_results.portfolio_management && (
        <Card 
          title={<span>📂 投资组合管理分析</span>}
          style={{ marginBottom: '16px' }}
          bordered
        >
          <Row gutter={16}>
            <Col span={8}>
              <Text strong>交易行动: </Text>
              <Tag color={getSignalColor(agent_results.portfolio_management.action)} icon={<DollarOutlined />}>
                {agent_results.portfolio_management.action?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={8}>
              <Text strong>交易数量: </Text>
              {agent_results.portfolio_management.quantity || '-'}
            </Col>
            <Col span={8}>
              <Text strong>决策信心: </Text>
              {formatConfidence(agent_results.portfolio_management.confidence)}
            </Col>
          </Row>

          {agent_results.portfolio_management.agent_signals && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>各分析师意见</Divider>
              {agent_results.portfolio_management.agent_signals.map((signal: any, index: number) => (
                <div key={index} style={{ marginBottom: '8px', padding: '8px', background: '#fafafa', borderRadius: '4px' }}>
                  <Row gutter={16} align="middle">
                    <Col span={8}>
                      <RobotOutlined style={{ marginRight: '8px' }} />
                      <Text strong>{signal.agent_name}</Text>
                    </Col>
                    <Col span={8}>
                      {getSignalIcon(signal.signal)}
                      <Tag color={getSignalColor(signal.signal)} style={{ marginLeft: 8 }}>
                        {signal.signal?.toUpperCase()}
                      </Tag>
                    </Col>
                    <Col span={8}>
                      <Text>置信度: {formatConfidence(signal.confidence)}</Text>
                    </Col>
                  </Row>
                </div>
              ))}
            </div>
          )}

          {agent_results.portfolio_management.reasoning && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>决策理由</Divider>
              <Paragraph style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                {agent_results.portfolio_management.reasoning}
              </Paragraph>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default ReportView;