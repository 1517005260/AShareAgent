import React, { useState, useEffect } from 'react';
import { ApiService } from '../services/api';

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
  average_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

interface Transaction {
  id: number;
  ticker: string;
  transaction_type: 'buy' | 'sell';
  quantity: number;
  price: number;
  total_amount: number;
  created_at: string;
}

const PortfolioManagement: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 创建组合表单
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createFormData, setCreateFormData] = useState({
    name: '',
    description: '',
    initial_capital: 100000,
    risk_level: 'medium'
  });

  // 编辑组合表单
  const [showEditForm, setShowEditForm] = useState(false);
  const [editFormData, setEditFormData] = useState({
    name: '',
    description: '',
    risk_level: 'medium'
  });

  // 添加交易表单
  const [showTransactionForm, setShowTransactionForm] = useState(false);
  const [transactionFormData, setTransactionFormData] = useState({
    ticker: '',
    transaction_type: 'buy' as 'buy' | 'sell',
    quantity: 0,
    price: 0
  });

  const [activeTab, setActiveTab] = useState<'overview' | 'holdings' | 'transactions'>('overview');

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

  const handleCreatePortfolio = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await ApiService.createPortfolio(createFormData);
      if (response.success && response.data) {
        setSuccess('投资组合创建成功');
        setShowCreateForm(false);
        setCreateFormData({
          name: '',
          description: '',
          initial_capital: 100000,
          risk_level: 'medium'
        });
        await loadPortfolios();
      } else {
        setError(response.message || '创建失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '创建失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePortfolio = async () => {
    if (!selectedPortfolio) return;

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await ApiService.updatePortfolio(selectedPortfolio.id, editFormData);
      if (response.success && response.data) {
        setSuccess('投资组合更新成功');
        setShowEditForm(false);
        await loadPortfolios();
        // 更新选中的组合
        const updatedPortfolio = portfolios.find(p => p.id === selectedPortfolio.id);
        if (updatedPortfolio) {
          setSelectedPortfolio(updatedPortfolio);
        }
      } else {
        setError(response.message || '更新失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '更新失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePortfolio = async (portfolioId: number) => {
    if (!confirm('确定要删除这个投资组合吗？')) return;

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await ApiService.deletePortfolio(portfolioId);
      if (response.success) {
        setSuccess('投资组合删除成功');
        await loadPortfolios();
        if (selectedPortfolio?.id === portfolioId) {
          setSelectedPortfolio(portfolios[0] || null);
        }
      } else {
        setError(response.message || '删除失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '删除失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAddTransaction = async () => {
    if (!selectedPortfolio) return;

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await ApiService.addTransaction(selectedPortfolio.id, {
        ...transactionFormData,
        total_amount: transactionFormData.quantity * transactionFormData.price
      });

      if (response.success) {
        setSuccess('交易记录添加成功');
        setShowTransactionForm(false);
        setTransactionFormData({
          ticker: '',
          transaction_type: 'buy',
          quantity: 0,
          price: 0
        });
        await loadPortfolioDetails();
        await loadPortfolios(); // 刷新组合数据
      } else {
        setError(response.message || '添加交易记录失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '添加交易记录失败');
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

  if (loading && portfolios.length === 0) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-lg">加载中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">投资组合管理</h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          创建新组合
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 左侧组合列表 */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-lg font-semibold mb-4">我的组合</h3>
            
            {portfolios.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                暂无投资组合
              </div>
            ) : (
              <div className="space-y-2">
                {portfolios.map((portfolio) => (
                  <div
                    key={portfolio.id}
                    onClick={() => setSelectedPortfolio(portfolio)}
                    className={`p-3 rounded border cursor-pointer hover:bg-gray-50 ${
                      selectedPortfolio?.id === portfolio.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200'
                    }`}
                  >
                    <div className="font-medium">{portfolio.name}</div>
                    <div className="text-sm text-gray-600">
                      {formatCurrency(portfolio.current_value)}
                    </div>
                    <div className="text-xs text-gray-400">
                      风险等级: {portfolio.risk_level}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 右侧详情区域 */}
        <div className="lg:col-span-3">
          {selectedPortfolio ? (
            <>
              {/* 组合概览 */}
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-semibold">{selectedPortfolio.name}</h3>
                    <p className="text-gray-600">{selectedPortfolio.description}</p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => {
                        setEditFormData({
                          name: selectedPortfolio.name,
                          description: selectedPortfolio.description || '',
                          risk_level: selectedPortfolio.risk_level || 'medium'
                        });
                        setShowEditForm(true);
                      }}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => handleDeletePortfolio(selectedPortfolio.id)}
                      className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      删除
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {formatCurrency(selectedPortfolio.current_value)}
                    </div>
                    <div className="text-sm text-gray-600">当前价值</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {formatCurrency(selectedPortfolio.initial_capital)}
                    </div>
                    <div className="text-sm text-gray-600">初始资金</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {formatCurrency(selectedPortfolio.cash_balance)}
                    </div>
                    <div className="text-sm text-gray-600">现金余额</div>
                  </div>
                  <div className="text-center">
                    <div className={`text-2xl font-bold ${
                      selectedPortfolio.current_value >= selectedPortfolio.initial_capital
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}>
                      {formatPercent(
                        (selectedPortfolio.current_value - selectedPortfolio.initial_capital) / 
                        selectedPortfolio.initial_capital
                      )}
                    </div>
                    <div className="text-sm text-gray-600">总收益率</div>
                  </div>
                </div>
              </div>

              {/* 标签页 */}
              <div className="bg-white rounded-lg shadow">
                <div className="border-b">
                  <nav className="flex space-x-8 px-6">
                    {[
                      { key: 'overview', label: '概览' },
                      { key: 'holdings', label: '持仓' },
                      { key: 'transactions', label: '交易记录' }
                    ].map((tab) => (
                      <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key as any)}
                        className={`py-4 px-1 border-b-2 font-medium text-sm ${
                          activeTab === tab.key
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </nav>
                </div>

                <div className="p-6">
                  {activeTab === 'overview' && (
                    <div>
                      <h4 className="text-lg font-semibold mb-4">组合概览</h4>
                      <div className="text-gray-600">
                        <p>创建时间: {new Date(selectedPortfolio.created_at).toLocaleDateString('zh-CN')}</p>
                        <p>最后更新: {new Date(selectedPortfolio.updated_at).toLocaleDateString('zh-CN')}</p>
                        <p>风险等级: {selectedPortfolio.risk_level}</p>
                      </div>
                    </div>
                  )}

                  {activeTab === 'holdings' && (
                    <div>
                      <div className="flex justify-between items-center mb-4">
                        <h4 className="text-lg font-semibold">持仓详情</h4>
                        <button
                          onClick={() => setShowTransactionForm(true)}
                          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                        >
                          添加交易
                        </button>
                      </div>
                      
                      {holdings.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                          暂无持仓
                        </div>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  股票代码
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  持仓数量
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  平均成本
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  当前价格
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  市值
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  盈亏
                                </th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {holdings.map((holding) => (
                                <tr key={holding.id}>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {holding.ticker}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {holding.quantity}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {formatCurrency(holding.average_price)}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {formatCurrency(holding.current_price)}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {formatCurrency(holding.market_value)}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    <span className={holding.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                                      {formatCurrency(holding.unrealized_pnl)} 
                                      ({formatPercent(holding.unrealized_pnl_percent)})
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'transactions' && (
                    <div>
                      <h4 className="text-lg font-semibold mb-4">交易记录</h4>
                      
                      {transactions.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                          暂无交易记录
                        </div>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  交易时间
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  股票代码
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  交易类型
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  数量
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  价格
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  总金额
                                </th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {transactions.map((transaction) => (
                                <tr key={transaction.id}>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {new Date(transaction.created_at).toLocaleDateString('zh-CN')}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {transaction.ticker}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    <span className={`px-2 py-1 text-xs rounded-full ${
                                      transaction.transaction_type === 'buy'
                                        ? 'bg-green-100 text-green-800'
                                        : 'bg-red-100 text-red-800'
                                    }`}>
                                      {transaction.transaction_type === 'buy' ? '买入' : '卖出'}
                                    </span>
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {transaction.quantity}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {formatCurrency(transaction.price)}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {formatCurrency(transaction.total_amount)}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-center text-gray-500 py-8">
                请选择一个投资组合查看详情
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 创建组合模态框 */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">创建投资组合</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  组合名称
                </label>
                <input
                  type="text"
                  value={createFormData.name}
                  onChange={(e) => setCreateFormData({ ...createFormData, name: e.target.value })}
                  placeholder="请输入组合名称"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  组合描述
                </label>
                <textarea
                  value={createFormData.description}
                  onChange={(e) => setCreateFormData({ ...createFormData, description: e.target.value })}
                  placeholder="请输入组合描述"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  初始资金
                </label>
                <input
                  type="number"
                  value={createFormData.initial_capital}
                  onChange={(e) => setCreateFormData({ ...createFormData, initial_capital: Number(e.target.value) })}
                  placeholder="请输入初始资金"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  风险等级
                </label>
                <select
                  value={createFormData.risk_level}
                  onChange={(e) => setCreateFormData({ ...createFormData, risk_level: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="low">低风险</option>
                  <option value="medium">中等风险</option>
                  <option value="high">高风险</option>
                </select>
              </div>
            </div>

            <div className="mt-6 flex space-x-2">
              <button
                onClick={handleCreatePortfolio}
                disabled={loading || !createFormData.name}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '创建中...' : '创建'}
              </button>
              <button
                onClick={() => setShowCreateForm(false)}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑组合模态框 */}
      {showEditForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">编辑投资组合</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  组合名称
                </label>
                <input
                  type="text"
                  value={editFormData.name}
                  onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                  placeholder="请输入组合名称"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  组合描述
                </label>
                <textarea
                  value={editFormData.description}
                  onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                  placeholder="请输入组合描述"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  风险等级
                </label>
                <select
                  value={editFormData.risk_level}
                  onChange={(e) => setEditFormData({ ...editFormData, risk_level: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="low">低风险</option>
                  <option value="medium">中等风险</option>
                  <option value="high">高风险</option>
                </select>
              </div>
            </div>

            <div className="mt-6 flex space-x-2">
              <button
                onClick={handleUpdatePortfolio}
                disabled={loading || !editFormData.name}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '更新中...' : '更新'}
              </button>
              <button
                onClick={() => setShowEditForm(false)}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 添加交易模态框 */}
      {showTransactionForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">添加交易记录</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  股票代码
                </label>
                <input
                  type="text"
                  value={transactionFormData.ticker}
                  onChange={(e) => setTransactionFormData({ ...transactionFormData, ticker: e.target.value.toUpperCase() })}
                  placeholder="例如: 000001"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  交易类型
                </label>
                <select
                  value={transactionFormData.transaction_type}
                  onChange={(e) => setTransactionFormData({ ...transactionFormData, transaction_type: e.target.value as 'buy' | 'sell' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="buy">买入</option>
                  <option value="sell">卖出</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  数量
                </label>
                <input
                  type="number"
                  value={transactionFormData.quantity}
                  onChange={(e) => setTransactionFormData({ ...transactionFormData, quantity: Number(e.target.value) })}
                  placeholder="请输入股票数量"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  价格
                </label>
                <input
                  type="number"
                  value={transactionFormData.price}
                  onChange={(e) => setTransactionFormData({ ...transactionFormData, price: Number(e.target.value) })}
                  placeholder="请输入交易价格"
                  min="0"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm text-gray-600">
                  总金额: {formatCurrency(transactionFormData.quantity * transactionFormData.price)}
                </div>
              </div>
            </div>

            <div className="mt-6 flex space-x-2">
              <button
                onClick={handleAddTransaction}
                disabled={loading || !transactionFormData.ticker || transactionFormData.quantity <= 0 || transactionFormData.price <= 0}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? '添加中...' : '添加交易'}
              </button>
              <button
                onClick={() => setShowTransactionForm(false)}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioManagement;