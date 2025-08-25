import React from 'react';
import { Button, Space, Dropdown, Menu, message } from 'antd';
import { 
  FireOutlined, 
  ExclamationCircleOutlined, 
  CheckCircleOutlined,
  ClockCircleOutlined,
  BugOutlined,
  FilterOutlined
} from '@ant-design/icons';
import moment from 'moment';

const FilterPresets = ({ onApplyPreset, currentFilters }) => {
  const presets = [
    {
      key: 'critical',
      name: 'Critical Alerts',
      icon: <FireOutlined style={{ color: '#ff4d4f' }} />,
      filters: {
        severity: ['critical'],
        grafanaStatus: ['active']
      },
      description: 'Show only critical severity alerts that are active'
    },
    {
      key: 'unacknowledged',
      name: 'Unacknowledged',
      icon: <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />,
      filters: {
        grafanaStatus: ['active'],
        jiraStatus: ['open']
      },
      description: 'Show alerts that haven\'t been acknowledged yet'
    },
    {
      key: 'acknowledged',
      name: 'Acknowledged',
      icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      filters: {
        jiraStatus: ['acknowledged']
      },
      description: 'Show alerts that have been acknowledged'
    },
    {
      key: 'recent',
      name: 'Last 24 Hours',
      icon: <ClockCircleOutlined style={{ color: '#1890ff' }} />,
      filters: {
        dateRange: [
          moment().subtract(24, 'hours'),
          moment()
        ]
      },
      description: 'Show alerts from the last 24 hours'
    },
    {
      key: 'my-alerts',
      name: 'My Alerts',
      icon: <BugOutlined style={{ color: '#722ed1' }} />,
      filters: {}, // Will be populated with current user
      description: 'Show alerts assigned to or acknowledged by you'
    },
    {
      key: 'active-issues',
      name: 'Active with Issues',
      icon: <ExclamationCircleOutlined style={{ color: '#fa541c' }} />,
      filters: {
        grafanaStatus: ['active'],
        jiraStatus: ['open', 'acknowledged']
      },
      description: 'Show active alerts with open Jira issues'
    }
  ];

  const handlePresetClick = (preset) => {
    let filters = { ...preset.filters };
    
    // Special handling for "My Alerts" preset
    if (preset.key === 'my-alerts') {
      const username = localStorage.getItem('alertManager_username') || '';
      if (username) {
        filters = {
          acknowledgedBy: username,
          // Could also add assignee filter if we track it
        };
      } else {
        // If no username stored, show message
        message.info('Set your name by acknowledging an alert first');
        return;
      }
    }
    
    onApplyPreset(filters);
  };

  const isPresetActive = (preset) => {
    if (preset.key === 'my-alerts') {
      const username = localStorage.getItem('alertManager_username') || '';
      return currentFilters.acknowledgedBy === username;
    }
    
    // Check if current filters match preset filters
    return Object.entries(preset.filters).every(([key, value]) => {
      const currentValue = currentFilters[key];
      
      if (Array.isArray(value) && Array.isArray(currentValue)) {
        return value.length === currentValue.length && 
               value.every(v => currentValue.includes(v));
      }
      
      return JSON.stringify(currentValue) === JSON.stringify(value);
    });
  };

  const menu = (
    <Menu>
      {presets.map(preset => (
        <Menu.Item 
          key={preset.key}
          onClick={() => handlePresetClick(preset)}
          style={{ 
            backgroundColor: isPresetActive(preset) ? '#e6f7ff' : 'transparent'
          }}
        >
          <Space>
            {preset.icon}
            <div>
              <div style={{ fontWeight: 'bold' }}>{preset.name}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                {preset.description}
              </div>
            </div>
          </Space>
        </Menu.Item>
      ))}
    </Menu>
  );

  // Quick preset buttons for most common ones
  const quickPresets = presets.slice(0, 4);

  return (
    <Space wrap>
      {/* Quick preset buttons */}
      {quickPresets.map(preset => (
        <Button
          key={preset.key}
          size="small"
          type={isPresetActive(preset) ? 'primary' : 'default'}
          icon={preset.icon}
          onClick={() => handlePresetClick(preset)}
        >
          {preset.name}
        </Button>
      ))}
      
      {/* More presets dropdown */}
      <Dropdown overlay={menu} trigger={['click']}>
        <Button size="small" icon={<FilterOutlined />}>
          More Filters
        </Button>
      </Dropdown>
    </Space>
  );
};

export default FilterPresets;