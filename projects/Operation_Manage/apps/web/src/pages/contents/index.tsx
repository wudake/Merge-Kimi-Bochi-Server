import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Table, Button, Input, Select, Tag, Space, Modal, Form,
  message, Popconfirm, Card, Row, Col, DatePicker, Radio, AutoComplete, Grid
} from 'antd'
import {
  PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined,
  CalendarOutlined, UnorderedListOutlined, ArrowLeftOutlined, ArrowRightOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import {
  getContents, getCalendarContents, createContent, updateContent,
  updateContentStatus, deleteContent, type ContentItem
} from '../../api/contents'
import { getAccounts, type Account } from '../../api/accounts'
import { getUsers, type User } from '../../api/users'

const { Option } = Select
// const { RangePicker } = DatePicker

const STATUS_MAP: Record<string, { text: string; color: string }> = {
  PENDING: { text: '待制作', color: 'default' },
  PRODUCING: { text: '制作中', color: 'processing' },
  READY: { text: '待发布', color: 'warning' },
  PUBLISHED: { text: '已发布', color: 'success' },
  ARCHIVED: { text: '已归档', color: 'gray' },
}

const PLATFORM_MAP: Record<string, string> = {
  TIKTOK: 'TikTok',
  INSTAGRAM: 'Instagram',
  YOUTUBE: 'YouTube',
  FACEBOOK: 'Facebook',
}

const CONTENT_TYPE_MAP: Record<string, string> = {
  original: '原创',
  mixed: '混剪',
  repost: '搬运',
}

export default function ContentCalendarPage() {
  const [contents, setContents] = useState<ContentItem[]>([])
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState<'week' | 'month' | 'list'>('week')
  const [currentDate, setCurrentDate] = useState(dayjs())
  const [modalVisible, setModalVisible] = useState(false)
  const [editingContent, setEditingContent] = useState<ContentItem | null>(null)
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>()
  const [accountsList, setAccountsList] = useState<Account[]>([])
  const [usersList, setUsersList] = useState<User[]>([])
  type PreviewInfo =
    | { type: 'social'; url: string; isVertical: boolean }
    | { type: 'video'; url: string }
    | { type: 'image'; url: string }
    | { type: 'pdf'; url: string }
    | { type: 'iframe'; url: string }

  const [previewInfo, setPreviewInfo] = useState<PreviewInfo | null>(null)
  const [form] = Form.useForm()
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.md

  const calendarStart = currentDate.startOf(viewMode === 'week' ? 'week' : 'month').startOf('week')
  const calendarEnd = currentDate.endOf(viewMode === 'week' ? 'week' : 'month').endOf('week')

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
        account: a,
        color,
      }
    })
  }, [accountsList])

  const fetchContents = useCallback(async () => {
    setLoading(true)
    try {
      if (viewMode === 'week' || viewMode === 'month') {
        const data = await getCalendarContents({
          startDate: calendarStart.format('YYYY-MM-DD'),
          endDate: calendarEnd.format('YYYY-MM-DD'),
        })
        setContents(data)
      } else {
        const data = await getContents({
          search: searchText || undefined,
          status: filterStatus,
        })
        setContents(data)
      }
    } finally {
      setLoading(false)
    }
  }, [viewMode, calendarStart.format('YYYY-MM-DD'), calendarEnd.format('YYYY-MM-DD'), searchText, filterStatus])

  useEffect(() => {
    fetchContents()
  }, [fetchContents])

  useEffect(() => {
    getAccounts().then(setAccountsList).catch(() => {})
    getUsers().then(setUsersList).catch(() => {})
  }, [])

  const getPreviewInfo = (url: string): PreviewInfo | null => {
    try {
      if (!url) return null
      // YouTube Shorts (竖屏)
      const ytShortsMatch = url.match(/youtube\.com\/shorts\/([a-zA-Z0-9_-]+)/)
      if (ytShortsMatch) {
        const origin = typeof window !== 'undefined' ? window.location.origin : ''
        return {
          type: 'social',
          url: `https://www.youtube.com/embed/${ytShortsMatch[1]}?playsinline=1&rel=0${origin ? `&origin=${encodeURIComponent(origin)}` : ''}`,
          isVertical: true,
        }
      }
      // YouTube 普通视频 (横屏)
      const ytWatchMatch = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/)
      if (ytWatchMatch) {
        const origin = typeof window !== 'undefined' ? window.location.origin : ''
        return {
          type: 'social',
          url: `https://www.youtube.com/embed/${ytWatchMatch[1]}?playsinline=1&rel=0${origin ? `&origin=${encodeURIComponent(origin)}` : ''}`,
          isVertical: false,
        }
      }
      // Instagram Reels (竖屏)
      const igReelsMatch = url.match(/instagram\.com\/(?:reels?|p)\/([a-zA-Z0-9_-]+)/)
      if (igReelsMatch) return {
        type: 'social',
        url: `https://www.instagram.com/p/${igReelsMatch[1]}/embed/?captioned=false`,
        isVertical: true,
      }
      // TikTok (竖屏)
      const ttMatch = url.match(/tiktok\.com\/.*\/video\/(\d+)/)
      if (ttMatch) return {
        type: 'social',
        url: `https://www.tiktok.com/embed/v2/${ttMatch[1]}`,
        isVertical: true,
      }

      // NAS / 局域网文件检测（根据扩展名）
      const lowerUrl = url.toLowerCase()
      let pathname = lowerUrl
      try {
        const parsed = new URL(url)
        pathname = parsed.pathname.toLowerCase()
      } catch {
        // 非标准URL，直接用原始字符串匹配
      }

      if (/\.(mp4|mov|webm|mkv|avi|m4v|ogv)(\?.*)?$/.test(pathname)) {
        return { type: 'video', url }
      }
      if (/\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?.*)?$/.test(pathname)) {
        return { type: 'image', url }
      }
      if (/\.pdf(\?.*)?$/.test(pathname)) {
        return { type: 'pdf', url }
      }
      if (/\.(html?|txt)(\?.*)?$/.test(pathname)) {
        return { type: 'iframe', url }
      }

      return null
    } catch {
      return null
    }
  }

  const handlePreview = () => {
    const url = form.getFieldValue('publishUrl')
    const info = getPreviewInfo(url)
    if (info) {
      setPreviewInfo(info)
    } else {
      message.error('暂不支持该链接的预览')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const payload = {
        ...values,
        plannedPublishAt: values.plannedPublishAt?.format?.('YYYY-MM-DD HH:mm:ss'),
      }
      if (editingContent) {
        await updateContent(editingContent.id, payload)
        message.success('更新成功')
      } else {
        await createContent(payload)
        message.success('创建成功')
      }
      setModalVisible(false)
      setEditingContent(null)
      form.resetFields()
      fetchContents()
    } catch (err: any) {
      message.error(err.message || '操作失败')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteContent(id)
      message.success('删除成功')
      fetchContents()
    } catch (err: any) {
      message.error(err.message || '删除失败')
    }
  }

  const handleStatusChange = async (id: string, status: string) => {
    try {
      await updateContentStatus(id, status)
      message.success('状态更新成功')
      fetchContents()
    } catch (err: any) {
      message.error(err.message || '更新失败')
    }
  }

  const openEdit = (content: ContentItem) => {
    setEditingContent(content)
    form.setFieldsValue({
      ...content,
      accountIds: content.accounts.map((a) => a.id),
      plannedPublishAt: content.plannedPublishAt ? dayjs(content.plannedPublishAt) : null,
      operatorId: content.operator?.id || undefined,
    })
    setModalVisible(true)
  }

  const openCreate = (date?: Dayjs) => {
    setEditingContent(null)
    form.resetFields()
    if (date) {
      form.setFieldsValue({ plannedPublishAt: date })
    }
    setModalVisible(true)
  }

  const weekDays = Array.from({ length: 7 }, (_, i) => calendarStart.add(i, 'day'))

  const getContentsForDay = (date: Dayjs) =>
    contents.filter((c) =>
      c.plannedPublishAt && dayjs(c.plannedPublishAt).isSame(date, 'day')
    )

  const listColumns = [
    { title: '标题', dataIndex: 'title', key: 'title', width: 250 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => {
        const cfg = STATUS_MAP[s] || { text: s, color: 'default' }
        return <Tag color={cfg.color}>{cfg.text}</Tag>
      },
    },
    {
      title: '内容类型',
      dataIndex: 'contentType',
      key: 'contentType',
      render: (v: string) => CONTENT_TYPE_MAP[v] || v || '-',
    },
    {
      title: '关联账号',
      dataIndex: 'accounts',
      key: 'accounts',
      render: (acs: ContentItem['accounts']) =>
        acs.map((a) => <Tag key={a.id}>{PLATFORM_MAP[a.platform] || a.platform}: {a.name}</Tag>),
    },
    {
      title: '负责人',
      dataIndex: 'operator',
      key: 'operator',
      render: (op: ContentItem['operator']) => op?.realName || '-',
    },
    {
      title: '发布时间',
      dataIndex: 'plannedPublishAt',
      key: 'plannedPublishAt',
      render: (v: string) => v ? dayjs(v).format('MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ContentItem) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(record)}>编辑</Button>
          <Select
            size="small"
            value={record.status}
            style={{ width: 100 }}
            onChange={(v) => handleStatusChange(record.id, v)}
          >
            {Object.entries(STATUS_MAP).map(([k, v]) => (
              <Option key={k} value={k}>{v.text}</Option>
            ))}
          </Select>
          <Popconfirm
            title="确认删除"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>内容产出</h2>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[isMobile ? 8 : 16, isMobile ? 8 : 16]} align="middle" justify="space-between">
          <Col xs={24} sm={12} md="auto">
            <Radio.Group
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value)}
              buttonStyle="solid"
              size={isMobile ? 'small' : 'middle'}
            >
              <Radio.Button value="week">
                <CalendarOutlined /> {!isMobile && ' 周视图'}
              </Radio.Button>
              <Radio.Button value="month">
                <CalendarOutlined /> {!isMobile && ' 月视图'}
              </Radio.Button>
              <Radio.Button value="list">
                <UnorderedListOutlined /> {!isMobile && ' 列表'}
              </Radio.Button>
            </Radio.Group>
          </Col>

          {(viewMode === 'week' || viewMode === 'month') && (
            <Col xs={24} sm={12} md="auto">
              <Space size={isMobile ? 'small' : 'middle'}>
                <Button icon={<ArrowLeftOutlined />} onClick={() => setCurrentDate(currentDate.subtract(1, viewMode))} size={isMobile ? 'small' : 'middle'} />
                <span style={{ fontWeight: 'bold', minWidth: isMobile ? 120 : 180, textAlign: 'center', fontSize: isMobile ? 12 : 14 }}>
                  {viewMode === 'week'
                    ? `${calendarStart.format('YYYY-MM-DD')} ~ ${calendarEnd.format('MM-DD')}`
                    : currentDate.format('YYYY年MM月')
                  }
                </span>
                <Button icon={<ArrowRightOutlined />} onClick={() => setCurrentDate(currentDate.add(1, viewMode))} size={isMobile ? 'small' : 'middle'} />
                <Button onClick={() => setCurrentDate(dayjs())} size={isMobile ? 'small' : 'middle'}>
                  {viewMode === 'week' ? '本周' : '本月'}
                </Button>
              </Space>
            </Col>
          )}

          {viewMode === 'list' && (
            <Col xs={24} sm={12} md="auto">
              <Space size={isMobile ? 'small' : 'middle'}>
                <Input
                  placeholder="搜索内容标题"
                  prefix={<SearchOutlined />}
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  onPressEnter={fetchContents}
                  style={{ width: isMobile ? 140 : 200 }}
                  size={isMobile ? 'small' : 'middle'}
                />
                <Select
                  placeholder="状态"
                  allowClear
                  style={{ width: isMobile ? 100 : 120 }}
                  value={filterStatus}
                  onChange={setFilterStatus}
                  size={isMobile ? 'small' : 'middle'}
                >
                  {Object.entries(STATUS_MAP).map(([k, v]) => (
                    <Option key={k} value={k}>{v.text}</Option>
                  ))}
                </Select>
                <Button onClick={fetchContents} size={isMobile ? 'small' : 'middle'}>查询</Button>
              </Space>
            </Col>
          )}

          <Col xs={24} md="auto" style={{ textAlign: isMobile ? 'right' : undefined }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => openCreate()} size={isMobile ? 'small' : 'middle'}>
              新建内容
            </Button>
          </Col>
        </Row>
      </Card>

      {viewMode === 'week' && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(7, minmax(0, 1fr))', gap: 8, width: '100%' }}>
          {weekDays.map((day) => {
            const dayContents = getContentsForDay(day)
            const isToday = day.isSame(dayjs(), 'day')
            return (
              <Card
                key={day.format('YYYY-MM-DD')}
                size="small"
                title={
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: isToday ? 'bold' : 'normal', color: isToday ? '#1677ff' : 'inherit' }}>
                      {day.format('MM-DD')} {['周一', '周二', '周三', '周四', '周五', '周六', '周日'][day.day() === 0 ? 6 : day.day() - 1]}
                    </span>
                    {isToday && <Tag color="blue">今天</Tag>}
                  </div>
                }
                styles={{ body: { padding: 8, minHeight: 120, background: isToday ? '#f0f5ff' : undefined } }}
                extra={
                  <Button type="link" size="small" onClick={() => openCreate(day)}>+</Button>
                }
              >
                <Space direction="vertical" style={{ width: '100%' }} size={4}>
                  {dayContents.map((c) => {
                    return (
                      <div
                        key={c.id}
                        onClick={() => openEdit(c)}
                        style={{
                          padding: '6px 8px',
                          borderRadius: 4,
                          background: '#fff',
                          border: '1px solid #f0f0f0',
                          cursor: 'pointer',
                          fontSize: 12,
                        }}
                      >
                        <div style={{ fontWeight: 'bold', marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {c.title}
                        </div>
                        <div>
                          {c.operator && (
                            <Tag color="blue" style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>
                              {c.operator.realName}
                            </Tag>
                          )}
                          {c.contentType && (
                            <Tag style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>
                              {CONTENT_TYPE_MAP[c.contentType] || c.contentType}
                            </Tag>
                          )}
                          {c.accounts.map((a) => (
                            <Tag key={a.id} style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>
                              {PLATFORM_MAP[a.platform] || a.platform}
                            </Tag>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </Space>
              </Card>
            )
          })}
        </div>
      )}

      {viewMode === 'month' && (() => {
        const monthStart = currentDate.startOf('month')
        const monthEnd = currentDate.endOf('month')
        const startOfCalendar = monthStart.startOf('week')
        const endOfCalendar = monthEnd.endOf('week')
        const totalDays = endOfCalendar.diff(startOfCalendar, 'day') + 1
        const monthDays = Array.from({ length: totalDays }, (_, i) => startOfCalendar.add(i, 'day'))
        const weekCount = Math.ceil(totalDays / 7)

        return (
          <div>
            {/* 星期标题 */}
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(7, minmax(36px, 1fr))' : 'repeat(7, 1fr)', gap: isMobile ? 4 : 8, marginBottom: 8 }}>
              {['周一', '周二', '周三', '周四', '周五', '周六', '周日'].map((d) => (
                <div key={d} style={{ textAlign: 'center', fontWeight: 'bold', color: '#666', padding: isMobile ? '4px 0' : '8px 0', fontSize: isMobile ? 11 : 14 }}>
                  {isMobile ? d.replace('星期', '周') : d}
                </div>
              ))}
            </div>
            {/* 日期网格 */}
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(7, minmax(36px, 1fr))' : 'repeat(7, 1fr)', gridTemplateRows: `repeat(${weekCount}, 1fr)`, gap: isMobile ? 4 : 8 }}>
              {monthDays.map((day) => {
                const dayContents = getContentsForDay(day)
                const isToday = day.isSame(dayjs(), 'day')
                const isCurrentMonth = day.month() === currentDate.month()
                return (
                  <Card
                    key={day.format('YYYY-MM-DD')}
                    size="small"
                    style={{ opacity: isCurrentMonth ? 1 : 0.5 }}
                    title={
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{
                          fontWeight: isToday ? 'bold' : 'normal',
                          color: isToday ? '#1677ff' : (isCurrentMonth ? 'inherit' : '#999'),
                        }}>
                          {day.date()}
                        </span>
                        {isToday && <Tag color="blue" style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>今天</Tag>}
                      </div>
                    }
                    styles={{ body: { padding: 6, minHeight: 100, background: isToday ? '#f0f5ff' : undefined } }}
                    extra={
                      <Button type="link" size="small" onClick={() => openCreate(day)} style={{ padding: 0 }}>+</Button>
                    }
                  >
                    <Space direction="vertical" style={{ width: '100%' }} size={2}>
                      {dayContents.map((c) => (
                        <div
                          key={c.id}
                          onClick={() => openEdit(c)}
                          style={{
                            padding: '4px 6px',
                            borderRadius: 4,
                            background: '#fff',
                            border: '1px solid #f0f0f0',
                            cursor: 'pointer',
                            fontSize: 11,
                          }}
                        >
                          <div style={{ fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', lineHeight: '16px' }}>
                            {c.title}
                          </div>
                          <div style={{ marginTop: 2 }}>
                            {c.operator && (
                              <Tag color="blue" style={{ fontSize: 9, lineHeight: '14px', padding: '0 3px' }}>
                                {c.operator.realName}
                              </Tag>
                            )}
                            {c.accounts.slice(0, 1).map((a) => (
                              <Tag key={a.id} style={{ fontSize: 9, lineHeight: '14px', padding: '0 3px' }}>
                                {PLATFORM_MAP[a.platform] || a.platform}
                              </Tag>
                            ))}
                            {c.accounts.length > 1 && (
                              <Tag style={{ fontSize: 9, lineHeight: '14px', padding: '0 3px' }}>+{c.accounts.length - 1}</Tag>
                            )}
                          </div>
                        </div>
                      ))}
                    </Space>
                  </Card>
                )
              })}
            </div>
          </div>
        )
      })()}

      {viewMode === 'list' && (
        <Table
          columns={listColumns}
          dataSource={contents}
          rowKey="id"
          loading={loading}
          size="small"
          scroll={{ x: isMobile ? 800 : undefined }}
        />
      )}

      <Modal
        title={editingContent ? '编辑内容' : '新建内容'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          setEditingContent(null)
          setPreviewInfo(null)
          form.resetFields()
        }}
        width={isMobile ? '90%' : 680}
        footer={
          <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 8 : 0, justifyContent: 'space-between', alignItems: isMobile ? 'stretch' : 'center' }}>
            {editingContent ? (
              <Popconfirm
                title="确认删除"
                description="删除后不可恢复，是否继续？"
                onConfirm={() => {
                  handleDelete(editingContent.id)
                  setModalVisible(false)
                  setEditingContent(null)
                  setPreviewInfo(null)
                  form.resetFields()
                }}
                okText="删除"
                okButtonProps={{ danger: true }}
                cancelText="取消"
              >
                <Button danger block={isMobile}>删除</Button>
              </Popconfirm>
            ) : (
              <div />
            )}
            <Space direction={isMobile ? 'vertical' : 'horizontal'} style={{ width: isMobile ? '100%' : undefined }}>
              <Button onClick={() => {
                setModalVisible(false)
                setEditingContent(null)
                setPreviewInfo(null)
                form.resetFields()
              }} block={isMobile}>
                取消
              </Button>
              <Button type="primary" onClick={() => form.submit()} block={isMobile}>
                确定
              </Button>
            </Space>
          </div>
        }
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="title" label="内容标题" rules={[{ required: true, message: '请输入内容标题' }]}>
            <Input placeholder="请输入内容标题" />
          </Form.Item>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item name="accountIds" label="关联账号">
                <Select
                  mode="multiple"
                  placeholder="选择要发布的账号"
                  optionFilterProp="label"
                  showSearch
                >
                  {accountOptions.map(({ account, color }) => (
                    <Option
                      key={account.id}
                      value={account.id}
                      label={account.customGroup
                        ? `${account.customGroup} | ${PLATFORM_MAP[account.platform] || account.platform} - ${account.name}`
                        : `${PLATFORM_MAP[account.platform] || account.platform} - ${account.name}`
                      }
                      style={{ background: color.bg, color: color.text }}
                    >
                      {account.customGroup && (
                        <span style={{ fontWeight: 600, marginRight: 6 }}>{account.customGroup} |</span>
                      )}
                      <span style={{ color: '#1677ff' }}>[{PLATFORM_MAP[account.platform] || account.platform}]</span> {account.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="contentType" label="内容类型">
                <AutoComplete
                  placeholder="选择或输入内容类型"
                  allowClear
                  options={Object.entries(CONTENT_TYPE_MAP).map(([k, v]) => ({ value: k, label: v }))}
                  filterOption={(inputValue, option) =>
                    (option?.label ?? '').toLowerCase().includes(inputValue.toLowerCase()) ||
                    (option?.value ?? '').toLowerCase().includes(inputValue.toLowerCase())
                  }
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="内容链接（URL）">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space direction={isMobile ? 'vertical' : 'horizontal'} style={{ width: '100%' }} size={isMobile ? 'small' : 'middle'}>
                <Form.Item name="publishUrl" noStyle>
                  <Input placeholder="发布后回填内容链接" style={{ width: isMobile ? '100%' : 480 }} />
                </Form.Item>
                <Button onClick={handlePreview} size={isMobile ? 'small' : 'middle'}>预览</Button>
              </Space>
              {previewInfo && (
                <div style={{ width: '100%' }}>
                  {previewInfo.type === 'social' && (
                    <div style={{ width: '100%', maxWidth: previewInfo.isVertical ? (isMobile ? 260 : 360) : (isMobile ? '100%' : 480) }}>
                      <div style={{ position: 'relative', paddingTop: previewInfo.isVertical ? '177.78%' : '56.25%', borderRadius: 8, overflow: 'hidden', background: '#000' }}>
                        <iframe
                          src={previewInfo.url}
                          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                          allowFullScreen
                          referrerPolicy="strict-origin-when-cross-origin"
                          loading="eager"
                        />
                      </div>
                    </div>
                  )}
                  {previewInfo.type === 'video' && (
                    <div style={{ borderRadius: 8, overflow: 'hidden', background: '#000' }}>
                      <video
                        src={previewInfo.url}
                        controls
                        style={{ width: '100%', maxHeight: isMobile ? 360 : 480, display: 'block' }}
                        preload="metadata"
                      />
                    </div>
                  )}
                  {previewInfo.type === 'image' && (
                    <div style={{ borderRadius: 8, overflow: 'hidden', background: '#f5f5f5', textAlign: 'center' }}>
                      <img
                        src={previewInfo.url}
                        alt="预览"
                        style={{ maxWidth: '100%', maxHeight: isMobile ? 360 : 480, display: 'block', margin: '0 auto' }}
                      />
                    </div>
                  )}
                  {previewInfo.type === 'pdf' && (
                    <div style={{ position: 'relative', paddingTop: '75%', borderRadius: 8, overflow: 'hidden', background: '#f5f5f5' }}>
                      <iframe
                        src={previewInfo.url}
                        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
                      />
                    </div>
                  )}
                  {previewInfo.type === 'iframe' && (
                    <div style={{ position: 'relative', paddingTop: '75%', borderRadius: 8, overflow: 'hidden', background: '#f5f5f5' }}>
                      <iframe
                        src={previewInfo.url}
                        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
                      />
                    </div>
                  )}
                  <div style={{ marginTop: 4, textAlign: 'right' }}>
                    <Button type="link" size="small" onClick={() => window.open(form.getFieldValue('publishUrl'), '_blank')}>
                      新窗口打开原链接 ↗
                    </Button>
                  </div>
                </div>
              )}
            </Space>
          </Form.Item>

          <Form.Item name="script" label="内容脚本">
            <Input.TextArea rows={4} placeholder="输入视频脚本或内容大纲" />
          </Form.Item>

          <Form.Item name="description" label="内容文案">
            <Input.TextArea rows={4} placeholder="输入发布文案、标题描述等" />
          </Form.Item>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item name="operatorId" label="负责人">
                <Select placeholder="选择负责人" allowClear showSearch optionFilterProp="children">
                  {usersList.map((user) => (
                    <Option key={user.id} value={user.id}>
                      {user.realName} ({user.username})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="plannedPublishAt" label="发布时间">
                <DatePicker showTime style={{ width: '100%' }} placeholder="选择发布时间" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="其他备注信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
