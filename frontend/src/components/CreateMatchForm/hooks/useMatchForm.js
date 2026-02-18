import { useState, useCallback } from 'react';
import { createMatch, getMatch, updateMatch } from '../../../services/matchService';
import { DEFAULT_CREATOR_ID, REQUIRED_FIELDS, ERROR_MESSAGES } from '../constants';
import { isNetworkError } from '../../../utils/errorUtils';
import { getUserProfile } from '../../../services/userService';

/**
 * Custom hook for managing match form state and submission
 * Handles form validation, submission, and reset functionality
 * 
 * @param {Object} form - Ant Design form instance
 * @param {Function} showAlert - Function to display alerts
 * @returns {Object} Form state and handlers
 */
export const useMatchForm = (form, showAlert, isEditMode = false, matchId = null) => {
  const [selectedMatchSetting, setSelectedMatchSetting] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFormValid, setIsFormValid] = useState(false);

  /**
   * Validates the form by checking field errors and completeness
   * @param {number|null} matchSettingValue - Currently selected match setting ID
   */
  const validateForm = (matchSettingValue) => {
    const fieldErrors = form.getFieldsError(REQUIRED_FIELDS);
    const hasErrors = fieldErrors.some(field => field.errors.length > 0);

    const fieldValues = form.getFieldsValue(REQUIRED_FIELDS);
    const allFieldsFilled = REQUIRED_FIELDS.every(field => {
      const value = fieldValues[field];
      return value !== undefined && value !== null && value !== '';
    });

    setIsFormValid(!hasErrors && allFieldsFilled && matchSettingValue !== null);
  };

  /**
   * Handles form field changes and triggers validation
   */
  const handleFormChange = () => {
    validateForm(selectedMatchSetting);
  };

  /**
   * Handles match setting selection change
   * @param {Event} e - Radio button change event
   */
  const handleMatchSettingChange = (e) => {
    const newValue = e.target.value;
    setSelectedMatchSetting(newValue);
    validateForm(newValue);
  };

  /**
   * Handles form submission
   * @param {Object} values - Form values from Ant Design form
   */
  const handleSubmit = async (values) => {
    if (!selectedMatchSetting) {
      showAlert('error', ERROR_MESSAGES.NO_MATCH_SETTING);
      return;
    }

    setIsSubmitting(true);
    const data = await getUserProfile();
    try {
      const matchData = {
        title: values.title,
        match_set_id: selectedMatchSetting,
        creator_id: data.user_id,
        difficulty_level: values.difficulty_level,
        review_number: values.review_number,
        duration_phase1: values.duration_phase1,
        duration_phase2: values.duration_phase2,
      };

      if (isEditMode && matchId) {
        const updatedMatch = await updateMatch(matchId, matchData);
        showAlert('success', `Match "${updatedMatch.title}" has been updated successfully!`);
      } else {
        const createdMatch = await createMatch(matchData);
        showAlert('success', `Match "${createdMatch.title}" has been created successfully!`);
        form.resetFields();
        setSelectedMatchSetting(null);
        setIsFormValid(false);
      }

    } catch (error) {
      let errorMessage;

      if (isNetworkError(error)) {
        errorMessage = 'Unable to connect to server. Please check your connection and ensure the backend is running.';
      } else if (error.message) {
        errorMessage = error.message;
      } else {
        errorMessage = ERROR_MESSAGES.CREATE_MATCH_ERROR;
      }

      showAlert('error', errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Resets the form to initial state
   * @param {Function} resetAlert - Function to reset alert state
   */
  const handleReset = (resetAlert) => {
    form.resetFields();
    setSelectedMatchSetting(null);
    setIsFormValid(false);
    resetAlert();
  };

  /**
   * Loads an existing match for edit/view mode
   */
  const loadMatch = useCallback(async (id) => {
    try {
      const match = await getMatch(id);
      form.setFieldsValue({
        title: match.title,
        difficulty_level: match.difficulty_level,
        review_number: match.review_number,
        duration_phase1: String(match.duration_phase1),
        duration_phase2: String(match.duration_phase2),
      });
      setSelectedMatchSetting(match.match_set_id);
      setIsFormValid(true);
    } catch (error) {
      showAlert('error', 'Failed to load match data.');
    }
  }, [form, showAlert]);

  return {
    selectedMatchSetting,
    isSubmitting,
    isFormValid,
    handleFormChange,
    handleMatchSettingChange,
    handleSubmit,
    handleReset,
    loadMatch,
  };
};

