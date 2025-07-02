import { useState } from 'react';
import { Layout, Menu, Typography, Space, Divider } from 'antd';
import { 
  DashboardOutlined, 
  RobotOutlined, 
  HistoryOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import AnalysisForm from './components/AnalysisForm';
import AnalysisStatus from './components/AnalysisStatus';
import AgentDashboard from './components/AgentDashboard';
import HistoryDashboard from './components/HistoryDashboard';
import 'antd/dist/reset.css';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

type MenuKey = 'dashboard' | 'agents' | 'history';

function App() {
  const [selectedMenu, setSelectedMenu] = useState<MenuKey>('dashboard');
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);

  const handleAnalysisStart = (runId: string) => {
    setCurrentRunId(runId);
  };

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
          </Space>
        );
      case 'agents':
        return <AgentDashboard />;
      case 'history':
        return <HistoryDashboard />;
      default:
        return <div>页面未找到</div>;
    }
  };

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '分析控制台',
    },
    {
      key: 'agents',
      icon: <RobotOutlined />,
      label: 'Agent管理',
    },
    {
      key: 'history',
      icon: <HistoryOutlined />,
      label: '历史记录',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#001529',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center'
      }}>
        <div style={{ 
          color: 'white', 
          fontSize: '20px', 
          fontWeight: 'bold',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <BarChartOutlined style={{ fontSize: '24px' }} />
          A股投资Agent监控平台
        </div>
      </Header>
      
      <Layout>
        <Sider 
          width={200} 
          style={{ background: '#fff' }}
          breakpoint="lg"
          collapsedWidth="0"
        >
          <Menu
            mode="inline"
            selectedKeys={[selectedMenu]}
            items={menuItems}
            style={{ height: '100%', borderRight: 0 }}
            onSelect={({ key }) => setSelectedMenu(key as MenuKey)}
          />
        </Sider>
        
        <Layout style={{ padding: '24px' }}>
          <Content
            style={{
              padding: '24px',
              margin: 0,
              minHeight: 280,
              background: '#fff',
              borderRadius: '8px',
            }}
          >
            <Title level={2} style={{ marginBottom: '24px' }}>
              {menuItems.find(item => item.key === selectedMenu)?.label}
            </Title>
            <Divider style={{ margin: '0 0 24px 0' }} />
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
