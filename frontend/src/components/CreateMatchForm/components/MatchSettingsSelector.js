import React, { useState, useMemo } from 'react';
import { Radio, Space, Spin, Typography, Input, Button } from 'antd';
import { SortAscendingOutlined, SortDescendingOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { INFO_MESSAGES } from '../constants';

const { Title } = Typography;

/**
 * MatchSettingsSelector - Component for displaying and selecting match settings
 * Shows a scrollable list of radio buttons for available match settings
 * 
 * @param {Object} props
 * @param {Array} props.matchSettings - List of available match settings
 * @param {boolean} props.isLoading - Loading state indicator
 * @param {number|null} props.selectedValue - Currently selected match setting ID
 * @param {Function} props.onChange - Callback when selection changes
 * @returns {JSX.Element} Match settings selector component
 */
const MatchSettingsSelector = ({
  matchSettings,
  isLoading,
  selectedValue,
  onChange,
  disabled = false,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortStrategy, setSortStrategy] = useState('latest'); // 'latest', 'name_asc', 'name_desc'

  const handleSortLatest = () => {
    setSortStrategy(prev => (prev === 'latest' ? 'oldest' : 'latest'));
  };

  const handleSortAlpha = () => {
    setSortStrategy(prev => {
      if (prev === 'name_asc') return 'name_desc';
      return 'name_asc';
    });
  };

  const processedSettings = useMemo(() => {
    let result = [...matchSettings];

    // Filter
    if (searchTerm) {
      result = result.filter(setting =>
        setting.title.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Sort
    result.sort((a, b) => {
      if (sortStrategy === 'latest') {
        return b.match_set_id - a.match_set_id;
      }
      if (sortStrategy === 'oldest') {
        return a.match_set_id - b.match_set_id;
      }
      const titleA = a.title.toLowerCase();
      const titleB = b.title.toLowerCase();
      if (titleA < titleB) return sortStrategy === 'name_asc' ? -1 : 1;
      if (titleA > titleB) return sortStrategy === 'name_asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [matchSettings, searchTerm, sortStrategy]);

  return (
    <div className="match-settings-column">
      <div className="match-settings-header">
        <Title level={4}>Match Settings</Title>
        <p className="match-settings-subtitle">
          Select one match setting from the ready list
        </p>
      </div>

      {!isLoading && (
        <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
          <Input
            placeholder="Search settings..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{ flex: 1 }}
            allowClear
          />
          <Button
            onClick={handleSortLatest}
            type={['latest', 'oldest'].includes(sortStrategy) ? 'primary' : 'default'}
            icon={<ClockCircleOutlined />}
            title={sortStrategy === 'oldest' ? "Sort by created (Oldest)" : "Sort by created (Latest)"}
          />
          <Button
            onClick={handleSortAlpha}
            type={['name_asc', 'name_desc'].includes(sortStrategy) ? 'primary' : 'default'}
            icon={sortStrategy === 'name_desc' ? <SortDescendingOutlined /> : <SortAscendingOutlined />}
            title={sortStrategy === 'name_desc' ? "Sort Z-A" : "Sort A-Z"}
          />
        </div>
      )}

      <div className="match-settings-scrollable">
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="Loading match settings..." />
          </div>
        ) : (
          <Radio.Group
            id="match-settings-radio-group"
            onChange={onChange}
            value={selectedValue}
            className="match-settings-radio-group"
            disabled={disabled}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {processedSettings.length > 0 ? (
                processedSettings.map((setting) => (
                  <Radio
                    key={setting.match_set_id}
                    value={setting.match_set_id}
                    className="match-setting-radio"
                    id={`match-setting-${setting.match_set_id}`}
                    data-testid={`match-setting-${setting.match_set_id}`}
                  >
                    <span className="match-setting-name">{setting.title}</span>
                  </Radio>
                ))
              ) : (
                <div className="no-settings-message" id="no-settings-message">
                  {searchTerm ? "No settings match your search." : INFO_MESSAGES.NO_READY_SETTINGS}
                </div>
              )}
            </Space>
          </Radio.Group>
        )}
      </div>
    </div>
  );
};

export default MatchSettingsSelector;

