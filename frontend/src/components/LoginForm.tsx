import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Tabs } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';
import ApiService, { type LoginRequest, type RegisterRequest } from '../services/api';

interface LoginFormProps {
  onLoginSuccess: (userInfo: any) => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');

  const handleLogin = async (values: LoginRequest) => {
    setLoading(true);
    try {
      const response = await ApiService.login(values);
      if (response.success && response.data) {
        localStorage.setItem('auth_token', response.data.access_token);
        localStorage.setItem('user_info', JSON.stringify(response.data.user));
        message.success('登录成功！');
        onLoginSuccess(response.data.user);
      } else {
        message.error(response.message || '登录失败');
      }
    } catch (error: any) {
      console.error('Login error:', error);
      message.error(error.response?.data?.message || '登录失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: RegisterRequest) => {
    setLoading(true);
    try {
      const response = await ApiService.register(values);
      if (response.success) {
        message.success('注册成功！请登录');
        setActiveTab('login');
      } else {
        message.error(response.message || '注册失败');
      }
    } catch (error: any) {
      console.error('Register error:', error);
      message.error(error.response?.data?.message || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  const loginForm = (
    <Form
      name="login"
      onFinish={handleLogin}
      autoComplete="off"
      size="large"
      className="modern-form"
    >
      <Form.Item
        name="username"
        rules={[{ required: true, message: '请输入用户名!' }]}
      >
        <Input 
          prefix={<UserOutlined />} 
          placeholder="用户名" 
          autoComplete="username"
        />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[{ required: true, message: '请输入密码!' }]}
      >
        <Input.Password 
          prefix={<LockOutlined />} 
          placeholder="密码"
          autoComplete="current-password"
        />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} className="primary-button" block>
          登录
        </Button>
      </Form.Item>
    </Form>
  );

  const registerForm = (
    <Form
      name="register"
      onFinish={handleRegister}
      autoComplete="off"
      size="large"
      className="modern-form"
    >
      <Form.Item
        name="username"
        rules={[
          { required: true, message: '请输入用户名!' },
          { min: 3, message: '用户名至少3个字符!' }
        ]}
      >
        <Input 
          prefix={<UserOutlined />} 
          placeholder="用户名" 
          autoComplete="username"
        />
      </Form.Item>

      <Form.Item
        name="email"
        rules={[
          { required: true, message: '请输入邮箱!' },
          { type: 'email', message: '请输入有效的邮箱地址!' }
        ]}
      >
        <Input 
          prefix={<MailOutlined />} 
          placeholder="邮箱" 
          autoComplete="email"
        />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[
          { required: true, message: '请输入密码!' },
          { min: 8, message: '密码至少8个字符!' }
        ]}
      >
        <Input.Password 
          prefix={<LockOutlined />} 
          placeholder="密码"
          autoComplete="new-password"
        />
      </Form.Item>

      <Form.Item
        name="confirm"
        dependencies={['password']}
        rules={[
          { required: true, message: '请确认密码!' },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('password') === value) {
                return Promise.resolve();
              }
              return Promise.reject(new Error('两次输入的密码不一致!'));
            },
          }),
        ]}
      >
        <Input.Password 
          prefix={<LockOutlined />} 
          placeholder="确认密码"
          autoComplete="new-password"
        />
      </Form.Item>

      <Form.Item
        name="full_name"
      >
        <Input 
          prefix={<UserOutlined />} 
          placeholder="真实姓名（可选）" 
          autoComplete="name"
        />
      </Form.Item>

      <Form.Item
        name="phone"
      >
        <Input 
          prefix={<PhoneOutlined />} 
          placeholder="手机号码（可选）" 
          autoComplete="tel"
        />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} className="primary-button" block>
          注册
        </Button>
      </Form.Item>
    </Form>
  );

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
      padding: '20px'
    }}>
      <Card 
        className="feature-card"
        style={{ 
          width: 420,
          maxWidth: '100%',
          boxShadow: '0 16px 48px rgba(0,0,0,0.2)'
        }}
        title={
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ margin: 0, color: '#1890ff', fontSize: '24px' }}>
              A股投资Agent系统
            </h2>
          </div>
        }
      >
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          centered
          items={[
            {
              key: 'login',
              label: '登录',
              children: loginForm,
            },
            {
              key: 'register',
              label: '注册',
              children: registerForm,
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default LoginForm;