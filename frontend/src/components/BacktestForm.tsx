import React, { useState } from 'react';
import { Form, Input, Button, DatePicker, InputNumber, Card, message, Collapse, Space, Switch, Select, Row, Col } from 'antd';
import { PlayCircleOutlined, SettingOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import ApiService, { type BacktestRequest } from '../services/api';

const { RangePicker } = DatePicker;
const { Panel } = Collapse;
const { Option } = Select;

interface BacktestFormProps {
  onBacktestStart: (runId: string) => void;
}

const BacktestForm: React.FC<BacktestFormProps> = ({ onBacktestStart }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      // 构建回测请求
      const request: BacktestRequest = {
        ticker: values.ticker,
        start_date: values.dateRange[0].format('YYYY-MM-DD'),
        end_date: values.dateRange[1].format('YYYY-MM-DD'),
        initial_capital: values.initial_capital || 100000,
        num_of_news: values.num_of_news || 5,
      };

      // 基本回测参数 - 始终包含
      if (values.time_granularity) {
        request.time_granularity = values.time_granularity;
      }
      
      if (values.benchmark_type) {
        request.benchmark_type = values.benchmark_type;
      }
      
      if (values.rebalance_frequency) {
        request.rebalance_frequency = values.rebalance_frequency;
      }

      // 如果启用了高级配置，添加Agent频率和交易成本参数
      if (values.enable_advanced) {
        // Agent频率配置
        request.agent_frequencies = {
          market_data: values.market_data_freq || 'daily',
          technical: values.technical_freq || 'daily',
          fundamentals: values.fundamentals_freq || 'weekly',
          sentiment: values.sentiment_freq || 'daily',
          valuation: values.valuation_freq || 'monthly',
          macro: values.macro_freq || 'weekly',
          portfolio: values.portfolio_freq || 'daily'
        };
        
        if (values.transaction_cost !== undefined) {
          request.transaction_cost = values.transaction_cost;
        }
        
        if (values.slippage !== undefined) {
          request.slippage = values.slippage;
        }
      }

      const response = await ApiService.startBacktest(request);
      if (response.success && response.data) {
        message.success('回测任务已启动！');
        onBacktestStart(response.data.run_id);
        form.resetFields();
      } else {
        message.error(response.message || '启动回测失败');
      }
    } catch (error: any) {
      console.error('Backtest start error:', error);
      message.error(error.response?.data?.detail || '启动回测失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      title={
        <Space>
          <PlayCircleOutlined />
          启动策略回测
        </Space>
      }
      className="feature-card"
      style={{ marginBottom: 24 }}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        className="modern-form"
        initialValues={{
          initial_capital: 100000,
          num_of_news: 5,
          enable_advanced: false,
          market_data_freq: 'daily',
          technical_freq: 'daily',
          fundamentals_freq: 'weekly',
          sentiment_freq: 'daily',
          valuation_freq: 'monthly',
          macro_freq: 'weekly',
          portfolio_freq: 'daily',
          time_granularity: 'daily',
          benchmark_type: 'spe',
          rebalance_frequency: 'daily',
          transaction_cost: 0.001,
          slippage: 0.0005
        }}
      >
        <Form.Item
          name="ticker"
          label="股票代码"
          rules={[
            { required: true, message: '请输入股票代码!' },
            { pattern: /^[0-9]{6}$/, message: '请输入6位数字的股票代码!' }
          ]}
        >
          <Input
            placeholder="例如: 000001"
            maxLength={6}
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          name="dateRange"
          label="回测时间范围"
          rules={[{ required: true, message: '请选择回测时间范围!' }]}
        >
          <RangePicker
            style={{ width: '100%' }}
            format="YYYY-MM-DD"
            disabledDate={(current) => current && current > dayjs().endOf('day')}
            placeholder={['开始日期', '结束日期']}
          />
        </Form.Item>

        <Form.Item
          name="initial_capital"
          label="初始资金"
          rules={[{ required: true, message: '请输入初始资金!' }]}
        >
          <InputNumber
            min={1000}
            max={10000000}
            step={1000}
            formatter={value => `￥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={value => value!.replace(/￥\s?|(,*)/g, '') as any}
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          name="num_of_news"
          label="新闻数量"
          tooltip="用于情感分析的新闻文章数量"
        >
          <InputNumber
            min={1}
            max={100}
            style={{ width: '100%' }}
          />
        </Form.Item>

        {/* 基本回测参数配置 - 始终可见 */}
        <div style={{ marginTop: 24, marginBottom: 24 }}>
          <h4 style={{ marginBottom: 16, color: '#1890ff', fontSize: '16px', fontWeight: 'bold' }}>📊 回测参数配置</h4>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="time_granularity"
                label="时间细粒度"
                tooltip="回测的时间间隔，影响策略执行频率"
              >
                <Select>
                  <Option value="minute">分钟级</Option>
                  <Option value="hourly">小时级</Option>
                  <Option value="daily">日级</Option>
                  <Option value="weekly">周级</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="benchmark_type"
                label="基准策略"
                tooltip="选择用于比较的基准策略"
              >
                <Select placeholder="选择基准策略">
                  <Option value="spe">SPE策略 (买入并持有)</Option>
                  <Option value="csi300">CSI300指数</Option>
                  <Option value="equal_weight">等权重策略</Option>
                  <Option value="momentum">动量策略</Option>
                  <Option value="mean_reversion">均值回归策略</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="rebalance_frequency"
                label="调仓频率"
                tooltip="投资组合重新平衡的频率"
              >
                <Select>
                  <Option value="daily">每日</Option>
                  <Option value="weekly">每周</Option>
                  <Option value="monthly">每月</Option>
                  <Option value="quarterly">每季度</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </div>

        <Collapse ghost>
          <Panel
            header={
              <Space>
                <SettingOutlined />
                高级配置
              </Space>
            }
            key="advanced"
          >
            <Form.Item
              name="enable_advanced"
              valuePropName="checked"
              style={{ marginBottom: 16 }}
            >
              <Switch />
              <span style={{ marginLeft: 8, color: '#666' }}>
                启用自定义Agent频率配置和交易成本设置
              </span>
            </Form.Item>

            <Form.Item
              noStyle
              shouldUpdate={(prevValues, currentValues) =>
                prevValues.enable_advanced !== currentValues.enable_advanced
              }
            >
              {({ getFieldValue }) => {
                const enableAdvanced = getFieldValue('enable_advanced');
                if (!enableAdvanced) return null;

                return (
                  <div style={{ marginTop: 16, padding: '16px', background: '#fafafa', borderRadius: '6px' }}>
                    {/* 交易成本配置 */}
                    <h4 style={{ marginBottom: 16, color: '#52c41a' }}>💰 交易成本配置</h4>
                    <Row gutter={16} style={{ marginBottom: 24 }}>
                      <Col span={12}>
                        <Form.Item
                          name="transaction_cost"
                          label="交易手续费率"
                          tooltip="每笔交易的手续费率 (小数形式，例如 0.001 = 0.1%)"
                        >
                          <InputNumber
                            min={0}
                            max={0.01}
                            step={0.0001}
                            precision={4}
                            formatter={value => `${(Number(value) * 100).toFixed(3)}%`}
                            parser={value => Number(value!.replace('%', '')) / 100 as any}
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          name="slippage"
                          label="滑点率"
                          tooltip="交易时的价格滑点率 (小数形式，例如 0.0005 = 0.05%)"
                        >
                          <InputNumber
                            min={0}
                            max={0.005}
                            step={0.0001}
                            precision={4}
                            formatter={value => `${(Number(value) * 100).toFixed(3)}%`}
                            parser={value => Number(value!.replace('%', '')) / 100 as any}
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                    </Row>

                    {/* Agent频率配置 */}
                    <h4 style={{ marginBottom: 16, color: '#722ed1' }}>🤖 Agent执行频率配置</h4>
                    <div style={{ marginBottom: 16, padding: '8px 12px', background: '#f0f8ff', borderRadius: '4px', fontSize: '12px', color: '#666' }}>
                      <strong>频率说明：</strong> 
                      每日=每个交易日执行 | 
                      每周=每周一执行 | 
                      每月=每月第一个交易日执行 | 
                      条件触发=基于市场波动率和价格变动自动触发
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                      <Form.Item
                        name="market_data_freq"
                        label="市场数据Agent"
                        tooltip="控制市场数据Agent的执行频率"
                      >
                        <Select>
                          <Option value="daily">每日</Option>
                          <Option value="weekly">每周</Option>
                          <Option value="monthly">每月</Option>
                          <Option value="conditional">条件触发</Option>
                        </Select>
                      </Form.Item>

                      <Form.Item
                        name="technical_freq"
                        label="技术分析Agent"
                        tooltip="控制技术分析Agent的执行频率"
                      >
                        <Select>
                          <Option value="daily">每日</Option>
                          <Option value="weekly">每周</Option>
                          <Option value="monthly">每月</Option>
                          <Option value="conditional">条件触发</Option>
                        </Select>
                      </Form.Item>

                      <Form.Item
                        name="fundamentals_freq"
                        label="基本面Agent"
                        tooltip="控制基本面分析Agent的执行频率"
                      >
                        <Select>
                          <Option value="daily">每日</Option>
                          <Option value="weekly">每周</Option>
                          <Option value="monthly">每月</Option>
                          <Option value="conditional">条件触发</Option>
                        </Select>
                      </Form.Item>

                      <Form.Item
                        name="sentiment_freq"
                        label="情感分析Agent"
                        tooltip="控制情感分析Agent的执行频率"
                      >
                        <Select>
                          <Option value="daily">每日</Option>
                          <Option value="weekly">每周</Option>
                          <Option value="monthly">每月</Option>
                          <Option value="conditional">条件触发</Option>
                        </Select>
                      </Form.Item>

                      <Form.Item
                        name="valuation_freq"
                        label="估值分析Agent"
                        tooltip="控制估值分析Agent的执行频率"
                      >
                        <Select>
                          <Option value="daily">每日</Option>
                          <Option value="weekly">每周</Option>
                          <Option value="monthly">每月</Option>
                          <Option value="conditional">条件触发</Option>
                        </Select>
                      </Form.Item>

                      <Form.Item
                        name="macro_freq"
                        label="宏观分析Agent"
                        tooltip="控制宏观分析Agent的执行频率"
                      >
                        <Select>
                          <Option value="daily">每日</Option>
                          <Option value="weekly">每周</Option>
                          <Option value="monthly">每月</Option>
                          <Option value="conditional">条件触发</Option>
                        </Select>
                      </Form.Item>

                      <Form.Item
                        name="portfolio_freq"
                        label="投资组合Agent"
                        tooltip="控制投资组合管理Agent的执行频率"
                      >
                        <Select>
                          <Option value="daily">每日</Option>
                          <Option value="weekly">每周</Option>
                          <Option value="monthly">每月</Option>
                          <Option value="conditional">条件触发</Option>
                        </Select>
                      </Form.Item>
                    </div>
                  </div>
                );
              }}
            </Form.Item>
          </Panel>
        </Collapse>

        <Form.Item style={{ marginTop: 24 }}>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            className="primary-button"
            block
            icon={<PlayCircleOutlined />}
          >
            开始回测
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default BacktestForm;