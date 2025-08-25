import React, { useMemo } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Progress,
  List,
  Tag,
  Space,
  Typography,
  Tooltip,
  Empty,
  Badge
} from 'antd';
import {
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  TeamOutlined,
  TrophyOutlined,
  WarningOutlined,
  FireOutlined,
  BugOutlined,
  RocketOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import moment from 'moment';

const { Text, Title } = Typography;

const DashboardWidgets = ({ alerts, loading }) => {
  // Calculate comprehensive metrics
  const metrics = useMemo(() => {
    if (!alerts || alerts.length === 0) {
      return {
        total: 0,
        active: 0,
        critical: 0,
        resolved: 0,
        acknowledged: 0,
        unacknowledged: 0,
        avgResponseTime: 0,
        severityBreakdown: {},
        clusterBreakdown: {},
        teamActivity: {},
        alertTrends: [],
        topClusters: [],
        responseTimeStats: {},
        recentActivity: []
      };
    }

    const now = moment();
    const last24h = now.clone().subtract(24, 'hours');
    const last7d = now.clone().subtract(7, 'days');

    // Basic counts
    const total = alerts.length;
    const active = alerts.filter(a => a.grafana_status === 'active').length;
    const critical = alerts.filter(a => a.severity === 'critical' && a.grafana_status === 'active').length;
    const resolved = alerts.filter(a => a.jira_status === 'resolved').length;
    const acknowledged = alerts.filter(a => a.jira_status === 'acknowledged').length;
    const unacknowledged = alerts.filter(a => a.jira_status === 'open' && a.grafana_status === 'active').length;

    // Severity breakdown
    const severityBreakdown = alerts.reduce((acc, alert) => {
      const severity = alert.severity || 'unknown';
      acc[severity] = (acc[severity] || 0) + 1;
      return acc;
    }, {});

    // Cluster breakdown
    const clusterBreakdown = alerts.reduce((acc, alert) => {
      const cluster = alert.cluster || 'unknown';
      acc[cluster] = (acc[cluster] || 0) + 1;
      return acc;
    }, {});

    // Team activity
    const teamActivity = alerts.reduce((acc, alert) => {
      if (alert.acknowledged_by) {
        acc[alert.acknowledged_by] = (acc[alert.acknowledged_by] || 0) + 1;
      }
      if (alert.resolved_by && alert.resolved_by !== 'Auto-resolved (Grafana)') {
        acc[alert.resolved_by] = (acc[alert.resolved_by] || 0) + 1;
      }
      return acc;
    }, {});

    // Alert trends (last 7 days)
    const alertTrends = [];
    for (let i = 6; i >= 0; i--) {
      const date = now.clone().subtract(i, 'days');
      const dayAlerts = alerts.filter(alert => 
        moment(alert.created_at).isSame(date, 'day')
      );
      alertTrends.push({
        date: date.format('MM/DD'),
        total: dayAlerts.length,
        critical: dayAlerts.filter(a => a.severity === 'critical').length,
        resolved: dayAlerts.filter(a => a.jira_status === 'resolved').length
      });
    }

    // Top clusters by alert count
    const topClusters = Object.entries(clusterBreakdown)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([cluster, count]) => ({ cluster, count }));

    // Response time statistics
    const responseTimeStats = alerts.reduce((acc, alert) => {
      if (alert.acknowledged_at && alert.created_at) {
        const responseTime = moment(alert.acknowledged_at).diff(moment(alert.created_at), 'minutes');
        if (responseTime >= 0) {
          acc.times.push(responseTime);
        }
      }
      return acc;
    }, { times: [] });

    const avgResponseTime = responseTimeStats.times.length > 0 
      ? responseTimeStats.times.reduce((a, b) => a + b, 0) / responseTimeStats.times.length 
      : 0;

    // Recent activity (last 24 hours)
    const recentActivity = alerts
      .filter(alert => 
        alert.acknowledged_at && moment(alert.acknowledged_at).isAfter(last24h)
      )
      .sort((a, b) => moment(b.acknowledged_at) - moment(a.acknowledged_at))
      .slice(0, 10);

    return {
      total,
      active,
      critical,
      resolved,
      acknowledged,
      unacknowledged,
      avgResponseTime,
      severityBreakdown,
      clusterBreakdown,
      teamActivity,
      alertTrends,
      topClusters,
      responseTimeStats,
      recentActivity
    };
  }, [alerts]);

  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#ff4d4f',
      warning: '#fa8c16',
      info: '#1890ff',
      unknown: '#8c8c8c'
    };
    return colors[severity] || colors.unknown;
  };

  const pieChartColors = ['#ff4d4f', '#fa8c16', '#1890ff', '#52c41a', '#722ed1'];

  // Prepare data for charts
  const severityPieData = Object.entries(metrics.severityBreakdown).map(([severity, count], index) => ({
    name: severity,
    value: count,
    color: getSeverityColor(severity)
  }));

  const clusterPieData = Object.entries(metrics.clusterBreakdown)
    .slice(0, 5)
    .map(([cluster, count], index) => ({
      name: cluster,
      value: count,
      color: pieChartColors[index % pieChartColors.length]
    }));

  return (
    <div style={{ padding: '0 0 24px 0' }}>
      {/* Key Metrics Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Alerts"
              value={metrics.total}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Alerts"
              value={metrics.active}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: metrics.active > 0 ? '#fa8c16' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Critical Alerts"
              value={metrics.critical}
              prefix={<FireOutlined />}
              valueStyle={{ color: metrics.critical > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Avg Response Time"
              value={metrics.avgResponseTime}
              suffix="min"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ 
                color: metrics.avgResponseTime > 60 ? '#ff4d4f' : 
                       metrics.avgResponseTime > 30 ? '#fa8c16' : '#52c41a' 
              }}
              precision={1}
            />
          </Card>
        </Col>
      </Row>

      {/* Progress Indicators Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8}>
          <Card title="Resolution Progress" size="small">
            <Progress
              type="circle"
              percent={metrics.total > 0 ? Math.round((metrics.resolved / metrics.total) * 100) : 0}
              format={percent => (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{percent}%</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Resolved</div>
                </div>
              )}
              width={120}
            />
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Text type="secondary">
                {metrics.resolved} of {metrics.total} alerts resolved
              </Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card title="Acknowledgment Rate" size="small">
            <Progress
              type="circle"
              percent={metrics.active > 0 ? Math.round((metrics.acknowledged / (metrics.acknowledged + metrics.unacknowledged)) * 100) : 0}
              format={percent => (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{percent}%</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Acknowledged</div>
                </div>
              )}
              width={120}
              strokeColor="#52c41a"
            />
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Text type="secondary">
                {metrics.acknowledged} acknowledged, {metrics.unacknowledged} pending
              </Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card title="Critical Alert Ratio" size="small">
            <Progress
              type="circle"
              percent={metrics.active > 0 ? Math.round((metrics.critical / metrics.active) * 100) : 0}
              format={percent => (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{percent}%</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Critical</div>
                </div>
              )}
              width={120}
              strokeColor="#ff4d4f"
            />
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Text type="secondary">
                {metrics.critical} critical of {metrics.active} active
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={12}>
          <Card title="Alert Trends (7 Days)" size="small">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={metrics.alertTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Line type="monotone" dataKey="total" stroke="#1890ff" strokeWidth={2} />
                <Line type="monotone" dataKey="critical" stroke="#ff4d4f" strokeWidth={2} />
                <Line type="monotone" dataKey="resolved" stroke="#52c41a" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="Severity Distribution" size="small">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={severityPieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {severityPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Lists Row */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card 
            title={
              <Space>
                <TrophyOutlined />
                Top Active Clusters
              </Space>
            } 
            size="small"
          >
            {metrics.topClusters.length > 0 ? (
              <List
                size="small"
                dataSource={metrics.topClusters}
                renderItem={(item, index) => (
                  <List.Item>
                    <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>
                        <Badge count={index + 1} style={{ backgroundColor: '#1890ff', marginRight: 8 }} />
                        {item.cluster}
                      </span>
                      <Tag color="blue">{item.count}</Tag>
                    </div>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="No cluster data" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>
        
        <Col xs={24} md={8}>
          <Card 
            title={
              <Space>
                <TeamOutlined />
                Team Activity
              </Space>
            } 
            size="small"
          >
            {Object.keys(metrics.teamActivity).length > 0 ? (
              <List
                size="small"
                dataSource={Object.entries(metrics.teamActivity)
                  .sort(([,a], [,b]) => b - a)
                  .slice(0, 5)
                  .map(([person, count]) => ({ person, count }))}
                renderItem={(item) => (
                  <List.Item>
                    <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>
                        <TeamOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                        {item.person}
                      </span>
                      <Tag color="green">{item.count} actions</Tag>
                    </div>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="No team activity" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card 
            title={
              <Space>
                <RocketOutlined />
                Recent Activity
              </Space>
            } 
            size="small"
          >
            {metrics.recentActivity.length > 0 ? (
              <List
                size="small"
                dataSource={metrics.recentActivity.slice(0, 5)}
                renderItem={(alert) => (
                  <List.Item>
                    <div style={{ width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Tooltip title={alert.alert_name}>
                          <Text ellipsis style={{ maxWidth: '60%' }}>
                            {alert.alert_name}
                          </Text>
                        </Tooltip>
                        <Tag color="blue" size="small">
                          {alert.acknowledged_by}
                        </Tag>
                      </div>
                      <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
                        <ClockCircleOutlined style={{ marginRight: 4 }} />
                        {moment(alert.acknowledged_at).fromNow()}
                      </div>
                    </div>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="No recent activity" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardWidgets;