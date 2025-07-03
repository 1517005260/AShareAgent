import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Row,
  Col,
  Descriptions,
  Alert,
  Space,
  Tag,
  Avatar
} from 'antd';
import {
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  EditOutlined,
  LockOutlined,
  SaveOutlined,
  CloseOutlined
} from '@ant-design/icons';
import { ApiService, type UserInfo } from '../services/api';

interface UserProfileProps {
  onUserUpdate?: (user: UserInfo) => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ onUserUpdate }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 表单实例
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  useEffect(() => {
    loadUserInfo();
  }, []);

  const loadUserInfo = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getCurrentUser();
      if (response.success && response.data) {
        setUser(response.data);
        profileForm.setFieldsValue({
          full_name: response.data.full_name || '',
          email: response.data.email || '',
          phone: response.data.phone || ''
        });
      } else {
        setError('获取用户信息失败');
      }
    } catch (err) {
      setError('获取用户信息失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateInfo = async (values: any) => {
    try {
      setSubmitLoading(true);
      setError(null);
      setSuccess(null);

      const response = await ApiService.updateCurrentUser(values);
      if (response.success && response.data) {
        setUser(response.data);
        setIsEditing(false);
        setSuccess('用户信息更新成功');
        if (onUserUpdate) {
          onUserUpdate(response.data);
        }
      } else {
        setError(response.message || '更新失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '更新失败');
      console.error(err);
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleChangePassword = async (values: any) => {
    try {
      setSubmitLoading(true);
      setError(null);
      setSuccess(null);

      const response = await ApiService.changePassword({
        current_password: values.current_password,
        new_password: values.new_password
      });

      if (response.success) {
        setIsChangingPassword(false);
        passwordForm.resetFields();
        setSuccess('密码修改成功');
      } else {
        setError(response.message || '密码修改失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '密码修改失败');
      console.error(err);
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setIsChangingPassword(false);
    setError(null);
    setSuccess(null);
    if (user) {
      profileForm.setFieldsValue({
        full_name: user.full_name || '',
        email: user.email || '',
        phone: user.phone || ''
      });
    }
    passwordForm.resetFields();
  };

  if (loading) {
    return (
      <Card loading style={{ margin: '24px' }}>
        <div style={{ height: '400px' }} />
      </Card>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      {/* 消息提示 */}
      {error && (
        <Alert
          message={error}
          type="error"
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      {success && (
        <Alert
          message={success}
          type="success"
          closable
          onClose={() => setSuccess(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      {user && (
        <>
          {/* 基本信息卡片 */}
          <Card
            title={
              <Space>
                <Avatar size="large" icon={<UserOutlined />} />
                <div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold' }}>个人信息</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>管理您的账户信息</div>
                </div>
              </Space>
            }
            extra={
              !isEditing && !isChangingPassword && (
                <Button
                  type="primary"
                  icon={<EditOutlined />}
                  onClick={() => setIsEditing(true)}
                >
                  编辑信息
                </Button>
              )
            }
            style={{ marginBottom: 24 }}
          >
            {!isEditing ? (
              <Descriptions bordered column={2} size="middle">
                <Descriptions.Item label="用户名" span={1}>
                  <Space>
                    <UserOutlined />
                    <strong>{user.username}</strong>
                  </Space>
                </Descriptions.Item>

                <Descriptions.Item label="邮箱" span={1}>
                  <Space>
                    <MailOutlined />
                    {user.email || '未设置'}
                  </Space>
                </Descriptions.Item>

                <Descriptions.Item label="姓名" span={1}>
                  {user.full_name || '未设置'}
                </Descriptions.Item>

                <Descriptions.Item label="电话" span={1}>
                  <Space>
                    <PhoneOutlined />
                    {user.phone || '未设置'}
                  </Space>
                </Descriptions.Item>

                <Descriptions.Item label="注册时间" span={1}>
                  {new Date(user.created_at).toLocaleDateString('zh-CN')}
                </Descriptions.Item>

                <Descriptions.Item label="账户状态" span={1}>
                  <Tag color={user.is_active ? 'success' : 'error'}>
                    {user.is_active ? '活跃' : '已禁用'}
                  </Tag>
                </Descriptions.Item>

                <Descriptions.Item label="用户角色" span={2}>
                  <Space wrap>
                    {user.roles.map(role => (
                      <Tag color="blue" key={role}>{role}</Tag>
                    ))}
                  </Space>
                </Descriptions.Item>

                <Descriptions.Item label="权限" span={2}>
                  <div style={{ maxHeight: '100px', overflowY: 'auto' }}>
                    <Space wrap>
                      {user.permissions.slice(0, 10).map(permission => (
                        <Tag key={permission}>{permission}</Tag>
                      ))}
                      {user.permissions.length > 10 && (
                        <Tag>+{user.permissions.length - 10} 更多</Tag>
                      )}
                    </Space>
                  </div>
                </Descriptions.Item>
              </Descriptions>
            ) : (
              <Form
                form={profileForm}
                layout="vertical"
                onFinish={handleUpdateInfo}
              >
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="full_name"
                      label="姓名"
                    >
                      <Input placeholder="请输入姓名" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="email"
                      label="邮箱"
                      rules={[
                        { type: 'email', message: '请输入有效的邮箱地址' }
                      ]}
                    >
                      <Input placeholder="请输入邮箱" />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="phone"
                      label="电话"
                    >
                      <Input placeholder="请输入电话号码" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="用户名">
                      <Input value={user.username} disabled />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                  <Space>
                    <Button onClick={handleCancelEdit}>
                      <CloseOutlined /> 取消
                    </Button>
                    <Button type="primary" htmlType="submit" loading={submitLoading}>
                      <SaveOutlined /> 保存
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            )}
          </Card>

          {/* 密码管理卡片 */}
          <Card
            title={
              <Space>
                <LockOutlined />
                <div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold' }}>密码管理</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>修改您的登录密码</div>
                </div>
              </Space>
            }
            extra={
              !isChangingPassword && !isEditing && (
                <Button
                  type="default"
                  icon={<LockOutlined />}
                  onClick={() => setIsChangingPassword(true)}
                >
                  修改密码
                </Button>
              )
            }
          >
            {!isChangingPassword ? (
              <div style={{ padding: '20px 0', textAlign: 'center', color: '#666' }}>
                <LockOutlined style={{ fontSize: '32px', marginBottom: '8px' }} />
                <div>点击右上角按钮修改密码</div>
              </div>
            ) : (
              <Form
                form={passwordForm}
                layout="vertical"
                onFinish={handleChangePassword}
              >
                <Row gutter={16}>
                  <Col span={24}>
                    <Form.Item
                      name="current_password"
                      label="当前密码"
                      rules={[{ required: true, message: '请输入当前密码' }]}
                    >
                      <Input.Password placeholder="请输入当前密码" />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="new_password"
                      label="新密码"
                      rules={[
                        { required: true, message: '请输入新密码' },
                        { min: 6, message: '密码至少6个字符' }
                      ]}
                    >
                      <Input.Password placeholder="请输入新密码（至少6位）" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="confirm_password"
                      label="确认新密码"
                      dependencies={['new_password']}
                      rules={[
                        { required: true, message: '请确认新密码' },
                        ({ getFieldValue }) => ({
                          validator(_, value) {
                            if (!value || getFieldValue('new_password') === value) {
                              return Promise.resolve();
                            }
                            return Promise.reject(new Error('两次输入的密码不一致'));
                          },
                        }),
                      ]}
                    >
                      <Input.Password placeholder="请再次输入新密码" />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                  <Space>
                    <Button onClick={handleCancelEdit}>
                      <CloseOutlined /> 取消
                    </Button>
                    <Button type="primary" htmlType="submit" loading={submitLoading} danger>
                      <LockOutlined /> 修改密码
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            )}
          </Card>
        </>
      )}
    </div>
  );
};

export default UserProfile;