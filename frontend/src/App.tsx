import { useState, useEffect } from 'react';
import { Layout, Menu, Typography, Space, Button, Avatar, Dropdown } from 'antd';
import { 
  DashboardOutlined, 
  RobotOutlined, 
  HistoryOutlined,
  BarChartOutlined,
  ExperimentOutlined,
  UserOutlined,
  LogoutOutlined,
  FundOutlined,
  MonitorOutlined,
  SettingOutlined,
  LineChartOutlined
} from '@ant-design/icons';
import AnalysisForm from './components/AnalysisForm';
import AnalysisStatus from './components/AnalysisStatus';
import AgentDashboard from './components/AgentDashboard';
import HistoryDashboard from './components/HistoryDashboard';
import LoginForm from './components/LoginForm';
import BacktestForm from './components/BacktestForm';
import BacktestStatus from './components/BacktestStatus';
import UserProfile from './components/UserProfile';
import PortfolioManagement from './components/PortfolioManagement';
import SystemMonitor from './components/SystemMonitor';
import PersonalStats from './components/PersonalStats';
import ApiService, { type UserInfo } from './services/api';
import 'antd/dist/reset.css';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

type MenuKey = 'dashboard' | 'backtest' | 'agents' | 'history' | 'portfolios' | 'monitor' | 'stats' | 'profile';

function App() {
  const [selectedMenu, setSelectedMenu] = useState<MenuKey>('dashboard');
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [currentBacktestId, setCurrentBacktestId] = useState<string | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // 检查用户是否已登录
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          const response = await ApiService.getCurrentUser();
          if (response.success && response.data) {
            setUser(response.data);
            setIsAuthenticated(true);
          } else {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
          }
        } catch (error) {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user_info');
        }
      }
    };
    checkAuth();
  }, []);

  const handleAnalysisStart = (runId: string) => {
    setCurrentRunId(runId);
  };

  const handleBacktestStart = (runId: string) => {
    setCurrentBacktestId(runId);
    setSelectedMenu('backtest');
  };

  const handleLoginSuccess = (userInfo: UserInfo) => {
    setUser(userInfo);
    setIsAuthenticated(true);
  };

  const handleLogout = async () => {
    await ApiService.logout();
    setUser(null);
    setIsAuthenticated(false);
    setSelectedMenu('dashboard');
    setCurrentRunId(null);
    setCurrentBacktestId(null);
  };

  // 检查用户权限
  const hasPermission = (permission: string): boolean => {
    return user?.permissions?.includes(permission) || 
           user?.roles?.includes('admin') || false;
  };

  // 如果未登录，显示登录页面
  if (!isAuthenticated) {
    return <LoginForm onLoginSuccess={handleLoginSuccess} />;
  }

  const renderContent = () => {
    switch (selectedMenu) {
      case 'dashboard':
        return (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <AnalysisForm onAnalysisStart={handleAnalysisStart} />
            {currentRunId && (
              <AnalysisStatus 
                runId={currentRunId} 
                onComplete={(result) => console.log('Analysis completed:', result)}
              />
            )}
            {hasPermission('backtest:basic') && (
              <BacktestForm onBacktestStart={handleBacktestStart} />
            )}
          </Space>
        );
      case 'backtest':
        return (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {hasPermission('backtest:basic') && (
              <>
                <BacktestForm onBacktestStart={handleBacktestStart} />
                {currentBacktestId && (
                  <BacktestStatus 
                    runId={currentBacktestId} 
                    onComplete={(result) => console.log('Backtest completed:', result)}
                  />
                )}
              </>
            )}
            {!hasPermission('backtest:basic') && (
              <div className="permission-error">
                <Title level={3}>权限不足</Title>
                <p>您没有访问回测功能的权限</p>
              </div>
            )}
          </Space>
        );
      case 'agents':
        return hasPermission('system:monitor') ? (
          <AgentDashboard />
        ) : (
          <div className="permission-error">
            <Title level={3}>权限不足</Title>
            <p>您没有访问Agent管理功能的权限</p>
          </div>
        );
      case 'history':
        return <HistoryDashboard />;
      case 'portfolios':
        return hasPermission('portfolio:read') ? (
          <PortfolioManagement />
        ) : (
          <div className="permission-error">
            <Title level={3}>权限不足</Title>
            <p>您没有访问投资组合功能的权限</p>
          </div>
        );
      case 'monitor':
        return hasPermission('system:monitor') ? (
          <SystemMonitor />
        ) : (
          <div className="permission-error">
            <Title level={3}>权限不足</Title>
            <p>您没有访问系统监控功能的权限</p>
          </div>
        );
      case 'stats':
        return <PersonalStats />;
      case 'profile':
        return <UserProfile onUserUpdate={setUser} />;
      default:
        return <div>页面未找到</div>;
    }
  };

  // 根据权限动态生成菜单项
  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '股票分析',
    },
    ...(hasPermission('backtest:basic') ? [{
      key: 'backtest',
      icon: <ExperimentOutlined />,
      label: '策略回测',
    }] : []),
    ...(hasPermission('portfolio:read') ? [{
      key: 'portfolios',
      icon: <FundOutlined />,
      label: '投资组合',
    }] : []),
    ...(hasPermission('system:monitor') ? [{
      key: 'agents',
      icon: <RobotOutlined />,
      label: 'Agent管理',
    }] : []),
    {
      key: 'history',
      icon: <HistoryOutlined />,
      label: '历史记录',
    },
    {
      key: 'stats',
      icon: <LineChartOutlined />,
      label: '个人统计',
    },
    ...(hasPermission('system:monitor') ? [{
      key: 'monitor',
      icon: <MonitorOutlined />,
      label: '系统监控',
    }] : []),
    {
      key: 'profile',
      icon: <SettingOutlined />,
      label: '个人设置',
    },
  ];

  // 用户菜单
  const userMenu = {
    items: [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        onClick: handleLogout,
      },
    ],
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <Header className="app-header" style={{ 
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div className="logo">
          <BarChartOutlined className="logo-icon" />
          A股投资Agent分析平台
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ color: 'white' }}>
            欢迎，{user?.full_name || user?.username}
          </span>
          <Dropdown menu={userMenu} placement="bottomRight">
            <Button 
              type="text" 
              icon={<Avatar size="small" icon={<UserOutlined />} />}
              style={{ color: 'white' }}
            />
          </Dropdown>
        </div>
      </Header>
      
      <Layout>
        <Sider 
          width={200} 
          className="app-sider"
          breakpoint="lg"
          collapsedWidth="0"
        >
          <Menu
            mode="inline"
            selectedKeys={[selectedMenu]}
            items={menuItems}
            className="app-menu"
            style={{ height: '100%' }}
            onSelect={({ key }) => setSelectedMenu(key as MenuKey)}
          />
        </Sider>
        
        <Layout style={{ padding: '16px', background: '#f5f5f5' }}>
          <Content className="app-content">
            <div className="app-content-header">
              <Title level={2} style={{ margin: 0, color: '#262626' }}>
                {menuItems.find(item => item.key === selectedMenu)?.label}
              </Title>
            </div>
            <div className="app-content-body fade-in-up">
              {renderContent()}
            </div>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
