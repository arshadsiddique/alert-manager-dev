import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Switch, 
  Table, 
  Modal, 
  message,
  Space,
  Alert,
  Tag
} from 'antd';
import { PlusOutlined, EditOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { configApi } from '../services/api';

const ConfigPanel = () => {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [form] = Form.useForm();

  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const response = await configApi.getCronConfigs();
      setConfigs(response.data);
    } catch (error) {
      message.error('Failed to fetch configurations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, []);

  const handleSubmit = async (values) => {
    try {
      if (editingConfig) {
        await configApi.updateCronConfig(editingConfig.id, values);
        message.success('Configuration updated successfully');
      } else {
        await configApi.createCronConfig(values);
        message.success('Configuration created successfully');
      }
      setModalVisible(false);
      setEditingConfig(null);
      form.resetFields();
      fetchConfigs();
    } catch (error) {
      message.error('Failed to save configuration');
    }
  };

  const handleEdit = (config) => {
    setEditingConfig(config);
    form.setFieldsValue(config);
    setModalVisible(true);
  };

  const columns = [
    {
      title: 'Job Name',
      dataIndex: 'job_name',
      key: 'job_name',
      render: (text) => (
        <Space>
          <ThunderboltOutlined style={{ color: '#1890ff' }} />
          {text}
        </Space>
      ),
    },
    {
      title: 'Cron Expression',
      dataIndex: 'cron_expression',
      key: 'cron_expression',
      render: (text) => (
        <Tag color="blue">
          <code>{text}</code>
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? 'Enabled' : 'Disabled'}
        </Tag>
      ),
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Button
          icon={<EditOutlined />}
          onClick={() => handleEdit(record)}
          size="small"
        >
          Edit
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Alert
        message="JSM Sync Configuration"
        description="Configure when alerts are synchronized between Grafana and Jira Service Management. The system will automatically match alerts using alias, tags, and content similarity."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      <Card 
        title="Cron Job Configuration" 
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingConfig(null);
              form.resetFields();
              setModalVisible(true);
            }}
          >
            Add Job
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={loading}
          pagination={false}
        />

        <Modal
          title={editingConfig ? 'Edit Cron Job' : 'Create Cron Job'}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            setEditingConfig(null);
            form.resetFields();
          }}
          footer={null}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{ is_enabled: true }}
          >
            <Form.Item
              name="job_name"
              label="Job Name"
              rules={[{ required: true, message: 'Please input job name!' }]}
            >
              <Input placeholder="e.g., grafana-jsm-sync" disabled={editingConfig} />
            </Form.Item>

            <Form.Item
              name="cron_expression"
              label="Cron Expression"
              rules={[{ required: true, message: 'Please input cron expression!' }]}
              help="Example: */5 * * * * (every 5 minutes). Use https://crontab.guru for help."
            >
              <Input placeholder="*/5 * * * *" />
            </Form.Item>

            <Form.Item
              name="is_enabled"
              label="Enabled"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit">
                  {editingConfig ? 'Update' : 'Create'}
                </Button>
                <Button 
                  onClick={() => {
                    setModalVisible(false);
                    setEditingConfig(null);
                    form.resetFields();
                  }}
                >
                  Cancel
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      </Card>
    </div>
  );
};

export default ConfigPanel;
