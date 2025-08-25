import React, { useState } from 'react';
import { ConfigProvider } from 'antd';
import AppLayout from './components/Layout';
import AlertTable from './components/AlertTable';
import ConfigPanel from './components/ConfigPanel';
import { useAlerts } from './hooks/useAlerts';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('alerts');
  const { alerts, loading, error, acknowledgeAlerts, resolveAlerts, syncAlerts } = useAlerts();

  const renderContent = () => {
    switch (currentPage) {
      case 'alerts':
        return (
          <AlertTable
            alerts={alerts}
            loading={loading}
            error={error}
            onAcknowledge={acknowledgeAlerts}
            onResolve={resolveAlerts}
            onSync={syncAlerts}
          />
        );
      case 'config':
        return <ConfigPanel />;
      default:
        return <div>Page not found</div>;
    }
  };

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <AppLayout currentPage={currentPage} onPageChange={setCurrentPage}>
        {renderContent()}
      </AppLayout>
    </ConfigProvider>
  );
}

export default App;
