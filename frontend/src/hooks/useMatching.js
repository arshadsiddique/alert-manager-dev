import { useState, useEffect } from 'react';
import { matchingApi } from '../services/api';

export const useMatching = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const fetchMatchingStats = async () => {
    setLoading(true);
    try {
      const response = await matchingApi.getStats();
      setMetrics(response.data);
    } catch (error) {
      console.error('Error fetching matching stats:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return {
    metrics,
    loading,
    fetchMatchingStats
  };
};