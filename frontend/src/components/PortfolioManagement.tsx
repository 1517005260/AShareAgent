import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Table,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Tabs,
  Row,
  Col,
  Tag,
  Space,
  Descriptions,
  Alert
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  TransactionOutlined,
  DollarOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { ApiService } from '../services/api';

const { TextArea } = Input;
const { Option } = Select;

interface Portfolio {
  id: number;
  name: string;
  description?: string;
  initial_capital: number;
  current_value: number;
  cash_balance: number;
  risk_level?: string;
  created_at: string;
  updated_at: string;
}

interface Holding {
  id: number;
  ticker: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_rate: number;
}

interface Transaction {
  id: number;
  ticker: string;
  transaction_type: 'buy' | 'sell';
  quantity: number;
  price: number;
  total_amount: number;
  transaction_date: string;
}

const PortfolioManagement: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 模态框状态
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [transactionModalVisible, setTransactionModalVisible] = useState(false);

  // 表单实例
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [transactionForm] = Form.useForm();

  const [activeTab, setActiveTab] = useState<'overview' | 'holdings' | 'transactions'>('overview');
  const [fetchingPrice, setFetchingPrice] = useState(false);

  const handleGetStockPrice = async (ticker: string) => {
    if (!ticker) return;
    
    try {
      setFetchingPrice(true);
      const response = await ApiService.getStockPrice(ticker);
      if (response.success && response.data?.current_price) {
        transactionForm.setFieldsValue({ price: response.data.current_price });
        message.success(`获取到${ticker}的当前价格: ¥${response.data.current_price}`);
      } else {
        message.warning('无法获取股票价格，请手动输入');
      }
    } catch (err: any) {
      message.error('获取股票价格失败');
    } finally {
      setFetchingPrice(false);
    }
  };

  useEffect(() => {
    loadPortfolios();
  }, []);

  useEffect(() => {
    if (selectedPortfolio) {
      loadPortfolioDetails();
    }
  }, [selectedPortfolio]);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getPortfolios();
      if (response.success && response.data) {
        setPortfolios(response.data);
        if (response.data.length > 0 && !selectedPortfolio) {
          setSelectedPortfolio(response.data[0]);
        }
      } else {
        setError('获取投资组合失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '获取投资组合失败');
    } finally {
      setLoading(false);
    }
  };

  const loadPortfolioDetails = async () => {
    if (!selectedPortfolio) return;

    try {
      // 加载持仓
      const holdingsResponse = await ApiService.getPortfolioHoldings(selectedPortfolio.id);
      if (holdingsResponse.success && holdingsResponse.data) {
        setHoldings(holdingsResponse.data);
      }

      // 加载交易记录
      const transactionsResponse = await ApiService.getTransactions(selectedPortfolio.id);
      if (transactionsResponse.success && transactionsResponse.data) {
        setTransactions(transactionsResponse.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '获取组合详情失败');
    }
  };

  const handleRefreshPrices = async () => {
    if (!selectedPortfolio) return;

    try {
      setLoading(true);
      message.info('正在刷新股票价格...');
      
      const response = await ApiService.updatePortfolioHoldings(selectedPortfolio.id);
      if (response.success) {
        message.success('股票价格刷新成功');
        await loadPortfolioDetails();
        await loadPortfolios();
      } else {
        message.error(response.message || '刷新价格失败');
      }
    } catch (err: any) {
      message.error(err.response?.data?.message || '刷新价格失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePortfolio = async (values: any) => {
    try {
      setLoading(true);
      const response = await ApiService.createPortfolio(values);
      if (response.success && response.data) {
        message.success('投资组合创建成功');
        setCreateModalVisible(false);
        createForm.resetFields();
        await loadPortfolios();
      } else {
        message.error(response.message || '创建失败');
      }
    } catch (err: any) {
      message.error(err.response?.data?.message || '创建失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePortfolio = async (values: any) => {
    if (!selectedPortfolio) return;

    try {
      setLoading(true);
      const response = await ApiService.updatePortfolio(selectedPortfolio.id, values);
      if (response.success && response.data) {
        message.success('投资组合更新成功');
        setEditModalVisible(false);
        editForm.resetFields();
        await loadPortfolios();
        setSelectedPortfolio(response.data);
      } else {
        message.error(response.message || '更新失败');
      }
    } catch (err: any) {
      message.error(err.response?.data?.message || '更新失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePortfolio = async (portfolioId: number) => {
    try {
      setLoading(true);
      const response = await ApiService.deletePortfolio(portfolioId);
      if (response.success) {
        message.success('投资组合删除成功');
        await loadPortfolios();
        if (selectedPortfolio?.id === portfolioId) {
          setSelectedPortfolio(portfolios[0] || null);
        }
      } else {
        message.error(response.message || '删除失败');
      }
    } catch (err: any) {
      message.error(err.response?.data?.message || '删除失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAddTransaction = async (values: any) => {
    if (!selectedPortfolio) return;

    try {
      setLoading(true);
      
      // 获取股票实时价格（如果没有手动输入价格）
      let finalPrice = values.price;
      if (!finalPrice || finalPrice === 0) {
        try {
          const priceResponse = await ApiService.getStockPrice(values.ticker);
          if (priceResponse.success && priceResponse.data?.current_price) {
            finalPrice = priceResponse.data.current_price;
            message.info(`自动获取实时价格: ¥${finalPrice}`);
          }
        } catch (priceErr) {
          console.warn('获取实时价格失败，使用手动输入价格');
        }
      }
      
      const response = await ApiService.addTransaction(selectedPortfolio.id, {
        ...values,
        price: finalPrice,
        total_amount: values.quantity * finalPrice
      });

      if (response.success) {
        message.success('交易记录添加成功');
        setTransactionModalVisible(false);
        transactionForm.resetFields();
        await loadPortfolioDetails();
        await loadPortfolios();
        // 更新持仓价格
        try {
          await ApiService.updatePortfolioHoldings(selectedPortfolio.id);
          await loadPortfolioDetails(); // 重新加载显示更新后的数据
        } catch (updateErr) {
          console.warn('更新持仓价格失败');
        }
      } else {
        message.error(response.message || '添加交易记录失败');
      }
    } catch (err: any) {
      message.error(err.response?.data?.message || '添加交易记录失败');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    if (isNaN(value) || value === null || value === undefined) {
      return '¥0.00';
    }
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY'
    }).format(value);
  };

  const formatPercent = (value: number) => {
    if (isNaN(value) || value === null || value === undefined) {
      return '0.00%';
    }
    return `${(value * 100).toFixed(2)}%`;
  };

  const getReturnColor = (value: number) => {
    return value >= 0 ? 'success' : 'error';
  };

  const holdingsColumns = [
    {
      title: '股票代码',
      dataIndex: 'ticker',
      key: 'ticker',
    },
    {
      title: '持仓数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '平均成本',
      dataIndex: 'avg_cost',
      key: 'avg_cost',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '当前价格',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '市值',
      dataIndex: 'market_value',
      key: 'market_value',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '盈亏',
      key: 'pnl',
      render: (record: Holding) => (
        <Space direction="vertical" size="small">
          <Tag color={getReturnColor(record.unrealized_pnl)}>
            {formatCurrency(record.unrealized_pnl)}
          </Tag>
          <Tag color={getReturnColor(record.unrealized_pnl_rate)}>
            {formatPercent(record.unrealized_pnl_rate / 100)}
          </Tag>
        </Space>
      ),
    },
  ];

  const transactionsColumns = [
    {
      title: '交易时间',
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      render: (date: string) => {
        if (!date) {
          // 如果没有日期，显示当前日期
          return new Date().toLocaleDateString('zh-CN');
        }
        const parsedDate = new Date(date);
        if (isNaN(parsedDate.getTime())) {
          // 如果日期无效，使用当前日期
          return new Date().toLocaleDateString('zh-CN');
        }
        return parsedDate.toLocaleDateString('zh-CN');
      },
    },
    {
      title: '股票代码',
      dataIndex: 'ticker',
      key: 'ticker',
    },
    {
      title: '交易类型',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      render: (type: string) => (
        <Tag color={type === 'buy' ? 'green' : 'red'}>
          {type === 'buy' ? '买入' : '卖出'}
        </Tag>
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
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '总金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (value: number) => formatCurrency(value),
    },
  ];

  if (loading && portfolios.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <div>加载中...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {error && (
        <Alert
          message={error}
          type="error"
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={16}>
        {/* 左侧组合列表 */}
        <Col span={6}>
          <Card
            title="我的投资组合"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setCreateModalVisible(true)}
              >
                创建
              </Button>
            }
          >
            {portfolios.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                暂无投资组合
              </div>
            ) : (
              <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {portfolios.map((portfolio) => (
                  <Card
                    key={portfolio.id}
                    size="small"
                    hoverable
                    onClick={() => setSelectedPortfolio(portfolio)}
                    style={{
                      marginBottom: 8,
                      border: selectedPortfolio?.id === portfolio.id ? '2px solid #1890ff' : '1px solid #d9d9d9'
                    }}
                  >
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{portfolio.name}</div>
                      <div style={{ color: '#666', fontSize: '12px' }}>{portfolio.description}</div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                      <span>当前价值: {formatCurrency(portfolio.current_value)}</span>
                      <Tag color={portfolio.risk_level === 'high' ? 'red' : portfolio.risk_level === 'medium' ? 'orange' : 'green'}>
                        {portfolio.risk_level === 'high' ? '高风险' : portfolio.risk_level === 'medium' ? '中风险' : '低风险'}
                      </Tag>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </Card>
        </Col>

        {/* 右侧详情区域 */}
        <Col span={18}>
          {selectedPortfolio ? (
            <>
              {/* 组合概览卡片 */}
              <Card
                style={{ marginBottom: 16 }}
                title={
                  <Space>
                    <TrophyOutlined />
                    {selectedPortfolio.name}
                  </Space>
                }
                extra={
                  <Space>
                    <Button
                      icon={<EditOutlined />}
                      onClick={() => {
                        editForm.setFieldsValue({
                          name: selectedPortfolio.name,
                          description: selectedPortfolio.description,
                          risk_level: selectedPortfolio.risk_level
                        });
                        setEditModalVisible(true);
                      }}
                    >
                      编辑
                    </Button>
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => {
                        Modal.confirm({
                          title: '确认删除',
                          content: `确定要删除投资组合 "${selectedPortfolio.name}" 吗？`,
                          onOk: () => handleDeletePortfolio(selectedPortfolio.id),
                        });
                      }}
                    >
                      删除
                    </Button>
                  </Space>
                }
              >
                <Row gutter={16}>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                        {formatCurrency(selectedPortfolio.current_value)}
                      </div>
                      <div style={{ color: '#666' }}>当前价值</div>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                        {formatCurrency(selectedPortfolio.initial_capital)}
                      </div>
                      <div style={{ color: '#666' }}>初始资金</div>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#722ed1' }}>
                        {formatCurrency(selectedPortfolio.cash_balance)}
                      </div>
                      <div style={{ color: '#666' }}>现金余额</div>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{
                        fontSize: '24px',
                        fontWeight: 'bold',
                        color: selectedPortfolio.current_value >= selectedPortfolio.initial_capital ? '#52c41a' : '#ff4d4f'
                      }}>
                        {formatPercent((selectedPortfolio.current_value - selectedPortfolio.initial_capital) / selectedPortfolio.initial_capital)}
                      </div>
                      <div style={{ color: '#666' }}>总收益率</div>
                    </div>
                  </Col>
                </Row>
              </Card>

              {/* 详情标签页 */}
              <Card>
                <Tabs
                  activeKey={activeTab}
                  onChange={(key) => setActiveTab(key as any)}
                  tabBarExtraContent={
                    activeTab === 'holdings' ? (
                      <Space>
                        <Button
                          icon={<TransactionOutlined />}
                          onClick={() => setTransactionModalVisible(true)}
                        >
                          添加交易
                        </Button>
                        <Button
                          type="primary"
                          loading={loading}
                          onClick={handleRefreshPrices}
                        >
                          刷新价格
                        </Button>
                      </Space>
                    ) : null
                  }
                  items={[
                    {
                      key: 'overview',
                      label: '概览',
                      children: (
                        <Descriptions bordered column={2}>
                          <Descriptions.Item label="创建时间">
                            {selectedPortfolio.created_at ? 
                              (isNaN(new Date(selectedPortfolio.created_at).getTime()) ? 
                                '无效日期' : 
                                new Date(selectedPortfolio.created_at).toLocaleDateString('zh-CN')) : 
                              '无效日期'}
                          </Descriptions.Item>
                          <Descriptions.Item label="最后更新">
                            {selectedPortfolio.updated_at ? 
                              (isNaN(new Date(selectedPortfolio.updated_at).getTime()) ? 
                                '无效日期' : 
                                new Date(selectedPortfolio.updated_at).toLocaleDateString('zh-CN')) : 
                              '无效日期'}
                          </Descriptions.Item>
                          <Descriptions.Item label="风险等级">
                            <Tag color={selectedPortfolio.risk_level === 'high' ? 'red' : selectedPortfolio.risk_level === 'medium' ? 'orange' : 'green'}>
                              {selectedPortfolio.risk_level === 'high' ? '高风险' : selectedPortfolio.risk_level === 'medium' ? '中风险' : '低风险'}
                            </Tag>
                          </Descriptions.Item>
                          <Descriptions.Item label="描述" span={2}>
                            {selectedPortfolio.description || '暂无描述'}
                          </Descriptions.Item>
                        </Descriptions>
                      ),
                    },
                    {
                      key: 'holdings',
                      label: `持仓 (${holdings.length})`,
                      children: (
                        <Table
                          dataSource={holdings}
                          columns={holdingsColumns}
                          rowKey="id"
                          pagination={false}
                          locale={{ emptyText: '暂无持仓' }}
                        />
                      ),
                    },
                    {
                      key: 'transactions',
                      label: `交易记录 (${transactions.length})`,
                      children: (
                        <Table
                          dataSource={transactions}
                          columns={transactionsColumns}
                          rowKey="id"
                          pagination={{ pageSize: 10 }}
                          locale={{ emptyText: '暂无交易记录' }}
                        />
                      ),
                    },
                  ]}
                />
              </Card>
            </>
          ) : (
            <Card>
              <div style={{ textAlign: 'center', padding: '60px', color: '#999' }}>
                <DollarOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>请选择一个投资组合查看详情</div>
              </div>
            </Card>
          )}
        </Col>
      </Row>

      {/* 创建组合模态框 */}
      <Modal
        title="创建投资组合"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreatePortfolio}
          initialValues={{
            initial_capital: 100000,
            risk_level: 'medium'
          }}
        >
          <Form.Item
            name="name"
            label="组合名称"
            rules={[{ required: true, message: '请输入组合名称' }]}
          >
            <Input placeholder="请输入组合名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="组合描述"
          >
            <TextArea rows={3} placeholder="请输入组合描述" />
          </Form.Item>

          <Form.Item
            name="initial_capital"
            label="初始资金"
            rules={[{ required: true, message: '请输入初始资金' }]}
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
            name="risk_level"
            label="风险等级"
          >
            <Select>
              <Option value="low">低风险</Option>
              <Option value="medium">中等风险</Option>
              <Option value="high">高风险</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setCreateModalVisible(false);
                createForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑组合模态框 */}
      <Modal
        title="编辑投资组合"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          editForm.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdatePortfolio}
        >
          <Form.Item
            name="name"
            label="组合名称"
            rules={[{ required: true, message: '请输入组合名称' }]}
          >
            <Input placeholder="请输入组合名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="组合描述"
          >
            <TextArea rows={3} placeholder="请输入组合描述" />
          </Form.Item>

          <Form.Item
            name="risk_level"
            label="风险等级"
          >
            <Select>
              <Option value="low">低风险</Option>
              <Option value="medium">中等风险</Option>
              <Option value="high">高风险</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setEditModalVisible(false);
                editForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                更新
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 添加交易模态框 */}
      <Modal
        title="添加交易记录"
        open={transactionModalVisible}
        onCancel={() => {
          setTransactionModalVisible(false);
          transactionForm.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form
          form={transactionForm}
          layout="vertical"
          onFinish={handleAddTransaction}
          initialValues={{
            transaction_type: 'buy',
            quantity: 100,
            price: 10
          }}
        >
          <Form.Item
            name="ticker"
            label="股票代码"
            rules={[{ required: true, message: '请输入股票代码' }]}
          >
            <Input.Search
              placeholder="例如: 000001"
              maxLength={6}
              enterButton="获取价格"
              loading={fetchingPrice}
              onSearch={handleGetStockPrice}
            />
          </Form.Item>

          <Form.Item
            name="transaction_type"
            label="交易类型"
            rules={[{ required: true, message: '请选择交易类型' }]}
          >
            <Select>
              <Option value="buy">买入</Option>
              <Option value="sell">卖出</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="quantity"
            label="数量"
            rules={[{ required: true, message: '请输入数量' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="price"
            label="价格"
            rules={[{ required: true, message: '请输入价格' }]}
            extra="可以先输入股票代码点击'获取价格'自动填入当前价格"
          >
            <InputNumber 
              min={0.01} 
              step={0.01} 
              style={{ width: '100%' }} 
              placeholder="0.00"
              formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value!.replace(/¥\s?|(,*)/g, '') as any}
            />
          </Form.Item>

          <Form.Item
            label="总金额"
            dependencies={['quantity', 'price']}
          >
            <Form.Item noStyle shouldUpdate>
              {({ getFieldValue }) => {
                const quantity = getFieldValue('quantity') || 0;
                const price = getFieldValue('price') || 0;
                const total = quantity * price;
                return (
                  <InputNumber 
                    value={total}
                    disabled
                    style={{ width: '100%' }}
                    formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                    parser={value => value!.replace(/¥\s?|(,*)/g, '') as any}
                  />
                );
              }}
            </Form.Item>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setTransactionModalVisible(false);
                transactionForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                添加
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PortfolioManagement;