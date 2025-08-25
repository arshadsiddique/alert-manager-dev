import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Switch,
  Select,
  Button,
  Space,
  Divider,
  Alert,
  InputNumber,
  message,
  Row,
  Col,
  Typography,
  Collapse,
  Tag,
  Tabs,
  Modal
} from 'antd';
import {
  SettingOutlined,
  SaveOutlined,
  ReloadOutlined,
  DeleteOutlined,
  ExportOutlined,
  ImportOutlined,
  WarningOutlined,
  BellOutlined,
  KeyboardOutlined
} from '@ant-design/icons';
import NotificationSettings from './NotificationSettings';

const { Option } = Select;
const { Title, Text } = Typography;
const { Panel } = Collapse;
const { TabPane } = Tabs;

const AdvancedConfig = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Load settings from localStorage
  const loadSettings = () => {
    const defaultSettings = {
      // Display Settings
      theme: 'light',
      tableSize: 'small',
      showTimestamps: true,
      dateFormat: 'YYYY-MM-DD HH:mm:ss',
      timeZone: 'local',
      
      // Refresh Settings
      autoRefresh: true,
      refreshInterval: 30,
      refreshOnFocus: true,
      
      // Filter Settings
      rememberFilters: true,
      showAdvancedFilters: false,
      defaultPageSize: 50,
      
      // Notification Settings
      showNotifications: true,
      notifyOnNewAlerts: true,
      notifyOnStatusChange: false,
      soundEnabled: false,
      
      // Performance Settings
      maxAlertsToLoad: 1000,
      enableVirtualization: false,
      debounceMs: 300,
      
      // Export Settings
      exportFormat: 'csv',
      includeResolvedInExport: false,
      
      // Debug Settings
      debugMode: false,
      logLevel: 'warn',
      enableErrorReporting: true
    };

    try {
      const saved = localStorage.getItem('alertManager_advancedSettings');
      const settings = saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
      form.setFieldsValue(settings);
      return settings;
    } catch (error) {
      console.error('Failed to load settings:', error);
      form.setFieldsValue(defaultSettings);
      return defaultSettings;
    }
  };

  // Save settings to localStorage
  const saveSettings = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      localStorage.setItem('alertManager_advancedSettings', JSON.stringify(values));
      
      // Apply settings immediately
      applySettings(values);
      
      setHasChanges(false);
      message.success('Settings saved successfully');
    } catch (error) {
      message.error('Failed to save settings');
      console.error('Settings save error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Apply settings to the application
  const applySettings = (settings) => {
    // Apply theme
    if (settings.theme === 'dark') {
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
    }

    // Apply other settings
    localStorage.setItem('alertManager_refreshInterval', settings.refreshInterval.toString());
    localStorage.setItem('alertManager_autoRefresh', JSON.stringify(settings.autoRefresh));
    localStorage.setItem('alertManager_pageSize', settings.defaultPageSize.toString());
  };

  // Reset to defaults
  const resetToDefaults = () => {
    Modal.confirm({
      title: 'Reset to Default Settings',
      content: 'Are you sure you want to reset all settings to their default values? This cannot be undone.',
      icon: <WarningOutlined />,
      okText: 'Reset',
      okType: 'danger',
      onOk: () => {
        localStorage.removeItem('alertManager_advancedSettings');
        loadSettings();
        setHasChanges(false);
        message.success('Settings reset to defaults');
      }
    });
  };

  // Export settings
  const exportSettings = () => {
    try {
      const settings = form.getFieldsValue();
      const blob = new Blob([JSON.stringify(settings, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `alert-manager-settings-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      message.success('Settings exported');
    } catch (error) {
      message.error('Failed to export settings');
    }
  };

  // Import settings
  const importSettings = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imported = JSON.parse(e.target.result);
        form.setFieldsValue(imported);
        setHasChanges(true);
        message.success('Settings imported successfully');
      } catch (error) {
        message.error('Invalid settings file');
      }
    };
    reader.readAsText(file);
    
    // Clear the input
    event.target.value = '';
  };

  // Clear all data
  const clearAllData = () => {
    Modal.confirm({
      title: 'Clear All Data',
      content: 'This will clear all saved filters, preferences, and settings. This cannot be undone.',
      icon: <DeleteOutlined />,
      okText: 'Clear All',
      okType: 'danger',
      onOk: () => {
        // Clear all localStorage items related to alert manager
        Object.keys(localStorage)
          .filter(key => key.startsWith('alertManager_'))
          .forEach(key => localStorage.removeItem(key));
        
        loadSettings();
        setHasChanges(false);
        message.success('All data cleared');
      }
    });
  };

  useEffect(() => {
    loadSettings();
  }, []);

  // Watch for form changes
  const handleFormChange = () => {
    setHasChanges(true);
  };

  return (
    <div>
      <Alert
        message="Advanced Configuration"
        description="These settings control the behavior and appearance of the Alert Manager. Changes are saved locally in your browser."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Tabs defaultActiveKey="display" type="card">
        <TabPane 
          tab={
            <span>
              <SettingOutlined />
              Display & Performance
            </span>
          } 
          key="display"
        >
          <Form
            form={form}
            layout="vertical"
            onValuesChange={handleFormChange}
          >
            <Collapse defaultActiveKey={['display', 'refresh']} ghost>
          
          {/* Display Settings */}
          <Panel header="Display & Appearance" key="display">
            <Row gutter={16}>
              <Col xs={24} sm={12} md={8}>
                <Form.Item name="theme" label="Theme">
                  <Select>
                    <Option value="light">Light</Option>
                    <Option value="dark">Dark</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item name="tableSize" label="Table Size">
                  <Select>
                    <Option value="small">Compact</Option>
                    <Option value="middle">Medium</Option>
                    <Option value="large">Large</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item name="defaultPageSize" label="Default Page Size">
                  <Select>
                    <Option value={25}>25</Option>
                    <Option value={50}>50</Option>
                    <Option value={100}>100</Option>
                    <Option value={200}>200</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item name="showTimestamps" valuePropName="checked">
                  <Switch checkedChildren="Show" unCheckedChildren="Hide" />
                  <span style={{ marginLeft: 8 }}>Detailed Timestamps</span>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item name="dateFormat" label="Date Format">
                  <Select>
                    <Option value="YYYY-MM-DD HH:mm:ss">2024-01-01 14:30:00</Option>
                    <Option value="MM/DD/YYYY HH:mm">01/01/2024 14:30</Option>
                    <Option value="DD/MM/YYYY HH:mm">01/01/2024 14:30</Option>
                    <Option value="relative">Relative (2h ago)</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Panel>

          {/* Refresh Settings */}
          <Panel header="Auto-Refresh & Updates" key="refresh">
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item name="autoRefresh" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Auto-Refresh</span>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item name="refreshInterval" label="Refresh Interval (seconds)">
                  <InputNumber min={10} max={300} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item name="refreshOnFocus" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Refresh When Tab Becomes Active</span>
                </Form.Item>
              </Col>
            </Row>
          </Panel>

          {/* Filter Settings */}
          <Panel header="Filtering & Search" key="filters">
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item name="rememberFilters" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Remember Filter Settings</span>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item name="showAdvancedFilters" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Show Advanced Filters by Default</span>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} sm={12} md={8}>
                <Form.Item name="debounceMs" label="Search Delay (ms)">
                  <InputNumber min={100} max={1000} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
          </Panel>

          {/* Notification Settings */}
          <Panel header="Notifications" key="notifications">
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item name="showNotifications" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Show Notifications</span>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item name="notifyOnNewAlerts" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Notify on New Alerts</span>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item name="notifyOnStatusChange" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Notify on Status Changes</span>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item name="soundEnabled" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Sound Notifications</span>
                </Form.Item>
              </Col>
            </Row>
          </Panel>

          {/* Performance Settings */}
          <Panel header="Performance" key="performance">
            <Row gutter={16}>
              <Col xs={24} sm={12} md={8}>
                <Form.Item name="maxAlertsToLoad" label="Maximum Alerts to Load">
                  <InputNumber min={100} max={10000} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item name="enableVirtualization" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Enable Table Virtualization</span>
                </Form.Item>
              </Col>
            </Row>
          </Panel>

          {/* Debug Settings */}
          <Panel header="Debug & Development" key="debug">
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item name="debugMode" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Debug Mode</span>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item name="enableErrorReporting" valuePropName="checked">
                  <Switch checkedChildren="On" unCheckedChildren="Off" />
                  <span style={{ marginLeft: 8 }}>Error Reporting</span>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} sm={12} md={8}>
                <Form.Item name="logLevel" label="Console Log Level">
                  <Select>
                    <Option value="error">Error</Option>
                    <Option value="warn">Warning</Option>
                    <Option value="info">Info</Option>
                    <Option value="debug">Debug</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Panel>

        </Collapse>
      </Form>

      <Divider />

      {/* Action Buttons */}
      <Space wrap>
        <Button
          type="primary"
          icon={<SaveOutlined />}
          onClick={saveSettings}
          loading={loading}
          disabled={!hasChanges}
        >
          Save Settings
        </Button>

        <Button
          icon={<ReloadOutlined />}
          onClick={loadSettings}
          disabled={!hasChanges}
        >
          Discard Changes
        </Button>

        <Button
          icon={<ExportOutlined />}
          onClick={exportSettings}
        >
          Export Settings
        </Button>

        <Button icon={<ImportOutlined />}>
          <label style={{ cursor: 'pointer', margin: 0 }}>
            Import Settings
            <input
              type="file"
              accept=".json"
              onChange={importSettings}
              style={{ display: 'none' }}
            />
          </label>
        </Button>

        <Button
          danger
          icon={<DeleteOutlined />}
          onClick={resetToDefaults}
        >
          Reset to Defaults
        </Button>

        <Button
          danger
          icon={<DeleteOutlined />}
          onClick={clearAllData}
        >
          Clear All Data
        </Button>
      </Space>

      {hasChanges && (
        <Alert
          message="Unsaved Changes"
          description="You have unsaved changes. Click 'Save Settings' to apply them."
          type="warning"
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
        </TabPane>

        <TabPane 
          tab={
            <span>
              <BellOutlined />
              Notifications
            </span>
          } 
          key="notifications"
        >
          <NotificationSettings />
        </TabPane>

        <TabPane 
          tab={
            <span>
              <KeyboardOutlined />
              Keyboard Shortcuts
            </span>
          } 
          key="shortcuts"
        >
          <Card>
            <Alert
              message="Keyboard Shortcuts"
              description="Keyboard shortcuts are enabled by default. Use Shift + H to view all available shortcuts."
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <div style={{ padding: 16, background: '#fafafa', borderRadius: 6 }}>
              <Title level={4}>Quick Reference</Title>
              <Row gutter={[16, 8]}>
                <Col xs={24} sm={12}>
                  <Text strong>Navigation</Text>
                  <div style={{ marginLeft: 16, marginTop: 4 }}>
                    <div>R - Refresh alerts</div>
                    <div>F - Toggle filters</div>
                    <div>/ - Focus search</div>
                  </div>
                </Col>
                <Col xs={24} sm={12}>
                  <Text strong>Actions</Text>
                  <div style={{ marginLeft: 16, marginTop: 4 }}>
                    <div>K - Acknowledge</div>
                    <div>D - Resolve</div>
                    <div>Esc - Clear selection</div>
                  </div>
                </Col>
              </Row>
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <Button type="primary">
                  Press Shift + H for complete shortcut list
                </Button>
              </div>
            </div>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default AdvancedConfig;