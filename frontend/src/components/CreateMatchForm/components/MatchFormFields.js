import React from 'react';
import { Form, Select, InputNumber, Button, Space, Input, Tooltip } from 'antd';
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';
import {
  DEFAULT_CREATOR_ID,
  DEFAULT_REVIEW_NUMBER,
  MIN_REVIEWERS,
  MAX_REVIEWERS,
  MIN_TITLE_LENGTH,
  MAX_TITLE_LENGTH,
  MIN_DURATION,
  DIFFICULTY_LEVELS
} from '../constants';

const { Option } = Select;

/**
 * Shared validator function for duration fields
 * Validates that the value is a valid positive integer meeting minimum requirements
 * Note: Empty values are handled by the 'required' rule, so this validator skips them
 * 
 * @param {*} _ - Rule object (unused)
 * @param {*} value - Field value to validate
 * @returns {Promise} Resolves if valid, rejects with error message if invalid
 */
const durationValidator = (_, value) => {
  // Let the 'required' rule handle empty values
  if (!value) {
    return Promise.resolve();
  }
  const num = Number(value);
  if (isNaN(num)) {
    return Promise.reject(new Error('Please enter a valid number'));
  }
  if (!Number.isInteger(num)) {
    return Promise.reject(new Error('Duration must be a whole number'));
  }
  if (num < MIN_DURATION) {
    return Promise.reject(new Error(`Duration must be at least ${MIN_DURATION} minute`));
  }
  return Promise.resolve();
};

/**
 * MatchFormFields - Component containing all form input fields for match creation
 * Handles rendering of form fields with validation rules
 * 
 * @param {Object} props
 * @param {Object} props.form - Ant Design form instance
 * @param {Function} props.onSubmit - Form submission handler
 * @param {Function} props.onFieldsChange - Handler for form field changes
 * @param {Function} props.onReset - Form reset handler
 * @param {boolean} props.isSubmitting - Submit loading state
 * @param {boolean} props.isFormValid - Form validation state
 * @returns {JSX.Element} Form fields component
 */
const MatchFormFields = ({
  form,
  onSubmit,
  onFieldsChange,
  onReset,
  isSubmitting,
  isFormValid,
  isViewMode = false,
  isEditMode = false,
}) => {
  return (
    <div className="form-fields-column">
      <Form
        form={form}
        layout="vertical"
        onFinish={onSubmit}
        onFieldsChange={onFieldsChange}
        initialValues={{
          review_number: DEFAULT_REVIEW_NUMBER,
          creator_id: DEFAULT_CREATOR_ID,
        }}
      >
        {/* Match Title */}
        <Form.Item
          label="Match Title"
          name="title"
          rules={[
            {
              required: true,
              message: 'Please enter a match title',
            },
            {
              min: MIN_TITLE_LENGTH,
              message: `Title must be at least ${MIN_TITLE_LENGTH} characters`,
            },
            {
              max: MAX_TITLE_LENGTH,
              message: `Title must not exceed ${MAX_TITLE_LENGTH} characters`,
            },
          ]}
        >
          <Input
            id="title-input"
            placeholder="Enter a descriptive title for this match"
            size="large"
            showCount
            maxLength={MAX_TITLE_LENGTH}
            disabled={isViewMode}
          />
        </Form.Item>

        {/* Hidden Creator ID */}
        <Form.Item name="creator_id" hidden>
          <InputNumber />
        </Form.Item>

        {/* Difficulty Level */}
        <Form.Item
          label="Difficulty Level"
          name="difficulty_level"
          rules={[
            {
              required: true,
              message: 'Please select a difficulty level',
            },
          ]}
        >
          <Select
            id="difficulty-select"
            placeholder="Select difficulty level"
            size="large"
            disabled={isViewMode}
          >
            {DIFFICULTY_LEVELS.map(level => (
              <Option key={level.value} value={level.value}>
                {level.label}
              </Option>
            ))}
          </Select>
        </Form.Item>

        {/* Review Number */}
        <Form.Item
          label="Review Number"
          name="review_number"
          rules={[
            {
              required: true,
              message: 'Please enter the number of reviewers',
            },
            {
              type: 'number',
              min: MIN_REVIEWERS,
              max: MAX_REVIEWERS,
              message: `Reviewers must be between ${MIN_REVIEWERS} and ${MAX_REVIEWERS}`,
            },
          ]}
        >
          <InputNumber
            id="reviewers-input"
            style={{ width: '100%' }}
            size="large"
            placeholder={`Enter number of reviewers (default: ${DEFAULT_REVIEW_NUMBER})`}
            disabled={isViewMode}
          />
        </Form.Item>

        {/* Duration Phase 1 */}
        <Form.Item
          label="Estimated Duration Phase 1 (minutes)"
          name="duration_phase1"
          rules={[
            {
              required: true,
              message: 'Please enter the first phase duration',
            },
            {
              validator: durationValidator,
            },
          ]}
        >
          <Input
            id="first-phase-duration-input"
            size="large"
            placeholder="Enter Duration in minutes"
            disabled={isViewMode}
          />
        </Form.Item>

        {/* Duration Phase 2 */}
        <Form.Item
          label="Estimated Duration Phase 2 (minutes)"
          name="duration_phase2"
          rules={[
            {
              required: true,
              message: 'Please enter the second phase duration',
            },
            {
              validator: durationValidator,
            },
          ]}
        >
          <Input
            id="second-phase-duration-input"
            size="large"
            placeholder="Enter duration in minutes"
            disabled={isViewMode}
          />
        </Form.Item>

        {/* Action Buttons */}
        {!isViewMode && (
          <Form.Item>
            <Space size="middle">
              <Button
                id="save-match-button"
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={isSubmitting}
                size="large"
                disabled={!isFormValid || isSubmitting}
              >
                {isEditMode ? 'Update Match' : 'Save Match'}
              </Button>
              {!isEditMode && (
                <Tooltip title="Clear all form fields and start over">
                  <Button
                    id="reset-button"
                    danger
                    icon={<ReloadOutlined />}
                    onClick={onReset}
                    size="large"
                    disabled={isSubmitting}
                  >
                    Reset
                  </Button>
                </Tooltip>
              )}
            </Space>
          </Form.Item>
        )}
      </Form>
    </div>
  );
};

export default MatchFormFields;

