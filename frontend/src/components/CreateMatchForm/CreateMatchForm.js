import React, { useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Form, Button, Card, Tooltip, Typography } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useAlert } from './hooks/useAlert';
import { useMatchSettings } from './hooks/useMatchSettings';
import { useMatchForm } from './hooks/useMatchForm';
import AlertNotification from './components/AlertNotification';
import MatchSettingsSelector from './components/MatchSettingsSelector';
import MatchFormFields from './components/MatchFormFields';
import './CreateMatchForm.css';

const { Title } = Typography;

const CreateMatchForm = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const location = useLocation();
  const [form] = Form.useForm();

  // Determine mode from route
  const isViewMode = location.pathname.includes('/view');
  const isEditMode = location.pathname.includes('/edit') && !!id;
  const matchId = id ? parseInt(id, 10) : null;

  const pageTitle = isViewMode
    ? 'View Match'
    : isEditMode
      ? 'Edit Match'
      : 'Create New Match';

  // Custom hooks for state management
  const { alert, showAlert, hideAlert, resetAlert } = useAlert();
  const { matchSettings, isLoading } = useMatchSettings(showAlert);
  const {
    selectedMatchSetting,
    isSubmitting,
    isFormValid,
    handleFormChange,
    handleMatchSettingChange,
    handleSubmit,
    handleReset: resetForm,
    loadMatch,
  } = useMatchForm(form, showAlert, isEditMode, matchId);

  // Load match data when editing or viewing
  useEffect(() => {
    if ((isEditMode || isViewMode) && matchId) {
      loadMatch(matchId);
    }
  }, [isEditMode, isViewMode, matchId, loadMatch]);

  /**
   * Handles form reset including alert state
   */
  const handleReset = () => {
    resetForm(resetAlert);
  };

  const backRoute = (isEditMode || isViewMode) ? '/matches' : '/home';

  return (
    <div className="create-match-container">
      <Card className="create-match-card">
        {/* Page Header */}
        <div className="page-header">
          <Title level={2}>{pageTitle}</Title>
          <Tooltip title={isEditMode || isViewMode ? "Back to Matches" : "Back to Home"}>
            <Button
              id="back-to-home-button"
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate(backRoute)}
              shape="circle"
              size="large"
            />
          </Tooltip>
        </div>

        {/* Alert Notification */}
        {alert.visible && (
          <AlertNotification
            type={alert.type}
            message={alert.message}
            onClose={hideAlert}
          />
        )}

        {/* Two-column layout: Match Settings + Form Fields */}
        <div className="form-layout">
          <MatchSettingsSelector
            matchSettings={matchSettings}
            isLoading={isLoading}
            selectedValue={selectedMatchSetting}
            onChange={handleMatchSettingChange}
            disabled={isViewMode}
          />

          <MatchFormFields
            form={form}
            onSubmit={handleSubmit}
            onFieldsChange={handleFormChange}
            onReset={handleReset}
            isSubmitting={isSubmitting}
            isFormValid={isFormValid}
            isViewMode={isViewMode}
            isEditMode={isEditMode}
          />
        </div>
      </Card>
    </div>
  );
};

export default CreateMatchForm;
