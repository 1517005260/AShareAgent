import React from 'react';
import { Card, Typography, Tag, Divider, Row, Col, Badge, Alert } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
  RiseOutlined,
  FallOutlined,
  RobotOutlined,
  DollarOutlined,
  TrophyOutlined,
  WarningOutlined
} from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

interface ReportViewProps {
  data: any;
}

// 为各个分析模块提供默认的分析说明
const getDefaultReasoning = (agentName: string): string => {
  const reasoningMap: {[key: string]: string} = {
    'technical_analysis': '技术分析基于价格走势、交易量和技术指标进行评估。通过分析趋势、动量、支撑阻力位等因素，为投资决策提供技术面依据。',
    'fundamental_analysis': '基本面分析评估公司的财务健康状况，包括盈利能力、成长性、财务稳定性等关键指标。通过分析ROE、净利润率、营收增长等数据判断公司内在价值。',
    'sentiment_analysis': '情感分析通过分析市场新闻、社交媒体情绪、投资者行为等因素，评估市场对该股票的整体情绪倾向和预期。',
    'valuation_analysis': '估值分析运用DCF模型、所有者收益法等估值方法，计算股票的内在价值，并与当前市场价格比较以判断是否存在投资机会。',
    'risk_management': '风险管理分析评估投资风险水平，包括波动性、最大回撤、VaR等风险指标，并提供仓位建议和风险控制措施。',
    'selected_stock_macro_analysis': '宏观分析评估宏观经济环境对个股的影响，包括政策变化、经济周期、行业发展等宏观因素的综合分析。',
    'market_wide_news_summary(沪深300指数)': '大盘新闻分析通过分析沪深300指数相关新闻和市场动态，评估整体市场环境和趋势对个股的影响。',
    'ashare_policy_impact': 'A股政策影响分析专门评估中国股市政策变化对投资的影响，包括监管政策、财政政策、货币政策等。',
    'liquidity_assessment': '流动性评估分析市场流动性状况，包括成交量、买卖价差、市场深度等因素，评估交易执行的便利性和成本。'
  };
  return reasoningMap[agentName] || `${agentName}的专业分析结果`;
};

