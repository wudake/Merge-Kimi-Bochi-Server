import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Table, Button, Input, Select, Tag, Space, Modal, Form,
  message, Popconfirm, Card, Row, Col, DatePicker, Checkbox, AutoComplete, Grid
} from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { getTopics, createTopic, updateTopic, deleteTopic, type Topic } from '../../api/topics'
import { getUsers, type User } from '../../api/users'
import { getAccounts, type Account } from '../../api/accounts'
import dayjs from 'dayjs'

const { Option } = Select

const STATUS_MAP: Record<string, { text: string; color: string }> = {
  PENDING: { text: '待使用', color: 'default' },
  IN_USE: { text: '使用中', color: 'processing' },
  USED: { text: '已使用', color: 'success' },
  DISCARDED: { text: '已弃用', color: 'error' },
}

const PLATFORM_LABEL: Record<string, string> = {
  TIKTOK: 'TK',
  INSTAGRAM: 'INS',
  YOUTUBE: 'YTB',
  FACEBOOK: 'FB',
}

const CONTENT_TYPE_MAP: Record<string, string> = {
  factory_tour: '工厂实拍',
  installation: '安装案例',
  review: '产品测评',
  comparison: '对比类',
  pricing: '定价类',
  buying_guide: '采购指南',
  knowledge: '科普知识',
}

