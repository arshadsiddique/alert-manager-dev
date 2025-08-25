import { useState, useEffect, useRef } from 'react';
import { message } from 'antd';

export const useRealTimeUpdates = (fetchAlerts, intervalSeconds = 30) => {
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(() => {
    const saved = localStorage.getItem('alertManager_realTimeEnabled');
    return saved ? JSON.parse(saved) : true;
  });
  
  const [lastUpdateTime, setLastUpdateTime] = useState(new Date());
  const [updateCount, setUpdateCount] = useState(0);
  const intervalRef = useRef(null);
  const isVisibleRef = useRef(true);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      isVisibleRef.current = !document.hidden;
      
      if (!document.hidden && isRealTimeEnabled) {
        // Page became visible, do immediate refresh
        fetchAlerts();
        setLastUpdateTime(new Date());
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [fetchAlerts, isRealTimeEnabled]);

  // Save real-time preference
  useEffect(() => {
    localStorage.setItem('alertManager_realTimeEnabled', JSON.stringify(isRealTimeEnabled));
  }, [isRealTimeEnabled]);

  // Setup/cleanup interval
  useEffect(() => {
    if (isRealTimeEnabled) {
      intervalRef.current = setInterval(() => {
        // Only update if page is visible
        if (isVisibleRef.current) {
          fetchAlerts();
          setLastUpdateTime(new Date());
          setUpdateCount(prev => prev + 1);
        }
      }, intervalSeconds * 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRealTimeEnabled, intervalSeconds, fetchAlerts]);

  const toggleRealTime = () => {
    setIsRealTimeEnabled(!isRealTimeEnabled);
    
    if (!isRealTimeEnabled) {
      // If enabling, do immediate refresh
      fetchAlerts();
      setLastUpdateTime(new Date());
      message.success('Real-time updates enabled');
    } else {
      message.info('Real-time updates disabled');
    }
  };

  const forceRefresh = () => {
    fetchAlerts();
    setLastUpdateTime(new Date());
    setUpdateCount(prev => prev + 1);
  };

  const getTimeSinceLastUpdate = () => {
    const now = new Date();
    const diffMs = now - lastUpdateTime;
    const diffSeconds = Math.floor(diffMs / 1000);
    
    if (diffSeconds < 60) {
      return `${diffSeconds}s ago`;
    } else if (diffSeconds < 3600) {
      return `${Math.floor(diffSeconds / 60)}m ago`;
    } else {
      return `${Math.floor(diffSeconds / 3600)}h ago`;
    }
  };

  const getNextUpdateIn = () => {
    if (!isRealTimeEnabled) return null;
    
    const now = new Date();
    const nextUpdate = new Date(lastUpdateTime.getTime() + (intervalSeconds * 1000));
    const diffMs = nextUpdate - now;
    const diffSeconds = Math.ceil(diffMs / 1000);
    
    if (diffSeconds <= 0) return 'updating...';
    
    return `${diffSeconds}s`;
  };

  return {
    isRealTimeEnabled,
    toggleRealTime,
    forceRefresh,
    lastUpdateTime,
    updateCount,
    getTimeSinceLastUpdate,
    getNextUpdateIn,
    intervalSeconds
  };
};