const ReportView: React.FC<ReportViewProps> = ({ data }) => {
  // 检查数据有效性
  if (!data) {
    return (
      <Alert
        message="暂无报告数据"
        description="分析结果为空，请重新运行分析"
        type="warning"
        showIcon
      />
    );
  }

  // 检查数据结构并适配不同的返回格式
  console.log('ReportView received data:', data);
  
  // 尝试从不同来源获取数据
  let analysisData = null;
  let agent_results = null;
  
  // 优先级1: 从data.result获取（API标准格式）
  if (data.result && data.result.agent_results) {
    analysisData = data.result;
    agent_results = data.result.agent_results;
  }
  // 优先级2: 直接从data获取（直接格式）
  else if (data.agent_results && !data.action) {
    analysisData = data;
    agent_results = data.agent_results;
  }
  // 优先级3: 处理portfolio manager的直接输出格式
  else if (data.action && data.agent_signals && Array.isArray(data.agent_signals)) {
    // 这是portfolio manager的直接输出格式，需要转换
    analysisData = data;
    // 从agent_signals中构建agent_results结构
    agent_results = {};
    
    if (data.agent_signals && Array.isArray(data.agent_signals)) {
      data.agent_signals.forEach((signal: any) => {
        const agentName = signal.agent_name;
        if (agentName) {
          // 映射agent名称到前端期望的格式
          const nameMapping: {[key: string]: string} = {
            'technical_analysis': 'technical_analyst',
            'fundamental_analysis': 'fundamentals',
            'sentiment_analysis': 'sentiment',
            'valuation_analysis': 'valuation',
            'risk_management': 'risk_management',
            'selected_stock_macro_analysis': 'macro_analyst',
            'market_wide_news_summary(沪深300指数)': 'macro_news',
            'ashare_policy_impact': 'policy_impact',
            'liquidity_assessment': 'liquidity'
          };
          
          const mappedName = nameMapping[agentName] || agentName;
          agent_results[mappedName] = {
            signal: signal.signal,
            confidence: signal.confidence,
            reasoning: signal.reasoning || getDefaultReasoning(agentName),
            // 添加额外的字段以支持更详细的显示
            ...(signal.details && { details: signal.details }),
            ...(signal.metrics && { metrics: signal.metrics }),
            ...(signal.risk_score && { risk_score: signal.risk_score }),
            ...(signal.trading_action && { trading_action: signal.trading_action }),
            ...(signal.max_position_size && { max_position_size: signal.max_position_size }),
            ...(signal.risk_metrics && { risk_metrics: signal.risk_metrics })
          };
        }
      });
    }
  }
  
  // 如果仍然没有找到有效数据，显示错误信息
  if (!agent_results || Object.keys(agent_results).length === 0) {
    return (
      <Alert
        message="报告数据格式错误"
        description={
          <div>
            <div>分析结果中缺少agent_results字段</div>
            <div style={{ marginTop: 8, fontSize: '12px' }}>
              数据结构: {JSON.stringify(Object.keys(data), null, 2)}
            </div>
            {(data.final_decision || data.reasoning) && (
              <div style={{ marginTop: 8, fontSize: '12px', maxHeight: '200px', overflow: 'auto', background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                <strong>原始分析结果:</strong>
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: '11px' }}>
                  {String(data.final_decision || data.reasoning).substring(0, 1000)}...
                </pre>
              </div>
            )}
          </div>
        }
        type="error"
        showIcon
      />
    );
  }

  console.log('Final agent_results:', agent_results);
  console.log('Agent results keys:', agent_results ? Object.keys(agent_results) : 'none');

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

  // 安全获取数据的函数
  const safeGet = (obj: any, path: string[], defaultValue: any = null) => {
    try {
      return path.reduce((current, key) => current && current[key], obj) || defaultValue;
    } catch {
      return defaultValue;
    }
  };

  return (
    <div style={{ padding: '24px 0' }}>
      {/* 标题 */}
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <Title level={2} style={{
          margin: 0,
          background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          borderBottom: '3px solid #1890ff',
          paddingBottom: '12px',
          display: 'inline-block'
        }}>
          <TrophyOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          股票代码 {
            data.ticker || 
            data.result?.ticker || 
            analysisData?.ticker || 
            data.task_id?.split('-')[0] ||
            data.run_id?.split('-')[0] || 
            // 尝试从agent_signals中提取ticker信息
            (data.agent_signals && data.agent_signals.length > 0 && data.agent_signals[0].ticker) ||
            // 从当前URL或其他来源提取
            (window.location.pathname.includes('/analysis/') && window.location.pathname.split('/').pop()) ||
            'Unknown'
          } 投资分析报告
        </Title>
        <div style={{ marginTop: 8, color: '#666', fontSize: '14px' }}>
          分析区间: {safeGet(agent_results, ['market_data', 'start_date']) || ''} 至 {safeGet(agent_results, ['market_data', 'end_date']) || ''}
        </div>
      </div>

      {/* 技术分析 */}
      {agent_results.technical_analyst && (
        <Card
          title={
            <span>
              📈 技术分析
            </span>
          }
          style={{ marginBottom: '24px' }}
          bordered
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Text strong>信号: </Text>
              {getSignalIcon(agent_results.technical_analyst.signal)}
              <Tag color={getSignalColor(agent_results.technical_analyst.signal)} style={{ marginLeft: 8 }}>
                {agent_results.technical_analyst.signal?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              <Tag color="blue">
                {formatConfidence(agent_results.technical_analyst.confidence)}
              </Tag>
            </Col>
          </Row>

          {agent_results.technical_analyst.strategy_signals && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>策略信号详情</Divider>
              <Row gutter={[16, 16]}>
                {Object.entries(agent_results.technical_analyst.strategy_signals).map(([strategy, data]: [string, any]) => (
                  <Col span={12} key={strategy}>
                    <Card size="small" style={{ height: '100%' }}>
                      <div style={{ marginBottom: 8 }}>
                        <Text strong>{strategy.replace(/_/g, ' ').toUpperCase()}: </Text>
                        <Tag color={getSignalColor(data.signal)}>{data.signal}</Tag>
                      </div>
                      <div style={{ marginBottom: 8 }}>
                        <Text type="secondary">置信度: {formatConfidence(data.confidence)}</Text>
                      </div>
                      {data.metrics && (
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          {Object.entries(data.metrics).slice(0, 3).map(([key, value]: [string, any]) => (
                            <div key={key}>
                              {key}: {typeof value === 'number' ? value.toFixed(4) : value}
                            </div>
                          ))}
                        </div>
                      )}
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          )}
        </Card>
      )}

      {/* 基本面分析 */}
      {agent_results.fundamentals && (
        <Card
          title={<span>📝 基本面分析</span>}
          style={{ marginBottom: '24px' }}
          bordered
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Text strong>信号: </Text>
              {getSignalIcon(agent_results.fundamentals.signal)}
              <Tag color={getSignalColor(agent_results.fundamentals.signal)} style={{ marginLeft: 8 }}>
                {agent_results.fundamentals.signal?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              <Tag color="blue">
                {formatConfidence(agent_results.fundamentals.confidence)}
              </Tag>
            </Col>
          </Row>
          {agent_results.fundamentals.reasoning && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>分析详情</Divider>
              {typeof agent_results.fundamentals.reasoning === 'object' ? (
                <Row gutter={[16, 8]}>
                  {Object.entries(agent_results.fundamentals.reasoning).map(([key, data]: [string, any]) => (
                    <Col span={12} key={key}>
                      <Card size="small">
                        <Text strong>{key}: </Text>
                        <Tag color={getSignalColor(data.signal)}>{data.signal}</Tag>
                        <div style={{ marginTop: 4, fontSize: '12px', color: '#666' }}>
                          {data.details}
                        </div>
                      </Card>
                    </Col>
                  ))}
                </Row>
              ) : (
                <Paragraph style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                  {agent_results.fundamentals.reasoning}
                </Paragraph>
              )}
            </div>
          )}
        </Card>
      )}

      {/* 情感分析 */}
      {agent_results.sentiment && (
        <Card
          title={<span>🔍 情感分析</span>}
          style={{ marginBottom: '24px' }}
          bordered
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Text strong>信号: </Text>
              {getSignalIcon(agent_results.sentiment.signal)}
              <Tag color={getSignalColor(agent_results.sentiment.signal)} style={{ marginLeft: 8 }}>
                {agent_results.sentiment.signal?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              <Tag color="blue">
                {formatConfidence(agent_results.sentiment.confidence)}
              </Tag>
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
          style={{ marginBottom: '24px' }}
          bordered
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Text strong>信号: </Text>
              {getSignalIcon(agent_results.valuation.signal)}
              <Tag color={getSignalColor(agent_results.valuation.signal)} style={{ marginLeft: 8 }}>
                {agent_results.valuation.signal?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              <Tag color="blue">
                {formatConfidence(agent_results.valuation.confidence)}
              </Tag>
            </Col>
          </Row>
          {agent_results.valuation.reasoning && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>估值详情</Divider>
              {typeof agent_results.valuation.reasoning === 'object' ? (
                <Row gutter={[16, 8]}>
                  {Object.entries(agent_results.valuation.reasoning).map(([key, data]: [string, any]) => (
                    <Col span={12} key={key}>
                      <Card size="small">
                        <Text strong>{key}: </Text>
                        <Tag color={getSignalColor(data.signal)}>{data.signal}</Tag>
                        <div style={{ marginTop: 4, fontSize: '12px', color: '#666' }}>
                          {data.details}
                        </div>
                      </Card>
                    </Col>
                  ))}
                </Row>
              ) : (
                <Paragraph style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                  {agent_results.valuation.reasoning}
                </Paragraph>
              )}
            </div>
          )}
        </Card>
      )}

      {/* 多方研究分析 */}
      {agent_results.researcher_bull && (
        <Card
          title={<span>🐂 多方研究分析</span>}
          style={{ marginBottom: '24px' }}
          bordered
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Text strong>观点: </Text>
              <Tag color="green">
                <RiseOutlined /> {agent_results.researcher_bull.perspective?.toUpperCase() || 'BULL'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              <Tag color="blue">
                {formatConfidence(agent_results.researcher_bull.confidence)}
              </Tag>
            </Col>
          </Row>
          {agent_results.researcher_bull.thesis_points && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>论点</Divider>
              <div style={{ background: '#f6ffed', padding: '16px', borderRadius: '6px', border: '1px solid #b7eb8f' }}>
                {agent_results.researcher_bull.thesis_points.map((point: string, index: number) => (
                  <div key={index} style={{ marginBottom: '8px', display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ color: '#52c41a', marginRight: '8px', fontWeight: 'bold' }}>+</span>
                    <Text>{point}</Text>
                  </div>
                ))}
              </div>
            </div>
          )}
          {agent_results.researcher_bull.reasoning && (
            <Paragraph style={{ marginTop: '16px', background: '#f6ffed', padding: '12px', borderRadius: '4px', border: '1px solid #b7eb8f' }}>
              {agent_results.researcher_bull.reasoning}
            </Paragraph>
          )}
        </Card>
      )}

      {/* 空方研究分析 */}
      {agent_results.researcher_bear && (
        <Card
          title={<span>🐻 空方研究分析</span>}
          style={{ marginBottom: '24px' }}
          bordered
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Text strong>观点: </Text>
              <Tag color="red">
                <FallOutlined /> {agent_results.researcher_bear.perspective?.toUpperCase() || 'BEAR'}
              </Tag>
            </Col>
            <Col span={12}>
              <Text strong>置信度: </Text>
              <Tag color="blue">
                {formatConfidence(agent_results.researcher_bear.confidence)}
              </Tag>
            </Col>
          </Row>
          {agent_results.researcher_bear.thesis_points && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>论点</Divider>
              <div style={{ background: '#fff2e8', padding: '16px', borderRadius: '6px', border: '1px solid #ffccc7' }}>
                {agent_results.researcher_bear.thesis_points.map((point: string, index: number) => (
                  <div key={index} style={{ marginBottom: '8px', display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ color: '#ff4d4f', marginRight: '8px', fontWeight: 'bold' }}>-</span>
                    <Text>{point}</Text>
                  </div>
                ))}
              </div>
            </div>
          )}
          {agent_results.researcher_bear.reasoning && (
            <Paragraph style={{ marginTop: '16px', background: '#fff2e8', padding: '12px', borderRadius: '4px', border: '1px solid #ffccc7' }}>
              {agent_results.researcher_bear.reasoning}
            </Paragraph>
          )}
        </Card>
      )}

      {/* 风险管理分析 */}
      {agent_results.risk_management && (
        <Card
          title={<span><WarningOutlined /> 风险管理分析</span>}
          style={{ marginBottom: '24px' }}
          bordered
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Text strong>风险评分: </Text>
              <Badge 
                count={agent_results.risk_management.risk_score || 'N/A'} 
                style={{ backgroundColor: '#f50' }} 
              />
              <span style={{ marginLeft: '8px' }}>/10</span>
            </Col>
            <Col span={8}>
              <Text strong>建议操作: </Text>
              <Tag color={getSignalColor(agent_results.risk_management.trading_action || agent_results.risk_management.signal)}>
                {(agent_results.risk_management.trading_action || agent_results.risk_management.signal)?.toUpperCase() || '持有'}
              </Tag>
            </Col>
            <Col span={8}>
              <Text strong>最大仓位: </Text>
              <Text type="secondary">
                {agent_results.risk_management.max_position_size?.toFixed?.(2) || '未设定'}
              </Text>
            </Col>
          </Row>

          {agent_results.risk_management.risk_metrics && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>风险指标</Divider>
              <Row gutter={16}>
                <Col span={6}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <Paragraph strong style={{ margin: 0, fontSize: '12px' }}>波动率</Paragraph>
                    <Text style={{ fontSize: '16px', fontWeight: 'bold' }}>
                      {agent_results.risk_management.risk_metrics?.volatility 
                        ? (agent_results.risk_management.risk_metrics.volatility * 100).toFixed(2) + '%'
                        : 'N/A'}
                    </Text>
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <Paragraph strong style={{ margin: 0, fontSize: '12px' }}>VaR (95%)</Paragraph>
                    <Text style={{ fontSize: '16px', fontWeight: 'bold' }}>
                      {agent_results.risk_management.risk_metrics?.value_at_risk_95 
                        ? (agent_results.risk_management.risk_metrics.value_at_risk_95 * 100).toFixed(2) + '%'
                        : 'N/A'}
                    </Text>
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <Paragraph strong style={{ margin: 0, fontSize: '12px' }}>最大回撤</Paragraph>
                    <Text style={{ fontSize: '16px', fontWeight: 'bold' }}>
                      {agent_results.risk_management.risk_metrics?.max_drawdown 
                        ? (agent_results.risk_management.risk_metrics.max_drawdown * 100).toFixed(2) + '%'
                        : 'N/A'}
                    </Text>
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <Paragraph strong style={{ margin: 0, fontSize: '12px' }}>市场风险</Paragraph>
                    <Text style={{ fontSize: '16px', fontWeight: 'bold' }}>
                      {agent_results.risk_management.risk_metrics?.market_risk_score 
                        ? agent_results.risk_management.risk_metrics.market_risk_score + '/10'
                        : 'N/A'}
                    </Text>
                  </Card>
                </Col>
              </Row>
            </div>
          )}

          {agent_results.risk_management.reasoning && (
            <Paragraph style={{ marginTop: '16px', background: '#fff2e8', padding: '12px', borderRadius: '4px', border: '1px solid #ffccc7' }}>
              {agent_results.risk_management.reasoning}
            </Paragraph>
          )}
        </Card>
      )}

      {/* 投资组合管理分析 */}
      {agent_results.portfolio_management && (
        <Card
          title={<span><DollarOutlined /> 投资组合管理分析</span>}
          style={{ marginBottom: '24px' }}
          bordered
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Text strong>交易行动: </Text>
              <Tag color={getSignalColor(agent_results.portfolio_management.action)} icon={<DollarOutlined />}>
                {agent_results.portfolio_management.action?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </Col>
            <Col span={8}>
              <Text strong>交易数量: </Text>
              <Text type="secondary">
                {agent_results.portfolio_management.quantity || '-'}
              </Text>
            </Col>
            <Col span={8}>
              <Text strong>决策信心: </Text>
              <Tag color="blue">
                {formatConfidence(agent_results.portfolio_management.confidence)}
              </Tag>
            </Col>
          </Row>

          {agent_results.portfolio_management.agent_signals && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>各分析师意见</Divider>
              <Row gutter={[16, 8]}>
                {agent_results.portfolio_management.agent_signals.map((signal: any, index: number) => (
                  <Col span={12} key={index}>
                    <Card size="small" style={{ background: '#fafafa' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <RobotOutlined style={{ marginRight: '8px' }} />
                          <Text strong>{signal.agent_name}</Text>
                        </div>
                        <div>
                          {getSignalIcon(signal.signal)}
                          <Tag color={getSignalColor(signal.signal)} style={{ marginLeft: 8 }}>
                            {signal.signal?.toUpperCase()}
                          </Tag>
                        </div>
                      </div>
                      <div style={{ marginTop: 4, fontSize: '12px', color: '#666' }}>
                        置信度: {formatConfidence(signal.confidence)}
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
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

      {/* 最终投资决策摘要 */}
      {analysisData && analysisData.action && (
        <Card
          title={
            <span>
              <TrophyOutlined style={{ color: '#1890ff', marginRight: 8 }} />
              最终投资决策
            </span>
          }
          style={{ marginBottom: '24px' }}
          bordered
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Text strong>操作建议: </Text>
              {getSignalIcon(analysisData.action)}
              <Tag color={getSignalColor(analysisData.action)} style={{ marginLeft: 8 }}>
                {analysisData.action === 'buy' ? '买入' : 
                 analysisData.action === 'sell' ? '卖出' : '持有'}
              </Tag>
            </Col>
            <Col span={8}>
              <Text strong>交易数量: </Text>
              <Text type="secondary">{analysisData.quantity || 0} 股</Text>
            </Col>
            <Col span={8}>
              <Text strong>决策置信度: </Text>
              <Tag color="blue">
                {formatConfidence(analysisData.confidence)}
              </Tag>
            </Col>
          </Row>

          {analysisData.reasoning && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>决策理由</Divider>
              <Paragraph style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                {analysisData.reasoning}
              </Paragraph>
            </div>
          )}

          {analysisData.ashare_considerations && (
            <div style={{ marginTop: '16px' }}>
              <Divider orientation="left" plain>A股特色考虑</Divider>
              <div style={{ background: '#e6f7ff', padding: '12px', borderRadius: '4px', border: '1px solid #91d5ff' }}>
                {typeof analysisData.ashare_considerations === 'string' ? (
                  <Paragraph style={{ margin: 0 }}>
                    {analysisData.ashare_considerations}
                  </Paragraph>
                ) : (
                  <div>
                    {Object.entries(analysisData.ashare_considerations).map(([key, value]: [string, any]) => (
                      <div key={key} style={{ marginBottom: '8px' }}>
                        <Text strong>{key}: </Text>
                        <Text>{String(value)}</Text>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* 如果没有任何agent结果，显示提示 */}
      {Object.keys(agent_results).length === 0 && (
        <Alert
          message="暂无分析结果"
          description="Agent分析结果为空，请检查分析配置或重新运行分析"
          type="info"
          showIcon
        />
      )}
    </div>
  );
};

export default ReportView;