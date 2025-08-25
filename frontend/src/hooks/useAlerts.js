import { useState, useEffect } from 'react';
import { alertsApi } from '../services/api';

export const useAlerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await alertsApi.getAlerts();
      setAlerts(response.data || []);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const acknowledgeAlerts = async (alertIds, note, acknowledgedBy) => {
    try {
      if (acknowledgedBy) {
        localStorage.setItem('alertManager_username', acknowledgedBy);
      }
      
      await alertsApi.acknowledgeAlerts(alertIds, note, acknowledgedBy);
      await fetchAlerts();
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Error acknowledging alerts:', err);
      return false;
    }
  };

  const resolveAlerts = async (alertIds, note, resolvedBy) => {
    try {
      if (resolvedBy) {
        localStorage.setItem('alertManager_username', resolvedBy);
      }
      
      await alertsApi.resolveAlerts(alertIds, note, resolvedBy);
      await fetchAlerts();
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Error resolving alerts:', err);
      return false;
    }
  };

  const syncAlerts = async () => {
    try {
      setLoading(true);
      await alertsApi.syncAlerts();
      await fetchAlerts();
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Error syncing alerts:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    
    // Auto-refresh alerts every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return {
    alerts,
    loading,
    error,
    fetchAlerts,
    acknowledgeAlerts,
    resolveAlerts,
    syncAlerts,
  };
};
