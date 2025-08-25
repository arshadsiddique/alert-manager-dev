import { useState, useEffect } from 'react';

const STORAGE_KEY = 'alertManager_filters';

export const useFilterPersistence = (initialFilters) => {
  const [filters, setFilters] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? { ...initialFilters, ...JSON.parse(saved) } : initialFilters;
    } catch (error) {
      console.warn('Failed to load saved filters:', error);
      return initialFilters;
    }
  });

  const [showAdvancedFilters, setShowAdvancedFilters] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY + '_advanced');
      return saved ? JSON.parse(saved) : false;
    } catch (error) {
      return false;
    }
  });

  // Save filters to localStorage whenever they change
  useEffect(() => {
    try {
      // Only save non-empty filters to avoid clutter
      const filtersToSave = Object.entries(filters).reduce((acc, [key, value]) => {
        if (value && (Array.isArray(value) ? value.length > 0 : true)) {
          acc[key] = value;
        }
        return acc;
      }, {});

      if (Object.keys(filtersToSave).length > 0) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(filtersToSave));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (error) {
      console.warn('Failed to save filters:', error);
    }
  }, [filters]);

  // Save advanced filter preference
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY + '_advanced', JSON.stringify(showAdvancedFilters));
    } catch (error) {
      console.warn('Failed to save advanced filter preference:', error);
    }
  }, [showAdvancedFilters]);

  const updateFilter = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const clearFilters = () => {
    setFilters(initialFilters);
    localStorage.removeItem(STORAGE_KEY);
  };

  const resetToDefaults = () => {
    setFilters(initialFilters);
    setShowAdvancedFilters(false);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_KEY + '_advanced');
  };

  return {
    filters,
    setFilters,
    updateFilter,
    clearFilters,
    resetToDefaults,
    showAdvancedFilters,
    setShowAdvancedFilters
  };
};