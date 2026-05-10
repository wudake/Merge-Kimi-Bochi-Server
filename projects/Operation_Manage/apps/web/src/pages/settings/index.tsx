import { useState, useEffect } from 'react'
import {
  Tabs, Table, Button, Tag, Modal, Form, Input, Select,
  message, Popconfirm, Space, Grid
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined, SafetyOutlined } from '@ant-design/icons'
import { getUsers, createUser, updateUser, deleteUser, type User } from '../../api/users'
import { useAuthStore } from '../../stores/auth'

const { Option } = Select

const ROLE_MAP: Record<string, string> = {
  SUPER_ADMIN: '超级管理员',
  MANAGER: '运营主管',
  OPERATOR: '运营专员',
}

const STATUS_MAP: Record<string, { text: string; color: string }> = {
  ACTIVE: { text: '正常', color: 'green' },
  INACTIVE: { text: '禁用', color: 'red' },
}

export default function SettingsPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [form] = Form.useForm()
  const currentUser = useAuthStore((s) => s.user)
  const isSuperAdmin = currentUser?.role === 'SUPER_ADMIN'
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.md

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const data = await getUsers()
      setUsers(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const handleSubmit = async (values: any) => {
    try {
      if (editingUser) {
        await updateUser(editingUser.id, values)
        message.success('更新成功')
      } else {
        await createUser(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      setEditingUser(null)
      form.resetFields()
      fetchUsers()
    } catch (err: any) {
      message.error(err.message || '操作失败')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteUser(id)
      message.success('删除成功')
      fetchUsers()
    } catch (err: any) {
      message.error(err.message || '删除失败')
    }
  }

  const openEdit = (user: User) => {
    setEditingUser(user)
    form.setFieldsValue({
      realName: user.realName,
      role: user.role,
      email: user.email,
      phone: user.phone,
      status: user.status,
    })
    setModalVisible(true)
  }

  const openCreate = () => {
    setEditingUser(null)
    form.resetFields()
    setModalVisible(true)
  }

  const columns = [
    { title: '用户名', dataIndex: 'username' },
    { title: '姓名', dataIndex: 'realName' },
    {
      title: '角色',
      dataIndex: 'role',
      render: (r: string) => ROLE_MAP[r] || r,
    },
    { title: '邮箱', dataIndex: 'email', render: (v: string) => v || '-' },
    { title: '电话', dataIndex: 'phone', render: (v: string) => v || '-' },
    {
      title: '状态',
      dataIndex: 'status',
      render: (s: string) => {
        const cfg = STATUS_MAP[s] || { text: s, color: 'default' }
        return <Tag color={cfg.color}>{cfg.text}</Tag>
      },
    },
    {
      title: '操作',
      render: (_: any, record: User) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="确认删除该用户？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>系统设置</h2>

      <Tabs
        items={[
          {
            key: 'users',
            label: (
              <span>
                <UserOutlined /> 用户管理
              </span>
            ),
            children: isSuperAdmin ? (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
                    新增用户
                  </Button>
                </div>
                <Table
                  columns={columns}
                  dataSource={users}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 10 }}
                  scroll={{ x: isMobile ? 600 : undefined }}
                />
              </div>
            ) : (
              <div>只有超级管理员可以管理用户</div>
            ),
          },
          {
            key: 'security',
            label: (
              <span>
                <SafetyOutlined /> 安全设置
              </span>
            ),
            children: <div>安全设置（开发中）</div>,
          },
        ]}
      />

      <Modal
        title={editingUser ? '编辑用户' : '新增用户'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false)
          setEditingUser(null)
          form.resetFields()
        }}
        width={isMobile ? '90%' : 520}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {!editingUser && (
            <>
              <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
              <Form.Item name="password" label="密码" rules={[{ required: true }]}>
                <Input.Password />
              </Form.Item>
            </>
          )}
          <Form.Item name="realName" label="真实姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true }]} initialValue="OPERATOR">
            <Select>
              {Object.entries(ROLE_MAP).map(([k, v]) => (
                <Option key={k} value={k}>{v}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="email" label="邮箱">
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="电话">
            <Input />
          </Form.Item>
          {editingUser && (
            <Form.Item name="status" label="状态" initialValue="ACTIVE">
              <Select>
                <Option value="ACTIVE">正常</Option>
                <Option value="INACTIVE">禁用</Option>
              </Select>
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}
