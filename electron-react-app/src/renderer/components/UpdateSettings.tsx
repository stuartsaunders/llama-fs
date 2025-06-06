import React, { useState, useEffect } from 'react';
import { Button } from '@nextui-org/button';
import { Input } from '@nextui-org/input';

const UpdateSettings: React.FC = () => {
  const [autoUpdateEnabled, setAutoUpdateEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // LLM Configuration state
  const [llmProvider, setLlmProvider] = useState('local');
  const [localLlmUrl, setLocalLlmUrl] = useState('http://127.0.0.1:1234');
  const [groqConfigured, setGroqConfigured] = useState(false);
  const [llmLoading, setLlmLoading] = useState(false);
  
  // AgentOps Configuration state
  const [agentOpsEnabled, setAgentOpsEnabled] = useState(false);
  const [agentOpsConfigured, setAgentOpsConfigured] = useState(false);
  const [agentOpsLoading, setAgentOpsLoading] = useState(false);

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
    
    const loadLlmConfig = async () => {
      try {
        const response = await fetch('http://localhost:8000/llm-config');
        if (response.ok) {
          const config = await response.json();
          setLlmProvider(config.current_provider);
          setLocalLlmUrl(config.local_llm_base_url);
          setGroqConfigured(config.groq_configured);
        }
      } catch (error) {
        console.error('Failed to load LLM config:', error);
      }
    };
    
    const loadAgentOpsConfig = async () => {
      try {
        const response = await fetch('http://localhost:8000/agentops-config');
        if (response.ok) {
          const config = await response.json();
          setAgentOpsEnabled(config.agentops_enabled);
          setAgentOpsConfigured(config.agentops_configured);
        }
      } catch (error) {
        console.error('Failed to load AgentOps config:', error);
      }
    };
    
    loadSettings();
    loadLlmConfig();
    loadAgentOpsConfig();
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

  const handleLlmProviderChange = async (provider: string) => {
    setLlmLoading(true);
    try {
      const response = await fetch('http://localhost:8000/llm-config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider,
          local_llm_base_url: localLlmUrl,
        }),
      });

      if (response.ok) {
        setLlmProvider(provider);
        console.log(`Successfully switched to ${provider} provider`);
      } else {
        console.error('Failed to update LLM provider:', response.status, response.statusText);
        alert(`Failed to update LLM provider: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to update LLM provider:', error);
      alert(`Error connecting to server: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
    setLlmLoading(false);
  };

  const handleLocalLlmConfigUpdate = async () => {
    setLlmLoading(true);
    try {
      const response = await fetch('http://localhost:8000/llm-config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: llmProvider,
          local_llm_base_url: localLlmUrl,
        }),
      });

      if (!response.ok) {
        console.error('Failed to update local LLM configuration');
      }
    } catch (error) {
      console.error('Failed to update local LLM configuration:', error);
    }
    setLlmLoading(false);
  };

  const handleToggleAgentOps = async () => {
    setAgentOpsLoading(true);
    try {
      const newValue = !agentOpsEnabled;
      const response = await fetch('http://localhost:8000/agentops-config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          enabled: newValue,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setAgentOpsEnabled(newValue);
        if (result.restart_required) {
          alert('AgentOps configuration updated. Server restart required for changes to take effect.');
        }
      } else {
        console.error('Failed to update AgentOps configuration');
        alert('Failed to update AgentOps configuration');
      }
    } catch (error) {
      console.error('Failed to update AgentOps configuration:', error);
      alert(`Error connecting to server: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
    setAgentOpsLoading(false);
  };

  return (
    <div className="update-settings p-4 border rounded-lg bg-gray-50 dark:bg-gray-800">
      <h3 className="text-lg font-semibold mb-3">Update Settings</h3>

      <div className="flex items-center justify-between mb-3">
        <div>
          <label className="text-sm font-medium">Auto-check for updates</label>
          <p className="text-xs text-gray-600 dark:text-gray-400">
            When enabled, the app will automatically check for updates on
            startup
          </p>
        </div>
        <Button
          size="sm"
          color={autoUpdateEnabled ? 'success' : 'default'}
          variant={autoUpdateEnabled ? 'solid' : 'bordered'}
          onPress={handleToggleAutoUpdate}
          isLoading={loading}
        >
          {autoUpdateEnabled ? 'Enabled' : 'Disabled'}
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
      
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-600">
        <h4 className="text-md font-semibold mb-3">Analytics Settings</h4>
        
        <div className="flex items-center justify-between mb-3">
          <div>
            <label className="text-sm font-medium">AgentOps Tracking</label>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Enable analytics tracking for development insights (disabled by default)
            </p>
          </div>
          <Button
            size="sm"
            color={agentOpsEnabled ? 'success' : 'default'}
            variant={agentOpsEnabled ? 'solid' : 'bordered'}
            onPress={handleToggleAgentOps}
            isLoading={agentOpsLoading}
            isDisabled={!agentOpsConfigured}
          >
            {agentOpsEnabled ? 'Enabled' : 'Disabled'}
          </Button>
        </div>

        {!agentOpsConfigured && (
          <p className="text-xs text-orange-600 dark:text-orange-400">
            Note: AgentOps is disabled (no API key configured in server .env)
          </p>
        )}

        <p className="text-xs text-gray-500 mt-2">
          Privacy note: When enabled, sends anonymous usage data to AgentOps for analytics
        </p>
      </div>
      
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-600">
        <h4 className="text-md font-semibold mb-3">LLM Provider Settings</h4>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">Current Provider</label>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Choose between local LLM API or remote Groq
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                color={llmProvider === 'local' ? 'success' : 'default'}
                variant={llmProvider === 'local' ? 'solid' : 'bordered'}
                onPress={() => handleLlmProviderChange('local')}
                isLoading={llmLoading}
              >
                Local API
              </Button>
              <Button
                size="sm"
                color={llmProvider === 'groq' ? 'success' : 'default'}
                variant={llmProvider === 'groq' ? 'solid' : 'bordered'}
                onPress={() => handleLlmProviderChange('groq')}
                isLoading={llmLoading}
                isDisabled={!groqConfigured}
              >
                Groq
              </Button>
            </div>
          </div>

          {llmProvider === 'local' && (
            <div className="space-y-2 p-3 bg-gray-100 dark:bg-gray-700 rounded">
              <div>
                <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  Local LLM API URL
                </label>
                <Input
                  size="sm"
                  value={localLlmUrl}
                  onChange={(e) => setLocalLlmUrl(e.target.value)}
                  onBlur={handleLocalLlmConfigUpdate}
                  placeholder="http://127.0.0.1:1234"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Works with Ollama, LM Studio, or any OpenAI-compatible API
                </p>
              </div>
            </div>
          )}

          {!groqConfigured && (
            <p className="text-xs text-orange-600 dark:text-orange-400">
              Note: Groq is disabled (no API key configured in server .env)
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default UpdateSettings;
