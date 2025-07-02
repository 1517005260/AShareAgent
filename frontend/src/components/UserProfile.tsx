import React, { useState, useEffect } from 'react';
import { ApiService, type UserInfo } from '../services/api';

interface UserProfileProps {
  onUserUpdate?: (user: UserInfo) => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ onUserUpdate }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 用户信息表单
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: ''
  });

  // 密码修改表单
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  useEffect(() => {
    loadUserInfo();
  }, []);

  const loadUserInfo = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getCurrentUser();
      if (response.success && response.data) {
        setUser(response.data);
        setFormData({
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

  const handleUpdateInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await ApiService.updateCurrentUser(formData);
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
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    try {
      if (passwordData.new_password !== passwordData.confirm_password) {
        setError('新密码确认不匹配');
        return;
      }

      if (passwordData.new_password.length < 6) {
        setError('新密码长度至少6位');
        return;
      }

      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await ApiService.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });

      if (response.success) {
        setIsChangingPassword(false);
        setPasswordData({
          current_password: '',
          new_password: '',
          confirm_password: ''
        });
        setSuccess('密码修改成功');
      } else {
        setError(response.message || '密码修改失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '密码修改失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        email: user.email || '',
        phone: user.phone || ''
      });
    }
    setIsEditing(false);
    setIsChangingPassword(false);
    setError(null);
    setSuccess(null);
  };

  if (loading && !user) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-lg">加载中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-6">个人信息</h2>

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

      {user && (
        <div className="space-y-6">
          {/* 基本信息 */}
          <div className="border-b pb-6">
            <h3 className="text-lg font-semibold mb-4">基本信息</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  用户名
                </label>
                <input
                  type="text"
                  value={user.username}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  邮箱
                </label>
                <input
                  type="email"
                  value={isEditing ? formData.email : user.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={!isEditing}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md ${
                    !isEditing ? 'bg-gray-100' : ''
                  }`}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  姓名
                </label>
                <input
                  type="text"
                  value={isEditing ? formData.full_name : user.full_name || ''}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  disabled={!isEditing}
                  placeholder="请输入姓名"
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md ${
                    !isEditing ? 'bg-gray-100' : ''
                  }`}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  电话
                </label>
                <input
                  type="tel"
                  value={isEditing ? formData.phone : user.phone || ''}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  disabled={!isEditing}
                  placeholder="请输入电话号码"
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md ${
                    !isEditing ? 'bg-gray-100' : ''
                  }`}
                />
              </div>
            </div>

            <div className="mt-4 flex space-x-2">
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  编辑信息
                </button>
              ) : (
                <>
                  <button
                    onClick={handleUpdateInfo}
                    disabled={loading}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    {loading ? '保存中...' : '保存'}
                  </button>
                  <button
                    onClick={handleCancel}
                    className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                  >
                    取消
                  </button>
                </>
              )}
            </div>
          </div>

          {/* 账户信息 */}
          <div className="border-b pb-6">
            <h3 className="text-lg font-semibold mb-4">账户信息</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  注册时间
                </label>
                <input
                  type="text"
                  value={new Date(user.created_at).toLocaleDateString('zh-CN')}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  账户状态
                </label>
                <input
                  type="text"
                  value={user.is_active ? '活跃' : '已禁用'}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  用户角色
                </label>
                <input
                  type="text"
                  value={user.roles.join(', ')}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  权限数量
                </label>
                <input
                  type="text"
                  value={`${user.permissions.length} 个权限`}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* 密码修改 */}
          <div>
            <h3 className="text-lg font-semibold mb-4">密码管理</h3>
            
            {!isChangingPassword ? (
              <button
                onClick={() => setIsChangingPassword(true)}
                className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
              >
                修改密码
              </button>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    当前密码
                  </label>
                  <input
                    type="password"
                    value={passwordData.current_password}
                    onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                    placeholder="请输入当前密码"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    新密码
                  </label>
                  <input
                    type="password"
                    value={passwordData.new_password}
                    onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                    placeholder="请输入新密码（至少6位）"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    确认新密码
                  </label>
                  <input
                    type="password"
                    value={passwordData.confirm_password}
                    onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                    placeholder="请再次输入新密码"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={handleChangePassword}
                    disabled={loading}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                  >
                    {loading ? '修改中...' : '修改密码'}
                  </button>
                  <button
                    onClick={handleCancel}
                    className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                  >
                    取消
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default UserProfile;