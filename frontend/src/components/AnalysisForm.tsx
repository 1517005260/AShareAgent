import React, { useState } from 'react';
import { Form, Input, Button, Card, InputNumber, Switch, message } from 'antd';
import { PlayCircleOutlined } from '@ant-design/icons';
import { ApiService, type AnalysisRequest } from '../services/api';

interface AnalysisFormProps {
  onAnalysisStart: (runId: string) => void;
}

const AnalysisForm: React.FC<AnalysisFormProps> = ({ onAnalysisStart }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: AnalysisRequest) => {
    setLoading(true);
    try {
      const response = await ApiService.startAnalysis(values);
      if (response.success && response.data?.run_id) {
        message.success('分析任务已启动');
        onAnalysisStart(response.data.run_id);
        // 不重置表单字段，保持用户输入的数据
        // form.resetFields();
      } else {
        message.error(response.message || '启动分析失败');
      }
    } catch (error) {
      message.error('启动分析失败');
      console.error('Analysis start error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="启动股票分析" className="feature-card mb-4">
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        className="modern-form"
        initialValues={{
          show_reasoning: true,
          num_of_news: 20,
          initial_capital: 100000,
          initial_position: 0
        }}
      >
        <Form.Item
          label="股票代码"
          name="ticker"
          rules={[{ required: true, message: '请输入股票代码' }]}
        >
          <Input placeholder="输入股票代码，如：000001" />
        </Form.Item>

        <Form.Item
          label="显示推理过程"
          name="show_reasoning"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          label="新闻数量"
          name="num_of_news"
        >
          <InputNumber min={1} max={100} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="初始资金"
          name="initial_capital"
        >
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="初始仓位"
          name="initial_position"
        >
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            icon={<PlayCircleOutlined />}
            className="primary-button"
            block
          >
            开始分析
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default AnalysisForm;