export default function TopicListPage() {
  const [topics, setTopics] = useState<Topic[]>([])
  const [usersList, setUsersList] = useState<User[]>([])
  const [accountsList, setAccountsList] = useState<Account[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingTopic, setEditingTopic] = useState<Topic | null>(null)
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>()
  const [filterContentType, setFilterContentType] = useState<string>()
  const [form] = Form.useForm()
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.md

  const fetchTopics = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getTopics({
        search: searchText || undefined,
        status: filterStatus,
        contentType: filterContentType,
      })
      setTopics(data)
    } finally {
      setLoading(false)
    }
  }, [searchText, filterStatus, filterContentType])

  useEffect(() => {
    fetchTopics()
    getUsers().then(setUsersList).catch(() => {})
    getAccounts().then(setAccountsList).catch(() => {})
  }, [fetchTopics])

  const contentTypeOptions = useMemo(() => {
    const types = new Set<string>()
    topics.forEach((t) => {
      if (t.contentType) types.add(t.contentType)
    })
    return Array.from(types).map((t) => ({
      value: t,
      label: CONTENT_TYPE_MAP[t] || t,
    }))
  }, [topics])

  const formContentTypeOptions = useMemo(() => {
    const base = Object.values(CONTENT_TYPE_MAP).map((label) => ({
      value: label,
      label,
    }))
    const existing = Array.from(new Set(topics.map((t) => t.contentType).filter(Boolean)))
      .map((t) => {
        const key = t as string
        const label = CONTENT_TYPE_MAP[key] || key
        return { value: label, label }
      })
    return [...base, ...existing]
  }, [topics])

  const GROUP_BG_COLORS = [
    { bg: '#e0f2fe', text: '#0369a1' },
    { bg: '#dcfce7', text: '#15803d' },
    { bg: '#fef3c7', text: '#b45309' },
    { bg: '#fce7f3', text: '#be185d' },
    { bg: '#f3e8ff', text: '#7c3aed' },
    { bg: '#ffe4e6', text: '#be123c' },
  ]

  const accountOptions = useMemo(() => {
    const groupMap = new Map<string, number>()
    const sorted = [...accountsList].sort((a, b) => {
      const ga = a.customGroup || ''
      const gb = b.customGroup || ''
      if (ga !== gb) return ga.localeCompare(gb)
      return (a.name || '').localeCompare(b.name || '')
    })
    return sorted.map((a) => {
      const group = a.customGroup || '未分组'
      if (!groupMap.has(group)) groupMap.set(group, groupMap.size)
      const colorIdx = groupMap.get(group)!
      const color = GROUP_BG_COLORS[colorIdx % GROUP_BG_COLORS.length]
      return {
        value: a.id,
        label: a.customGroup
          ? `${a.customGroup} | ${PLATFORM_LABEL[a.platform] || a.platform} - ${a.name}`
          : `${PLATFORM_LABEL[a.platform] || a.platform} - ${a.name}`,
        group,
        color,
      }
    })
  }, [accountsList])

  const handleSubmit = async (values: any) => {
    try {
      const payload = {
        title: values.title,
        contentType: values.contentType || undefined,
        isCompleted: values.isCompleted ?? false,
        completedAt: values.completedAt?.format?.('YYYY-MM-DD') || undefined,
        operatorId: values.operatorId || undefined,
        publishedAccounts: Array.isArray(values.publishedAccounts)
          ? values.publishedAccounts.join(',')
          : values.publishedAccounts || undefined,
        script: values.script || undefined,
        copywriting: values.copywriting || undefined,
        remark: values.remark || undefined,
      }
      if (editingTopic) {
        await updateTopic(editingTopic.id, payload)
        message.success('更新成功')
      } else {
        await createTopic(payload)
        message.success('创建成功')
      }
      setModalVisible(false)
      setEditingTopic(null)
      form.resetFields()
      fetchTopics()
    } catch (err: any) {
      message.error(err.message || '操作失败')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteTopic(id)
      message.success('删除成功')
      fetchTopics()
    } catch (err: any) {
      message.error(err.message || '删除失败')
    }
  }

  const openEdit = (topic: Topic) => {
    setEditingTopic(topic)
    const publishedAccountsArr = topic.publishedAccounts
      ? topic.publishedAccounts.split(',').map((s) => s.trim()).filter(Boolean)
      : []
    form.setFieldsValue({
      title: topic.title,
      contentType: CONTENT_TYPE_MAP[topic.contentType || ''] || topic.contentType,
      isCompleted: topic.isCompleted,
      completedAt: topic.completedAt ? dayjs(topic.completedAt) : null,
      operatorId: topic.operatorId,
      publishedAccounts: publishedAccountsArr,
      script: topic.script,
      copywriting: topic.copywriting,
      remark: topic.remark,
    })
    setModalVisible(true)
  }

  const openCreate = () => {
    setEditingTopic(null)
    form.resetFields()
    form.setFieldsValue({
      isCompleted: false,
      completedAt: dayjs(),
    })
    setModalVisible(true)
  }

  const columns = [
    { title: '选题标题', dataIndex: 'title', key: 'title' },
    {
      title: '内容类型',
      dataIndex: 'contentType',
      key: 'contentType',
      width: 100,
      render: (v: string) => CONTENT_TYPE_MAP[v] || v || '-',
    },
    {
      title: '是否完成',
      dataIndex: 'isCompleted',
      key: 'isCompleted',
      width: 90,
      align: 'center' as const,
      render: (v: boolean) => (v ? <Tag color="green">已完成</Tag> : <Tag>未完成</Tag>),
    },
    {
      title: '完成时间',
      dataIndex: 'completedAt',
      key: 'completedAt',
      width: 110,
      render: (v: string) => (v ? dayjs(v).format('YYYY-MM-DD') : '-'),
    },
    {
      title: '负责人',
      dataIndex: 'operatorId',
      key: 'operatorId',
      width: 90,
      render: (id: string) => {
        const user = usersList.find((u) => u.id === id)
        return user?.realName || '-'
      },
    },
    {
      title: '发布的平台和账号',
      dataIndex: 'publishedAccounts',
      key: 'publishedAccounts',
      width: 160,
      ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (s: string) => {
        const cfg = STATUS_MAP[s] || { text: s, color: 'default' }
        return <Tag color={cfg.color}>{cfg.text}</Tag>
      },
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      align: 'center' as const,
      render: (_: any, record: Topic) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm
            title="确认删除"
            description="删除后不可恢复，是否继续？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>选题库</h2>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col>
            <Input
              placeholder="搜索选题标题/标签"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={fetchTopics}
              style={{ width: isMobile ? '100%' : 240 }}
            />
          </Col>
          <Col>
            <Select
              placeholder="状态"
              allowClear
              style={{ width: isMobile ? '100%' : 140 }}
              value={filterStatus}
              onChange={setFilterStatus}
            >
              {Object.entries(STATUS_MAP).map(([k, v]) => (
                <Option key={k} value={k}>{v.text}</Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Select
              placeholder="内容类型"
              allowClear
              showSearch
              style={{ width: isMobile ? '100%' : 160 }}
              value={filterContentType}
              onChange={setFilterContentType}
            >
              {contentTypeOptions.map((opt) => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Button type="primary" onClick={fetchTopics}>查询</Button>
          </Col>
          <Col style={{ marginLeft: 'auto' }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              新增选题
            </Button>
          </Col>
        </Row>
      </Card>

      <Table
        columns={columns}
        dataSource={topics}
        rowKey="id"
        loading={loading}
        size="small"
        pagination={{ pageSize: 50 }}
        scroll={{ x: isMobile ? 800 : undefined }}
      />

      <Modal
        title={editingTopic ? '编辑选题' : '新增选题'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false)
          setEditingTopic(null)
          form.resetFields()
        }}
        width={isMobile ? '90%' : 640}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="title" label="选题标题" rules={[{ required: true }]}>
            <Input placeholder="输入选题标题" />
          </Form.Item>
          <Form.Item name="contentType" label="内容类型">
            <AutoComplete
              placeholder="选择或输入内容类型"
              allowClear
              options={formContentTypeOptions}
              style={{ width: '100%' }}
            />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item name="isCompleted" valuePropName="checked" label="是否完成">
                <Checkbox>已完成</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="completedAt" label="完成时间">
                <DatePicker style={{ width: '100%' }} placeholder="选择完成日期" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="operatorId" label="负责人">
            <Select placeholder="选择负责人" allowClear>
              {usersList.map((user) => (
                <Option key={user.id} value={user.id}>{user.realName}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="publishedAccounts" label="发布的平台和账号">
            <Select
              mode="multiple"
              placeholder="选择发布的账号"
              allowClear
              style={{ width: '100%' }}
            >
              {accountOptions.map((opt) => (
                <Option
                  key={opt.value}
                  value={opt.value}
                  style={{ background: opt.color.bg, color: opt.color.text }}
                >
                  {opt.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="script" label="视频脚本">
            <Input.TextArea rows={4} placeholder="输入视频脚本内容" />
          </Form.Item>
          <Form.Item name="copywriting" label="视频文案">
            <Input.TextArea rows={4} placeholder="输入视频文案内容" />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="其他补充信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
