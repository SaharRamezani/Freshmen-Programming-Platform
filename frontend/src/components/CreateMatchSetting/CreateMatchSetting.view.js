import { ArrowLeftOutlined } from '@ant-design/icons';
import { Button, Tooltip } from 'antd';
import MatchDetails from './components/MatchDetails';
import TestCases from './components/TestCases';
import ProfessorConfig from './components/ProfessorConfig';
import PopupAlert from '../common/PopupAlert';
import './CreateMatchSetting.css';

const CreateMatchSettingView = ({
    isEditMode,
    formData,
    publicTests,
    privateTests,
    matchDetailsExpanded,
    configExpanded,
    validationResults,
    alert,
    isSubmitting,
    isTrying,
    inputsList,
    handlers,
}) => {
    const {
        setMatchDetailsExpanded,
        setConfigExpanded,
        handleInputChange,
        handleTestChange,
        handleDeleteTest,
        handleAddPublicTest,
        handleAddPrivateTest,
        handleInputChangeRow,
        handleRemoveInputRow,
        handleAddInputRow,
        generateBoilerplate,
        handleTry,
        handlePublish,
        handleSaveDraft,
        handleDismissAlert,
        onBack,
    } = handlers;

    return (
        <div className="create-match-setting-container">
            {/* Alert Popup */}
            {alert && (
                <PopupAlert
                    message={alert.message}
                    type={alert.type}
                    onClose={handleDismissAlert}
                />
            )}

            <div className="create-match-setting-card">
                {/* Header */}
                <div className="page-header">
                    <Tooltip title="Go Back">
                        <Button
                            id="back-to-home-button"
                            icon={<ArrowLeftOutlined />}
                            onClick={onBack}
                            shape="circle"
                            size="large"
                        />
                    </Tooltip>
                    <h2>{isEditMode ? 'Edit Match Setting' : 'Create Match Setting'}</h2>
                    <span />
                </div>

                {/* Match Details */}
                <MatchDetails
                    formData={formData}
                    expanded={matchDetailsExpanded}
                    onToggle={() => setMatchDetailsExpanded(!matchDetailsExpanded)}
                    onChange={handleInputChange}
                />

                {/* Test Cases */}
                <TestCases
                    publicTests={publicTests}
                    privateTests={privateTests}
                    onChange={handleTestChange}
                    onDelete={handleDeleteTest}
                    onAddPublic={handleAddPublicTest}
                    onAddPrivate={handleAddPrivateTest}
                />

                {/* Professor Configuration */}
                <ProfessorConfig
                    formData={formData}
                    inputsList={inputsList}
                    expanded={configExpanded}
                    onToggle={() => setConfigExpanded(!configExpanded)}
                    onChange={handleInputChange}
                    onInputChangeRow={handleInputChangeRow}
                    onRemoveInputRow={handleRemoveInputRow}
                    onAddInputRow={handleAddInputRow}
                    onGenerateBoilerplate={generateBoilerplate}
                />

                {/* Validation Results */}
                {validationResults && (() => {
                    const isCompileError = !!validationResults.compilation_error;
                    const hasTests = validationResults.test_results && validationResults.test_results.length > 0;
                    const isWarning = !hasTests && !isCompileError;
                    const passedCount = hasTests ? validationResults.test_results.filter(r => r.passed).length : 0;
                    const totalCount = hasTests ? validationResults.test_results.length : 0;

                    const stateClass = isCompileError ? 'error' : isWarning ? 'warning' : validationResults.success ? 'success' : 'error';

                    return (
                        <div className="validation-results-container">
                            {/* Summary Banner */}
                            <div className={`vr-summary-banner ${stateClass}`}>
                                <div className="vr-summary-icon">
                                    {isCompileError ? '✗' : isWarning ? '⚠' : validationResults.success ? '✓' : '✗'}
                                </div>
                                <div className="vr-summary-text">
                                    <span className="vr-summary-title">{validationResults.message}</span>
                                    {hasTests && (
                                        <span className="vr-summary-count">{passedCount}/{totalCount} tests passed</span>
                                    )}
                                </div>
                            </div>

                            {/* Compilation Error */}
                            {isCompileError && (
                                <div className="vr-compile-error">
                                    <div className="vr-compile-error-label">Compilation Output</div>
                                    <pre className="vr-compile-error-pre">{validationResults.compilation_error}</pre>
                                </div>
                            )}

                            {/* Warning: No test cases */}
                            {isWarning && (
                                <div className="vr-warning-body">
                                    <div className="vr-warning-icon">📋</div>
                                    <div className="vr-warning-content">
                                        <div className="vr-warning-title">No test cases to run</div>
                                        <div className="vr-warning-desc">Your code compiled without errors, but there are no test cases to validate the output. Add public or private test cases above, then try again.</div>
                                    </div>
                                </div>
                            )}

                            {/* Test Result Cards */}
                            {hasTests && (() => {
                                const cols = totalCount <= 4
                                    ? `repeat(${totalCount}, 1fr)`
                                    : 'repeat(auto-fill, minmax(260px, 1fr))';
                                return (
                                    <div className="vr-test-list" style={{ gridTemplateColumns: cols }}>
                                        {validationResults.test_results.map((result, index) => (
                                            <div key={index} className={`vr-test-card ${result.passed ? 'passed' : 'failed'}`}>
                                                <div className="vr-test-header">
                                                    <div className="vr-test-name-group">
                                                        <span className="vr-test-name">Test {index + 1}</span>
                                                        <span className={`vr-scope-tag ${result.scope}`}>
                                                            {result.scope === 'private' ? ' Private' : ' Public'}
                                                        </span>
                                                    </div>
                                                    <span className={`vr-test-badge ${result.passed ? 'passed' : 'failed'}`}>
                                                        {result.passed ? '✓ Passed' : '✗ Failed'}
                                                    </span>
                                                </div>
                                                <div className="vr-test-details">
                                                    <div className="vr-test-field">
                                                        <span className="vr-test-label">Input</span>
                                                        <span className="vr-test-value">{result.test_in || '—'}</span>
                                                    </div>
                                                    <div className="vr-test-field">
                                                        <span className="vr-test-label">Expected</span>
                                                        <span className="vr-test-value">{result.test_out}</span>
                                                    </div>
                                                    <div className={`vr-test-field ${!result.passed ? 'mismatch' : ''}`}>
                                                        <span className="vr-test-label">Got</span>
                                                        <span className="vr-test-value">{result.actual_output}</span>
                                                    </div>
                                                </div>
                                                {result.error && (
                                                    <div className="vr-test-error">{result.error}</div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                );
                            })()}
                        </div>
                    );
                })()}

                {/* Action Buttons */}
                <div className="action-buttons">
                    <button
                        className="btn btn-try"
                        onClick={handleTry}
                        disabled={isTrying || isSubmitting}
                    >
                        {isTrying ? 'Running...' : 'Try'}
                    </button>
                    <button
                        className="btn btn-publish"
                        onClick={handlePublish}
                        disabled={isSubmitting || isTrying}
                    >
                        {isSubmitting ? 'Publishing...' : 'Publish'}
                    </button>
                    <button
                        className="btn btn-draft"
                        onClick={handleSaveDraft}
                        disabled={isSubmitting || isTrying}
                    >
                        {isSubmitting ? 'Saving...' : 'Save as Draft'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CreateMatchSettingView;
