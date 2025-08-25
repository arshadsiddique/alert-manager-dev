import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Space, 
  Tag, 
  Tooltip, 
  Button, 
  Switch, 
  Dropdown, 
  Menu,
  Badge,
  Statistic,
  Row,
  Col
} from 'antd';
import {
  SyncOutlined,
  WifiOutlined,
  ClockCircleOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { useRealTimeUpdates } from '../hooks/useRealTimeUpdates';

const StatusIndicator = ({ 
  alerts, 
  loading, 
  error, 
  onRefresh, 
  filteredCount,
  selectedCount 
}) => {
  const {
    isRealTimeEnabled,
    toggleRealTime,
    forceRefresh,
    getTimeSinceLastUpdate,
    getNextUpdateIn,
    intervalSeconds,
    updateCount
  } = useRealTimeUpdates(onRefresh);

  const [connectionStatus, setConnectionStatus] = useState('online');

  // Monitor connection status
  useEffect(() => {
    const handleOnline = () => setConnectionStatus('online');
    const handleOffline = () => setConnectionStatus('offline');

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Calculate alert statistics
  const getAlertStats = () => {
    if (!alerts || alerts.length === 0) {
      return {
        total: 0,
        active: 0,
        critical: 0,
        unacknowledged: 0,
        resolved: 0
      };
    }

    return {
      total: alerts.length,
      active: alerts.filter(a => a.grafana_status === 'active').length,
      critical: alerts.filter(a => a.severity === 'critical' && a.grafana_status === 'active').length,
      unacknowledged: alerts.filter(a => a.jira_status === 'open' && a.grafana_status === 'active').length,
      resolved: alerts.filter(a => a.jira_status === 'resolved').length
    };
  };

  const stats = getAlertStats();
  const nextUpdate = getNextUpdateIn();

  const intervalMenu = (
    <Menu>
      <Menu.Item key="10" onClick={() => localStorage.setItem('alertManager_interval', '10')}>
        10 seconds
      </Menu.Item>
      <Menu.Item key="30" onClick={() => localStorage.setItem('alertManager_interval', '30')}>
        30 seconds (default)
      </Menu.Item>
      <Menu.Item key="60" onClick={() => localStorage.setItem('alertManager_interval', '60')}>
        1 minute
      </Menu.Item>
      <Menu.Item key="300" onClick={() => localStorage.setItem('alertManager_interval', '300')}>
        5 minutes
      </Menu.Item>
    </Menu>
  );

  const getStatusColor = () => {
    if (connectionStatus === 'offline') return '#ff4d4f';
    if (error) return '#ff4d4f';
    if (loading) return '#1890ff';
    if (stats.critical > 0) return '#ff4d4f';
    if (stats.unacknowledged > 0) return '#fa8c16';
    return '#52c41a';
  };

  const getStatusIcon = () => {
    if (connectionStatus === 'offline') return <CloseCircleOutlined />;
    if (error) return <ExclamationCircleOutlined />;
    if (loading) return <SyncOutlined spin />;
    if (stats.critical > 0) return <ExclamationCircleOutlined />;
    return <CheckCircleOutlined />;
  };

  const getStatusText = () => {
    if (connectionStatus === 'offline') return 'Offline';
    if (error) return 'Error';
    if (loading) return 'Updating...';
    if (stats.critical > 0) return `${stats.critical} Critical`;
    if (stats.unacknowledged > 0) return `${stats.unacknowledged} Unacked`;
    return 'All Clear';
  };

  return (
    <Card size="small" style={{ marginBottom: 16 }}>
      <Row gutter={16} align="middle">
        {/* System Status */}
        <Col xs={24} sm={12} md={8} lg={6}>
          <Space>
            <Badge 
              color={getStatusColor()} 
              text={
                <Space>
                  {getStatusIcon()}
                  <span style={{ fontWeight: 'bold' }}>
                    {getStatusText()}
                  </span>
                </Space>
              } 
            />
          </Space>
        </Col>

        {/* Alert Statistics */}
        <Col xs={24} sm={12} md={8} lg={6}>
          <Space size="large">
            <Statistic 
              title="Total" 
              value={stats.total} 
              valueStyle={{ fontSize: '14px' }}
            />
            <Statistic 
              title="Active" 
              value={stats.active} 
              valueStyle={{ fontSize: '14px', color: stats.active > 0 ? '#fa8c16' : '#52c41a' }}
            />
            <Statistic 
              title="Critical" 
              value={stats.critical} 
              valueStyle={{ fontSize: '14px', color: stats.critical > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Space>
        </Col>

        {/* Filter Info */}
        <Col xs={24} sm={12} md={4} lg={4}>
          <Space direction="vertical" size={0}>
            {filteredCount !== stats.total && (
              <div>
                <EyeOutlined style={{ marginRight: 4 }} />
                <span style={{ fontSize: '12px' }}>
                  Showing {filteredCount} of {stats.total}
                </span>
              </div>
            )}
            {selectedCount > 0 && (
              <div>
                <Tag size="small" color="blue">
                  {selectedCount} selected
                </Tag>
              </div>
            )}
          </Space>
        </Col>

        {/* Real-time Controls */}
        <Col xs={24} sm={12} md={4} lg={8}>
          <Space>
            {/* Real-time Toggle */}
            <Tooltip title={isRealTimeEnabled ? 'Disable real-time updates' : 'Enable real-time updates'}>
              <Switch
                checked={isRealTimeEnabled}
                onChange={toggleRealTime}
                checkedChildren={<WifiOutlined />}
                unCheckedChildren={<WifiOutlined />}
                size="small"
              />
            </Tooltip>

            {/* Update Info */}
            <Space size={4}>
              <Tooltip title={`Last updated: ${getTimeSinceLastUpdate()}`}>
                <Button 
                  size="small" 
                  icon={<ReloadOutlined />} 
                  onClick={forceRefresh}
                  loading={loading}
                >
                  Refresh
                </Button>
              </Tooltip>

              {isRealTimeEnabled && nextUpdate && (
                <Tooltip title="Next automatic update">
                  <Tag 
                    size="small" 
                    icon={<ClockCircleOutlined />}
                    color={nextUpdate === 'updating...' ? 'blue' : 'default'}
                  >
                    {nextUpdate}
                  </Tag>
                </Tooltip>
              )}
            </Space>

            {/* Settings */}
            <Dropdown overlay={intervalMenu} trigger={['click']}>
              <Button size="small" icon={<SettingOutlined />} />
            </Dropdown>
          </Space>
        </Col>
      </Row>

      {/* Additional Info Row */}
      <Row style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
        <Col span={24}>
          <Space split={<span>•</span>}>
            <span>Updates: {updateCount}</span>
            <span>Last: {getTimeSinceLastUpdate()}</span>
            <span>Interval: {intervalSeconds}s</span>
            <span>Connection: {connectionStatus}</span>
            {error && (
              <Tooltip title={error.message}>
                <span style={{ color: '#ff4d4f' }}>
                  Error: {error.message?.substring(0, 30)}...
                </span>
              </Tooltip>
            )}
          </Space>
        </Col>
      </Row>
    </Card>
  );
};

export default StatusIndicator;