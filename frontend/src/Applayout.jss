import React from "react";
import { Layout, Menu } from "antd";
import {
  UserOutlined,
  BellOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import "./App.css"; // your CSS file

const { Header, Sider, Content } = Layout;

export default function AppLayout() {
  return (
    <Layout style={{ minHeight: "100vh" }}>
      {/* Sidebar with Logo */}
      <Sider breakpoint="lg" collapsedWidth="0">
        <div className="ant-layout-sider-logo">
          {/* If logo is in public folder */}
          <img src="/devo.png" alt="Devo Logo" className="devo-logo" />
          {/* If logo is in src/assets, use:
              import devoLogo from './assets/devo.png';
              <img src={devoLogo} alt="Devo Logo" className="devo-logo" />
          */}
        </div>
        <Menu theme="dark" mode="inline" defaultSelectedKeys={["1"]}>
          <Menu.Item key="1" icon={<BellOutlined />}>
            Alerts
          </Menu.Item>
          <Menu.Item key="2" icon={<UserOutlined />}>
            Users
          </Menu.Item>
          <Menu.Item key="3" icon={<SettingOutlined />}>
            Settings
          </Menu.Item>
        </Menu>
      </Sider>

      {/* Main Layout */}
      <Layout>
        <Header className="alert-header">
          <h2 style={{ color: "#fff" }}>Alert Manager</h2>
        </Header>
        <Content style={{ margin: "16px" }}>
          <div style={{ padding: 24, background: "#fff", minHeight: 360 }}>
            Main content goes here...
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}