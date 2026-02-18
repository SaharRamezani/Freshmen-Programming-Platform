import React from 'react';
import { Select, Button, Flex, Collapse, Typography, Table, Tag } from 'antd';
import { CaretRightOutlined } from '@ant-design/icons';
import Editor from '@monaco-editor/react';
import DodgeTheBugsGame from './DodgeTheBugsGame';

const { Option } = Select;
const { Text } = Typography;

const EditorPanel = ({
    language,
    setLanguage,
    code,
    setCode,
    timeLeft,
    handleRunPublicTests,
    handleRunCustomTests,
    publicTestsCount,
    showOutput,
    setShowOutput,
    runResults
}) => {
    const [showMiniGame, setShowMiniGame] = React.useState(false);

    // Close mini-game when timer runs out
    React.useEffect(() => {
        if (timeLeft === 0) {
            setShowMiniGame(false);
        }
    }, [timeLeft]);

    // Mapping runResults to Collapse items
    const collapseItems = [
        {
            key: '1',
            label: 'Execution Output Windows / Test Results',
            children: runResults && (
                <div className="run-results-content">
                    <div className="run-results-header" style={{ marginBottom: 16 }}>
                        Test Results: <span className="run-result-success">{runResults.passed} Passed</span>, <span className="run-result-failure">{runResults.failed} Failed</span>
                    </div>

                    {runResults.testResults.length > 0 ? (
                        <Table
                            dataSource={runResults.testResults}
                            rowKey="test_id"
                            pagination={false}
                            size="small"
                            columns={[
                                {
                                    title: 'Test Case',
                                    dataIndex: 'test_id',
                                    key: 'test_id',
                                    render: (id) => `Test ${id}`,
                                    width: 80,
                                },
                                {
                                    title: 'Status',
                                    dataIndex: 'status',
                                    key: 'status',
                                    width: 100,
                                    render: (status) => {
                                        let color = status === 'pass' ? 'success' : 'error';
                                        let text = status === 'pass' ? 'Passed' : 'Failed';
                                        if (status === 'timeout') { color = 'warning'; text = 'Timeout'; }
                                        if (status === 'runtime_error') { color = 'error'; text = 'Runtime Error'; }
                                        return <Tag color={color}>{text}</Tag>;
                                    }
                                },
                                {
                                    title: 'Expected Output',
                                    dataIndex: 'expected_output',
                                    key: 'expected_output',
                                    render: (text) => <Text code>{text || 'N/A'}</Text>
                                },
                                {
                                    title: 'Received Output',
                                    dataIndex: 'actual_output',
                                    key: 'actual_output',
                                    render: (text, record) => (
                                        <Text
                                            style={{
                                                whiteSpace: 'pre-wrap',
                                                color: record.status !== 'pass' ? '#ff4d4f' : 'inherit'
                                            }}
                                        >
                                            {text || 'N/A'}
                                        </Text>
                                    )
                                }
                            ]}
                        />
                    ) : (
                        // Fallback for compilation errors or empty results
                        runResults.errors.map((err, i) => (
                            <pre key={i} className="run-result-error-msg" style={{
                                margin: '8px 0',
                                padding: '8px 12px',
                                backgroundColor: '#fff1f0',
                                border: '1px solid #ffa39e',
                                borderRadius: '4px',
                                fontSize: '13px',
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'monospace'
                            }}>{err}</pre>
                        ))
                    )}
                </div>
            )
        }
    ];

    return (
        <Flex vertical gap="middle" className="editor-panel-container">
            <Flex justify="space-between" align="center">
                <Text strong>Code Editor</Text>
                <div className="editor-toolbar">
                    <span className="editor-toolbar-label">Language:</span>
                    <Select
                        value={language}
                        onChange={setLanguage}
                        className="editor-select"
                    >
                        <Option value="C++">C++</Option>
                    </Select>
                </div>
            </Flex>

            {/* Wrapper with 'ace_content' class to satisfy test selector */}
            <div className="ace_content editor-content-wrapper">
                <Editor
                    height="100%"
                    defaultLanguage="C++"
                    value={code}
                    onChange={(value) => setCode(value)}
                    options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        padding: { top: 16 }
                    }}
                />
            </div>

            <Flex gap="middle">
                <Button
                    block
                    onClick={handleRunPublicTests}
                    disabled={timeLeft === 0}
                    size="large"
                >
                    Run Public Tests ({publicTestsCount})
                </Button>
                <Button
                    type="primary"
                    block
                    size="large"
                    onClick={handleRunCustomTests}
                    disabled={timeLeft === 0}
                >
                    Test My Custom Inputs
                </Button>
                <Button
                    onClick={() => setShowMiniGame(true)}
                    size="large"
                    disabled={timeLeft === 0}
                >
                   Open mini-game
                </Button>
            </Flex>

            <Collapse
                items={collapseItems}
                activeKey={showOutput ? ['1'] : []}
                onChange={() => setShowOutput(!showOutput)}
                expandIcon={({ isActive }) => <CaretRightOutlined rotate={isActive ? 90 : 0} />}
                size="small"
                className="results-collapse"
            />
            
            <DodgeTheBugsGame visible={showMiniGame} onClose={() => setShowMiniGame(false)} />
        </Flex>
    );
};

export default EditorPanel;
