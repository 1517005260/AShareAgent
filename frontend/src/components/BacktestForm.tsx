import React, { useState } from 'react';
import { Form, Input, Button, DatePicker, InputNumber, Card, message, Collapse, Space } from 'antd';
import { PlayCircleOutlined, SettingOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import ApiService, { type BacktestRequest } from '../services/api';

const { RangePicker } = DatePicker;
const { Panel } = Collapse;

interface BacktestFormProps {
  onBacktestStart: (runId: string) => void;
}

const BacktestForm: React.FC<BacktestFormProps> = ({ onBacktestStart }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const request: BacktestRequest = {
        ticker: values.ticker,
        start_date: values.dateRange[0].format('YYYY-MM-DD'),
        end_date: values.dateRange[1].format('YYYY-MM-DD'),
        initial_capital: values.initial_capital || 100000,
        num_of_news: values.num_of_news || 5,
        agent_frequencies: values.enable_advanced ? values.agent_frequencies : undefined,
      };

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

  const defaultAgentFrequencies = {
    market_data: 'daily',
    technical: 'daily',
    fundamentals: 'weekly',
    sentiment: 'daily',
    valuation: 'monthly',
    macro: 'weekly',
    portfolio: 'daily'
  };

  return (
    <Card 
      title={
        <Space>
          <PlayCircleOutlined />
          启动回测
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
          agent_frequencies: defaultAgentFrequencies
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
            >
              <span style={{ color: '#666' }}>
                启用自定义Agent频率配置（默认使用系统推荐配置）
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
                  <div style={{ marginTop: 16 }}>
                    <h4>Agent执行频率配置</h4>
                    {Object.entries(defaultAgentFrequencies).map(([agent, defaultFreq]) => (
                      <Form.Item
                        key={agent}
                        name={['agent_frequencies', agent]}
                        label={`${agent} Agent`}
                        initialValue={defaultFreq}
                      >
                        <Input 
                          placeholder="daily/weekly/monthly" 
                          style={{ width: '100%' }}
                        />
                      </Form.Item>
                    ))}
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