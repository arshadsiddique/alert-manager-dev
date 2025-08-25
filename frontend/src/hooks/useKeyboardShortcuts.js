import { useEffect, useRef, useState } from 'react';
import { message, Modal } from 'antd';

export const useKeyboardShortcuts = ({
  onRefresh,
  onSelectAll,
  onClearSelection,
  onAcknowledge,
  onResolve,
  onToggleFilters,
  onFocusSearch,
  selectedCount = 0
}) => {
  const [shortcutsEnabled, setShortcutsEnabled] = useState(() => {
    const saved = localStorage.getItem('alertManager_keyboardShortcuts');
    return saved ? JSON.parse(saved) : true;
  });
  
  const [helpVisible, setHelpVisible] = useState(false);
  const pressedKeys = useRef(new Set());
  const lastKeyTime = useRef(0);

  // Keyboard shortcuts configuration
  const shortcuts = {
    // Navigation
    'KeyR': { action: onRefresh, description: 'Refresh alerts', label: 'R' },
    'KeyF': { action: onToggleFilters, description: 'Toggle advanced filters', label: 'F' },
    'Slash': { action: onFocusSearch, description: 'Focus search field', label: '/' },
    
    // Selection
    'KeyA': { action: onSelectAll, description: 'Select all alerts', label: 'A', requireCtrl: true },
    'Escape': { action: onClearSelection, description: 'Clear selection', label: 'Esc' },
    
    // Actions (require selection)
    'KeyK': { 
      action: () => selectedCount > 0 ? onAcknowledge() : message.warning('Select alerts first'),
      description: 'Acknowledge selected alerts',
      label: 'K',
      requireSelection: true
    },
    'KeyD': { 
      action: () => selectedCount > 0 ? onResolve() : message.warning('Select alerts first'),
      description: 'Resolve selected alerts',
      label: 'D',
      requireSelection: true
    },
    
    // Quick filters
    'Digit1': { action: () => applyQuickFilter('critical'), description: 'Show critical alerts', label: '1' },
    'Digit2': { action: () => applyQuickFilter('unacknowledged'), description: 'Show unacknowledged alerts', label: '2' },
    'Digit3': { action: () => applyQuickFilter('acknowledged'), description: 'Show acknowledged alerts', label: '3' },
    'Digit4': { action: () => applyQuickFilter('recent'), description: 'Show recent alerts', label: '4' },
    'Digit0': { action: () => applyQuickFilter('clear'), description: 'Clear all filters', label: '0' },
    
    // Help
    'KeyH': { action: () => setHelpVisible(true), description: 'Show keyboard shortcuts help', label: 'H', requireShift: true },
    'F1': { action: () => setHelpVisible(true), description: 'Show help', label: 'F1' }
  };

  // Quick filter actions (would need to be passed from parent)
  const applyQuickFilter = (filterType) => {
    // This would trigger the appropriate filter preset
    message.info(`Applied ${filterType} filter`);
  };

  // Save shortcuts preference
  useEffect(() => {
    localStorage.setItem('alertManager_keyboardShortcuts', JSON.stringify(shortcutsEnabled));
  }, [shortcutsEnabled]);

  // Key event handlers
  const handleKeyDown = (event) => {
    if (!shortcutsEnabled) return;

    // Don't trigger shortcuts when typing in input fields
    const activeElement = document.activeElement;
    const isInputFocused = activeElement && (
      activeElement.tagName === 'INPUT' ||
      activeElement.tagName === 'TEXTAREA' ||
      activeElement.contentEditable === 'true' ||
      activeElement.closest('.ant-select-selector') ||
      activeElement.closest('.ant-picker')
    );

    // Allow certain shortcuts even when input is focused
    const allowedWhenInputFocused = ['Escape', 'F1'];
    if (isInputFocused && !allowedWhenInputFocused.includes(event.code)) {
      return;
    }

    pressedKeys.current.add(event.code);
    lastKeyTime.current = Date.now();

    const shortcut = shortcuts[event.code];
    if (!shortcut) return;

    // Check modifiers
    const requiresCtrl = shortcut.requireCtrl && !event.ctrlKey;
    const requiresShift = shortcut.requireShift && !event.shiftKey;
    const requiresAlt = shortcut.requireAlt && !event.altKey;

    if (requiresCtrl || requiresShift || requiresAlt) {
      return;
    }

    // Check if selection is required
    if (shortcut.requireSelection && selectedCount === 0) {
      return;
    }

    // Prevent default behavior for handled shortcuts
    event.preventDefault();
    event.stopPropagation();

    try {
      shortcut.action();
      
      // Show feedback for certain actions
      if (['KeyR', 'KeyF', 'Slash'].includes(event.code)) {
        // Visual feedback handled by the actual action
      } else {
        // Show brief confirmation
        const feedback = getShortcutFeedback(event.code);
        if (feedback) {
          message.success(feedback, 1);
        }
      }
    } catch (error) {
      console.error('Shortcut execution error:', error);
      message.error('Shortcut failed to execute');
    }
  };

  const handleKeyUp = (event) => {
    pressedKeys.current.delete(event.code);
  };

  // Get feedback message for shortcuts
  const getShortcutFeedback = (code) => {
    const feedbackMap = {
      'KeyK': `Acknowledging ${selectedCount} alert${selectedCount > 1 ? 's' : ''}`,
      'KeyD': `Resolving ${selectedCount} alert${selectedCount > 1 ? 's' : ''}`,
      'Escape': 'Selection cleared',
      'Digit1': 'Showing critical alerts',
      'Digit2': 'Showing unacknowledged alerts',
      'Digit3': 'Showing acknowledged alerts',
      'Digit4': 'Showing recent alerts',
      'Digit0': 'Filters cleared'
    };
    return feedbackMap[code];
  };

  // Sequence detection for advanced shortcuts
  const checkKeySequence = () => {
    const now = Date.now();
    if (now - lastKeyTime.current > 1000) {
      pressedKeys.current.clear();
      return;
    }

    // Check for specific sequences
    const keys = Array.from(pressedKeys.current).sort();
    
    // Example: Ctrl+Shift+? for help
    if (keys.includes('ControlLeft') && keys.includes('ShiftLeft') && keys.includes('Slash')) {
      setHelpVisible(true);
      pressedKeys.current.clear();
    }
  };

  // Setup event listeners
  useEffect(() => {
    if (!shortcutsEnabled) return;

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    // Check for sequences periodically
    const sequenceTimer = setInterval(checkKeySequence, 100);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
      clearInterval(sequenceTimer);
    };
  }, [shortcutsEnabled, selectedCount, onRefresh, onSelectAll, onClearSelection, onAcknowledge, onResolve]);

  // Render help modal
  const renderHelpModal = () => (
    <Modal
      title="Keyboard Shortcuts"
      open={helpVisible}
      onCancel={() => setHelpVisible(false)}
      footer={null}
      width={600}
    >
      <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
        <div style={{ marginBottom: 24 }}>
          <h4>Navigation</h4>
          <div className="shortcut-group">
            <div className="shortcut-item">
              <kbd>R</kbd> <span>Refresh alerts</span>
            </div>
            <div className="shortcut-item">
              <kbd>F</kbd> <span>Toggle advanced filters</span>
            </div>
            <div className="shortcut-item">
              <kbd>/</kbd> <span>Focus search field</span>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 24 }}>
          <h4>Selection</h4>
          <div className="shortcut-group">
            <div className="shortcut-item">
              <kbd>Ctrl</kbd> + <kbd>A</kbd> <span>Select all alerts</span>
            </div>
            <div className="shortcut-item">
              <kbd>Esc</kbd> <span>Clear selection</span>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 24 }}>
          <h4>Actions (require selection)</h4>
          <div className="shortcut-group">
            <div className="shortcut-item">
              <kbd>K</kbd> <span>Acknowledge selected alerts</span>
            </div>
            <div className="shortcut-item">
              <kbd>D</kbd> <span>Resolve selected alerts</span>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 24 }}>
          <h4>Quick Filters</h4>
          <div className="shortcut-group">
            <div className="shortcut-item">
              <kbd>1</kbd> <span>Show critical alerts</span>
            </div>
            <div className="shortcut-item">
              <kbd>2</kbd> <span>Show unacknowledged alerts</span>
            </div>
            <div className="shortcut-item">
              <kbd>3</kbd> <span>Show acknowledged alerts</span>
            </div>
            <div className="shortcut-item">
              <kbd>4</kbd> <span>Show recent alerts</span>
            </div>
            <div className="shortcut-item">
              <kbd>0</kbd> <span>Clear all filters</span>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 24 }}>
          <h4>Help</h4>
          <div className="shortcut-group">
            <div className="shortcut-item">
              <kbd>Shift</kbd> + <kbd>H</kbd> <span>Show this help</span>
            </div>
            <div className="shortcut-item">
              <kbd>F1</kbd> <span>Show help</span>
            </div>
          </div>
        </div>

        <div style={{ 
          backgroundColor: '#f6f8fa', 
          padding: 16, 
          borderRadius: 6,
          marginTop: 24 
        }}>
          <h4 style={{ margin: 0, marginBottom: 8 }}>Tips</h4>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li>Shortcuts are disabled when typing in input fields</li>
            <li>Some shortcuts require alerts to be selected first</li>
            <li>Use <kbd>Esc</kbd> to cancel most operations</li>
            <li>Shortcuts can be disabled in Settings</li>
          </ul>
        </div>
      </div>

      <style jsx>{`
        .shortcut-group {
          margin-left: 16px;
        }
        .shortcut-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 4px 0;
          border-bottom: 1px solid #f0f0f0;
        }
        .shortcut-item:last-child {
          border-bottom: none;
        }
        kbd {
          display: inline-block;
          padding: 2px 6px;
          background-color: #fafafa;
          border: 1px solid #d9d9d9;
          border-radius: 3px;
          font-size: 12px;
          font-family: monospace;
          margin: 0 2px;
        }
        h4 {
          color: #1890ff;
          margin-bottom: 8px;
        }
      `}</style>
    </Modal>
  );

  // Show shortcut hint for first-time users
  const showShortcutHint = () => {
    const hasSeenHint = localStorage.getItem('alertManager_shortcutHint');
    if (!hasSeenHint && shortcutsEnabled) {
      setTimeout(() => {
        message.info(
          <span>
            💡 Tip: Press <kbd style={{ 
              padding: '2px 6px', 
              backgroundColor: '#f0f0f0', 
              borderRadius: '3px',
              fontSize: '12px'
            }}>Shift + H</kbd> for keyboard shortcuts
          </span>,
          5
        );
        localStorage.setItem('alertManager_shortcutHint', 'true');
      }, 2000);
    }
  };

  // Initialize hint
  useEffect(() => {
    showShortcutHint();
  }, []);

  return {
    shortcutsEnabled,
    setShortcutsEnabled,
    helpVisible,
    setHelpVisible,
    shortcuts,
    renderHelpModal
  };
};