import React, { useState, useEffect } from 'react';
import { ApiService } from '../services/api';

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
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-lg">加载个人统计中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">个人统计摘要</h2>
        <div className="flex space-x-2">
          {[
            { key: '7d', label: '7天' },
            { key: '30d', label: '30天' },
            { key: '90d', label: '90天' },
            { key: 'all', label: '全部' }
          ].map((period) => (
            <button
              key={period.key}
              onClick={() => setTimeRange(period.key as any)}
              className={`px-3 py-1 text-sm rounded ${
                timeRange === period.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {period.label}
            </button>
          ))}
        </div>
      </div>

      {summary ? (
        <div className="space-y-6">
          {/* 总体统计 */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <div className="text-3xl font-bold text-blue-600">
                {summary.user_stats?.total_analyses || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">分析次数</div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <div className="text-3xl font-bold text-green-600">
                {summary.user_stats?.total_backtests || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">回测次数</div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <div className="text-3xl font-bold text-purple-600">
                {summary.user_stats?.total_portfolios || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">投资组合</div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <div className="text-3xl font-bold text-orange-600">
                {formatPercent(summary.user_stats?.success_rate || 0)}
              </div>
              <div className="text-sm text-gray-600 mt-1">成功率</div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <div className={`text-3xl font-bold ${getReturnColor(summary.user_stats?.avg_return || 0)}`}>
                {formatPercent(summary.user_stats?.avg_return || 0)}
              </div>
              <div className="text-sm text-gray-600 mt-1">平均收益率</div>
            </div>
          </div>

          {/* 投资表现摘要 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">投资表现</h3>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {formatCurrency(summary.performance_summary?.total_invested || 0)}
                </div>
                <div className="text-sm text-gray-600">总投资金额</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(summary.performance_summary?.current_value || 0)}
                </div>
                <div className="text-sm text-gray-600">当前总价值</div>
              </div>
              
              <div className="text-center">
                <div className={`text-2xl font-bold ${getReturnColor(summary.performance_summary?.profit_loss || 0)}`}>
                  {formatCurrency(summary.performance_summary?.profit_loss || 0)}
                </div>
                <div className="text-sm text-gray-600">总盈亏</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {formatPercent(summary.performance_summary?.best_return || 0)}
                </div>
                <div className="text-sm text-gray-600">最佳收益率</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {formatPercent(summary.performance_summary?.worst_return || 0)}
                </div>
                <div className="text-sm text-gray-600">最差收益率</div>
              </div>
            </div>
          </div>

          {/* 最近活动 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 最近分析 */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h4 className="font-semibold">最近分析</h4>
              </div>
              <div className="p-4">
                {(summary.recent_activity?.analyses || []).length === 0 ? (
                  <div className="text-center text-gray-500 py-4">
                    暂无分析记录
                  </div>
                ) : (
                  <div className="space-y-3">
                    {(summary.recent_activity?.analyses || []).slice(0, 5).map((analysis, index) => (
                      <div key={index} className="flex justify-between items-center text-sm">
                        <div>
                          <div className="font-medium">{analysis.ticker || analysis.stock_code}</div>
                          <div className="text-gray-500">
                            {analysis.created_at ? new Date(analysis.created_at).toLocaleDateString('zh-CN') : ''}
                          </div>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs ${
                          analysis.status === 'completed' ? 'bg-green-100 text-green-800' :
                          analysis.status === 'running' ? 'bg-blue-100 text-blue-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {analysis.status === 'completed' ? '完成' :
                           analysis.status === 'running' ? '运行中' : '失败'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 最近回测 */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h4 className="font-semibold">最近回测</h4>
              </div>
              <div className="p-4">
                {(summary.recent_activity?.backtests || []).length === 0 ? (
                  <div className="text-center text-gray-500 py-4">
                    暂无回测记录
                  </div>
                ) : (
                  <div className="space-y-3">
                    {(summary.recent_activity?.backtests || []).slice(0, 5).map((backtest, index) => (
                      <div key={index} className="flex justify-between items-center text-sm">
                        <div>
                          <div className="font-medium">{backtest.ticker}</div>
                          <div className="text-gray-500">
                            {backtest.created_at ? new Date(backtest.created_at).toLocaleDateString('zh-CN') : ''}
                          </div>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs ${
                          backtest.status === 'completed' ? 'bg-green-100 text-green-800' :
                          backtest.status === 'running' ? 'bg-blue-100 text-blue-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {backtest.status === 'completed' ? '完成' :
                           backtest.status === 'running' ? '运行中' : '失败'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 投资组合状态 */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h4 className="font-semibold">投资组合</h4>
              </div>
              <div className="p-4">
                {(summary.recent_activity?.portfolios || []).length === 0 ? (
                  <div className="text-center text-gray-500 py-4">
                    暂无投资组合
                  </div>
                ) : (
                  <div className="space-y-3">
                    {(summary.recent_activity?.portfolios || []).slice(0, 5).map((portfolio, index) => (
                      <div key={index} className="text-sm">
                        <div className="flex justify-between items-center">
                          <div className="font-medium">{portfolio.name}</div>
                          <div className={`${getReturnColor(portfolio.profit_loss_percent || 0)}`}>
                            {formatPercent(portfolio.profit_loss_percent || 0)}
                          </div>
                        </div>
                        <div className="text-gray-500 text-xs">
                          {formatCurrency(portfolio.current_value || 0)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center text-gray-500 py-8">
            暂无统计数据
          </div>
        </div>
      )}
    </div>
  );
};

export default PersonalStats;