import React, { useEffect } from 'react';
import {
    Modal,
    Form,
    Input,
    Button,
    Select,
    Typography,
    Card,
    Space,
    Divider
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import './MatchSettingEditModal.css';

const { TextArea } = Input;
const { Title, Text } = Typography;
const { Option } = Select;

const MatchSettingEditModal = ({
    visible,
    matchSetting,
    loading,
    onSave,
    onCancel,
}) => {
    const [form] = Form.useForm();

    // Initialize form with match setting data when modal opens
    useEffect(() => {
        if (visible && matchSetting) {
            form.setFieldsValue({
                title: matchSetting.name,
                description: matchSetting.description,
                reference_solution: matchSetting.reference_solution,
                student_code: matchSetting.student_code || '',
                function_name: matchSetting.function_name || '',
                function_type: matchSetting.function_type || 'output',
                function_inputs: matchSetting.function_inputs || '',
                language: matchSetting.language || 'cpp',
                tests: matchSetting.tests?.map(t => ({
                    test_in: t.test_in || '',
                    test_out: t.test_out,
                    scope: t.scope || 'public',
                })) || [],
            });
        }
    }, [visible, matchSetting, form]);

    // Handle form submission
    const handleSubmit = async () => {
        try {
            const values = await form.validateFields();
            onSave(matchSetting.id, values);
        } catch (err) {
            console.error('Form validation failed:', err);
        }
    };

    // Reset form when modal closes
    const handleCancel = () => {
        form.resetFields();
        onCancel();
    };

    return (
        <Modal
            title={<Title level={4} style={{ margin: 0 }}>Edit Match Setting</Title>}
            open={visible}
            onCancel={handleCancel}
            width={800}
            footer={[
                <Button key="cancel" onClick={handleCancel}>
                    Cancel
                </Button>,
                <Button
                    key="save"
                    type="primary"
                    onClick={handleSubmit}
                    loading={loading}
                >
                    Save Changes
                </Button>,
            ]}
            destroyOnClose
            className="match-setting-edit-modal"
        >
            <Form
                form={form}
                layout="vertical"
                className="match-setting-form"
            >
                {/* Basic Information */}
                <Form.Item
                    name="title"
                    label="Title"
                    rules={[
                        { required: true, message: 'Please enter a title' },
                        { min: 3, message: 'Title must be at least 3 characters' },
                    ]}
                >
                    <Input placeholder="Enter match setting title" />
                </Form.Item>

                <Form.Item
                    name="description"
                    label="Description"
                    rules={[
                        { required: true, message: 'Please enter a description' },
                    ]}
                >
                    <TextArea
                        rows={3}
                        placeholder="Enter description"
                    />
                </Form.Item>

                <Divider orientation="left">Code</Divider>

                <Form.Item
                    name="reference_solution"
                    label="Reference Solution"
                    rules={[
                        { required: true, message: 'Please enter the reference solution' },
                    ]}
                >
                    <TextArea
                        rows={8}
                        placeholder="Enter the complete reference solution code"
                        style={{ fontFamily: 'monospace' }}
                    />
                </Form.Item>

                <Form.Item
                    name="student_code"
                    label="Student Code Template (Optional)"
                >
                    <TextArea
                        rows={4}
                        placeholder="Enter template code for students (optional)"
                        style={{ fontFamily: 'monospace' }}
                    />
                </Form.Item>

                <Space style={{ width: '100%' }} size="large">
                    <Form.Item
                        name="language"
                        label="Language"
                        style={{ width: 150 }}
                    >
                        <Select>
                            <Option value="cpp">C++</Option>
                            <Option value="python">Python</Option>
                            <Option value="java">Java</Option>
                        </Select>
                    </Form.Item>

                    <Form.Item
                        name="function_name"
                        label="Function Name (Optional)"
                    >
                        <Input placeholder="e.g., solve" />
                    </Form.Item>

                    <Form.Item
                        name="function_type"
                        label="Function Type"
                        style={{ width: 150 }}
                    >
                        <Select>
                            <Option value="output">Output</Option>
                            <Option value="return">Return</Option>
                        </Select>
                    </Form.Item>
                </Space>

                <Divider orientation="left">Test Cases</Divider>

                <Form.List name="tests">
                    {(fields, { add, remove }) => (
                        <>
                            {fields.map(({ key, name, ...restField }) => (
                                <Card
                                    key={key}
                                    size="small"
                                    style={{ marginBottom: 12 }}
                                    title={<Text strong>Test Case {name + 1}</Text>}
                                    extra={
                                        <Button
                                            type="text"
                                            danger
                                            icon={<DeleteOutlined />}
                                            onClick={() => remove(name)}
                                        />
                                    }
                                >
                                    <Space style={{ width: '100%', display: 'flex' }} align="start">
                                        <Form.Item
                                            {...restField}
                                            name={[name, 'test_in']}
                                            label="Input"
                                            style={{ flex: 1, marginBottom: 0 }}
                                        >
                                            <TextArea
                                                rows={2}
                                                placeholder="Test input"
                                                style={{ fontFamily: 'monospace' }}
                                            />
                                        </Form.Item>

                                        <Form.Item
                                            {...restField}
                                            name={[name, 'test_out']}
                                            label="Expected Output"
                                            rules={[{ required: true, message: 'Required' }]}
                                            style={{ flex: 1, marginBottom: 0 }}
                                        >
                                            <TextArea
                                                rows={2}
                                                placeholder="Expected output"
                                                style={{ fontFamily: 'monospace' }}
                                            />
                                        </Form.Item>

                                        <Form.Item
                                            {...restField}
                                            name={[name, 'scope']}
                                            label="Scope"
                                            style={{ width: 120, marginBottom: 0 }}
                                        >
                                            <Select>
                                                <Option value="public">Public</Option>
                                                <Option value="private">Private</Option>
                                            </Select>
                                        </Form.Item>
                                    </Space>
                                </Card>
                            ))}

                            <Button
                                type="dashed"
                                onClick={() => add({ test_in: '', test_out: '', scope: 'public' })}
                                block
                                icon={<PlusOutlined />}
                            >
                                Add Test Case
                            </Button>
                        </>
                    )}
                </Form.List>
            </Form>
        </Modal>
    );
};

export default MatchSettingEditModal;
