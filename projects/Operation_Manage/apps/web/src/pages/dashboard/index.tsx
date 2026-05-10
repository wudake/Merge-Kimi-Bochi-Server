import { Card, Row, Col, Statistic } from 'antd'
import {
  FileTextOutlined,
  EyeOutlined,
  MessageOutlined,
  RiseOutlined,
} from '@ant-design/icons'

export default function DashboardPage() {
  return (
    <div>
      <h2 style={{ marginTop: 0, marginBottom: 24 }}>数据看板</h2>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日待发布"
              value={5}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="本周已发布"
              value={23}
              prefix={<EyeOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="本周询盘"
              value={12}
              prefix={<MessageOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="粉丝增长"
              value={156}
              prefix={<RiseOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
