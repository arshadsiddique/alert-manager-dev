import React, { useState } from 'react';
import { Layout, Menu, Typography, Space, Badge } from 'antd';
import { 
  AlertOutlined, 
  SettingOutlined, 
  DashboardOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

const AppLayout = ({ children, currentPage, onPageChange }) => {
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    {
      key: 'alerts',
      icon: <AlertOutlined />,
      label: 'JSM Alerts',
    },
    {
      key: 'config',
      icon: <SettingOutlined />,
      label: 'Configuration',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        theme="dark"
      >
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <ThunderboltOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
          {!collapsed && (
            <div style={{ color: 'white', marginTop: '8px', fontSize: '12px' }}>
              Devo Alert Manager
              <Badge count="v1.0" style={{ backgroundColor: '#52c41a', marginLeft: 8 }} />
            </div>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[currentPage]}
          items={menuItems}
          onClick={({ key }) => onPageChange(key)}
        />
      </Sider>
      
      <Layout>
        <Header style={{ background: 'white', padding: '0 24px' }}>
          <Space>
            <Title level={3} style={{ margin: 0 }}>
              Devo Alert Manager
            </Title>
            <Badge count="JSM" style={{ backgroundColor: '#1890ff' }} />
            <span style={{ color: '#666', fontSize: '14px' }}>
              Sync alerts from Grafana to Jira Service Management
            </span>
          </Space>
        </Header>
        
        <Content style={{ margin: '24px', background: 'white', padding: '24px' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
