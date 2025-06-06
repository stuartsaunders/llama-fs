import React, { useState, useEffect } from 'react';
import { Button } from '@nextui-org/button';

const UpdateSettings: React.FC = () => {
  const [autoUpdateEnabled, setAutoUpdateEnabled] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load current settings when component mounts
    const loadSettings = async () => {
      try {
        const enabled = await window.electron.updates.getUpdateSettings();
        setAutoUpdateEnabled(enabled);
      } catch (error) {
        console.error('Failed to load update settings:', error);
      }
    };
    loadSettings();
  }, []);

  const handleToggleAutoUpdate = async () => {
    setLoading(true);
    try {
      const newValue = !autoUpdateEnabled;
      await window.electron.updates.setUpdateSettings(newValue);
      setAutoUpdateEnabled(newValue);
    } catch (error) {
      console.error('Failed to update settings:', error);
    }
    setLoading(false);
  };

  const handleCheckForUpdates = async () => {
    setLoading(true);
    try {
      await window.electron.updates.checkForUpdates();
    } catch (error) {
      console.error('Failed to check for updates:', error);
    }
    setLoading(false);
  };

  return (
    <div className="update-settings p-4 border rounded-lg bg-gray-50 dark:bg-gray-800">
      <h3 className="text-lg font-semibold mb-3">Update Settings</h3>
      
      <div className="flex items-center justify-between mb-3">
        <div>
          <label className="text-sm font-medium">Auto-check for updates</label>
          <p className="text-xs text-gray-600 dark:text-gray-400">
            When enabled, the app will automatically check for updates on startup
          </p>
        </div>
        <Button
          size="sm"
          color={autoUpdateEnabled ? "success" : "default"}
          variant={autoUpdateEnabled ? "solid" : "bordered"}
          onPress={handleToggleAutoUpdate}
          isLoading={loading}
        >
          {autoUpdateEnabled ? "Enabled" : "Disabled"}
        </Button>
      </div>

      <Button
        size="sm"
        variant="bordered"
        onPress={handleCheckForUpdates}
        isLoading={loading}
        className="w-full"
      >
        Check for Updates Now
      </Button>
      
      <p className="text-xs text-gray-500 mt-2">
        Privacy note: Update checks make network requests to GitHub
      </p>
    </div>
  );
};

export default UpdateSettings;