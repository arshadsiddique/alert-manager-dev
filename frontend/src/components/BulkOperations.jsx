import React, { useState } from 'react';
import {
  Button,
  Dropdown,
  Menu,
  Modal,
  Form,
  Input,
  Select,
  message,
  Progress,
  Space,
  Tag,
  Divider
} from 'antd';
import {
  DownOutlined,
  CheckOutlined,
  CloseOutlined,
  DownloadOutlined,
  AppstoreOutlined, // Changed from BulkOutlined
  ExclamationCircleOutlined
} from '@ant-design/icons';

const { TextArea } = Input;
const { Option } = Select;

const BulkOperations = ({ 
  selectedAlerts, 
  onAcknowledge, 
  onResolve, 
  onClearSelection,
  alerts 
}) => {
  const [modalVisible, setModalVisible] = useState(false);
  const [operationType, setOperationType] = useState(null);
  const [form] = Form.useForm();
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);

  const selectedCount = selectedAlerts.length;

  // Get statistics about selected alerts
  const getSelectionStats = () => {
    if (selectedCount === 0) return null;

    const selected = alerts.filter(alert => selectedAlerts.includes(alert.id));
    
    const stats = {
      severities: {},
      clusters: {},
      statuses: {},
      assignees: {}
    };

    selected.forEach(alert => {
      // Count severities
      const severity = alert.severity || 'unknown';
      stats.severities[severity] = (stats.severities[severity] || 0) + 1;

      // Count clusters
      const cluster = alert.cluster || 'unknown';
      stats.clusters[cluster] = (stats.clusters[cluster] || 0) + 1;

      // Count Jira statuses
      const status = alert.jira_status || 'unknown';
      stats.statuses[status] = (stats.statuses[status] || 0) + 1;

      // Count assignees
      const assignee = alert.jira_assignee || 'unassigned';
      stats.assignees[assignee] = (stats.assignees[assignee] || 0) + 1;
    });

    return stats;
  };

  const stats = getSelectionStats();

  const handleBulkOperation = (operation) => {
    setOperationType(operation);
    setModalVisible(true);
    
    // Set default values based on operation
    if (operation === 'acknowledge') {
      form.setFieldsValue({
        user: localStorage.getItem('alertManager_username') || '',
        note: `Bulk acknowledged ${selectedCount} alerts`
      });
    } else if (operation === 'resolve') {
      form.setFieldsValue({
        user: localStorage.getItem('alertManager_username') || '',
        note: `Bulk resolved ${selectedCount} alerts`
      });
    }
  };

  const executeBulkOperation = async () => {
    try {
      const values = await form.validateFields();
      setIsProcessing(true);
      setProgress(0);

      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      let success = false;
      
      if (operationType === 'acknowledge') {
        success = await onAcknowledge(selectedAlerts, values.note, values.user);
      } else if (operationType === 'resolve') {
        success = await onResolve(selectedAlerts, values.note, values.user);
      }

      clearInterval(progressInterval);
      setProgress(100);

      setTimeout(() => {
        setIsProcessing(false);
        setProgress(0);
        
        if (success) {
          message.success(`Successfully ${operationType}d ${selectedCount} alerts`);
          setModalVisible(false);
          onClearSelection();
          form.resetFields();
        } else {
          message.error(`Failed to ${operationType} alerts`);
        }
      }, 500);

    } catch (error) {
      setIsProcessing(false);
      setProgress(0);
      console.error('Bulk operation failed:', error);
    }
  };

  const exportSelected = () => {
    const selected = alerts.filter(alert => selectedAlerts.includes(alert.id));
    
    const csvHeader = [
      'Alert ID', 'Alert Name', 'Cluster', 'Severity', 'Summary',
      'Grafana Status', 'Jira Status', 'Jira Issue', 'Assignee',
      'Acknowledged By', 'Acknowledged At', 'Resolved By', 'Resolved At',
      'Started At', 'Created At'
    ].join(',');

    const csvData = selected.map(alert => [
      alert.alert_id || '',
      `"${(alert.alert_name || '').replace(/"/g, '""')}"`,
      alert.cluster || '',
      alert.severity || '',
      `"${(alert.summary || '').replace(/"/g, '""')}"`,
      alert.grafana_status || '',
      alert.jira_status || '',
      alert.jira_issue_key || '',
      alert.jira_assignee || '',
      alert.acknowledged_by || '',
      alert.acknowledged_at || '',
      alert.resolved_by || '',
      alert.resolved_at || '',
      alert.started_at || '',
      alert.created_at || ''
    ].join(','));

    const csvContent = [csvHeader, ...csvData].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `alerts_export_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    message.success(`Exported ${selectedCount} alerts to CSV`);
  };

  const bulkMenu = (
    <Menu>
      <Menu.Item 
        key="acknowledge" 
        icon={<CheckOutlined />}
        onClick={() => handleBulkOperation('acknowledge')}
        disabled={selectedCount === 0}
      >
        Acknowledge Selected ({selectedCount})
      </Menu.Item>
      <Menu.Item 
        key="resolve" 
        icon={<CloseOutlined />}
        onClick={() => handleBulkOperation('resolve')}
        disabled={selectedCount === 0}
      >
        Resolve Selected ({selectedCount})
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item 
        key="export" 
        icon={<DownloadOutlined />}
        onClick={exportSelected}
        disabled={selectedCount === 0}
      >
        Export to CSV ({selectedCount})
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item 
        key="clear" 
        onClick={onClearSelection}
        disabled={selectedCount === 0}
      >
        Clear Selection
      </Menu.Item>
    </Menu>
  );

  return (
    <div>
      <Space>
        <Dropdown overlay={bulkMenu} trigger={['click']} disabled={selectedCount === 0}>
          <Button icon={<AppstoreOutlined />} disabled={selectedCount === 0}>
            Bulk Actions ({selectedCount}) <DownOutlined />
          </Button>
        </Dropdown>

        {selectedCount > 0 && (
          <Button 
            size="small" 
            onClick={onClearSelection}
            type="text"
          >
            Clear Selection
          </Button>
        )}
      </Space>

      {/* Selection Statistics */}
      {stats && selectedCount > 0 && (
        <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
          <Space wrap size={4}>
            <span>Selected:</span>
            {Object.entries(stats.severities).map(([severity, count]) => (
              <Tag key={severity} size="small" color={getSeverityColor(severity)}>
                {severity}: {count}
              </Tag>
            ))}
            {Object.keys(stats.clusters).length > 1 && (
              <Tag size="small">
                {Object.keys(stats.clusters).length} clusters
              </Tag>
            )}
          </Space>
        </div>
      )}

      {/* Bulk Operation Modal */}
      <Modal
        title={`Bulk ${operationType === 'acknowledge' ? 'Acknowledge' : 'Resolve'} Alerts`}
        open={modalVisible}
        onCancel={() => {
          if (!isProcessing) {
            setModalVisible(false);
            form.resetFields();
          }
        }}
        footer={null}
        closable={!isProcessing}
        maskClosable={!isProcessing}
      >
        <div style={{ marginBottom: 16 }}>
          <ExclamationCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />
          You are about to {operationType} <strong>{selectedCount} alerts</strong>.
        </div>

        {stats && (
          <div style={{ marginBottom: 16, padding: 12, background: '#fafafa', borderRadius: 4 }}>
            <div style={{ fontWeight: 'bold', marginBottom: 8 }}>Selection Summary:</div>
            <Space direction="vertical" size={4}>
              <div>
                <strong>Severities:</strong> {' '}
                {Object.entries(stats.severities).map(([severity, count]) => (
                  <Tag key={severity} size="small" color={getSeverityColor(severity)}>
                    {severity}: {count}
                  </Tag>
                ))}
              </div>
              <div>
                <strong>Clusters:</strong> {Object.keys(stats.clusters).join(', ')}
              </div>
              <div>
                <strong>Current Status:</strong> {' '}
                {Object.entries(stats.statuses).map(([status, count]) => (
                  <Tag key={status} size="small">
                    {status}: {count}
                  </Tag>
                ))}
              </div>
            </Space>
          </div>
        )}

        {isProcessing && (
          <div style={{ marginBottom: 16 }}>
            <Progress percent={progress} status="active" />
            <div style={{ textAlign: 'center', marginTop: 8, color: '#666' }}>
              Processing {operationType}...
            </div>
          </div>
        )}

        <Form
          form={form}
          layout="vertical"
          onFinish={executeBulkOperation}
        >
          <Form.Item
            name="user"
            label="Your Name"
            rules={[{ required: true, message: 'Please enter your name' }]}
          >
            <Input placeholder="Enter your name" disabled={isProcessing} />
          </Form.Item>

          <Form.Item
            name="note"
            label="Note"
            rules={[{ required: true, message: 'Please enter a note' }]}
          >
            <TextArea
              placeholder={`Add a note for this bulk ${operationType}...`}
              rows={3}
              disabled={isProcessing}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button 
                onClick={() => {
                  setModalVisible(false);
                  form.resetFields();
                }}
                disabled={isProcessing}
              >
                Cancel
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={isProcessing}
                danger={operationType === 'resolve'}
              >
                {operationType === 'acknowledge' ? 'Acknowledge' : 'Resolve'} {selectedCount} Alerts
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

// Helper function for severity colors
const getSeverityColor = (severity) => {
  const colors = {
    critical: 'red',
    warning: 'orange', 
    info: 'blue',
    unknown: 'default',
  };
  return colors[severity?.toLowerCase()] || 'default';
};

export default BulkOperations;