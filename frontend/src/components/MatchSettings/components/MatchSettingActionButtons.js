import React from 'react';
import { Button, Space, Tooltip, Popconfirm } from 'antd';
import {
    EyeOutlined,
    EditOutlined,
    CopyOutlined,
    DeleteOutlined,
    CheckCircleOutlined
} from '@ant-design/icons';

const MatchSettingActionButtons = ({
    matchSetting,
    onView,
    onClone,
    onEdit,
    onDelete,
    onPublish,
}) => {
    const isDraft = matchSetting.status === 'Draft';

    return (
        <Space size="small">
            {/* View Details */}
            <Tooltip title="View Details">
                <Button
                    id={`btn-view-${matchSetting.id}`}
                    icon={<EyeOutlined />}
                    onClick={() => onView(matchSetting)}
                />
            </Tooltip>

            {/* Clone */}
            <Tooltip title="Clone Setting">
                <Popconfirm
                    title="Clone Match Setting"
                    description="Are you sure you want to clone this match setting?"
                    onConfirm={() => onClone(matchSetting.id)}
                    okText="Yes"
                    cancelText="No"
                >
                    <Button
                        id={`btn-clone-${matchSetting.id}`}
                        icon={<CopyOutlined />}
                        style={{ color: 'rgba(0, 0, 0, 0.88)' }}
                    />
                </Popconfirm>
            </Tooltip>

            {/* Edit */}
            <Tooltip title="Edit Setting">
                <Button
                    id={`btn-edit-${matchSetting.id}`}
                    icon={<EditOutlined />}
                    onClick={() => onEdit(matchSetting)}
                    style={{ color: '#1890ff', borderColor: '#1890ff' }}
                />
            </Tooltip>

            {/* Publish (only for drafts) */}
            {isDraft && (
                <Tooltip title="Publish Setting">
                    <Popconfirm
                        title="Publish Match Setting"
                        description="This will validate and publish the match setting. Continue?"
                        onConfirm={() => onPublish(matchSetting.id)}
                        okText="Yes"
                        cancelText="No"
                    >
                        <Button
                            id={`btn-publish-${matchSetting.id}`}
                            icon={<CheckCircleOutlined />}
                            style={{ color: '#52c41a', borderColor: '#52c41a' }}
                        />
                    </Popconfirm>
                </Tooltip>
            )}

            {/* Delete */}
            <Popconfirm
                title="Delete Match Setting"
                description="Are you sure you want to delete this match setting?"
                onConfirm={() => onDelete(matchSetting.id)}
                okText="Yes"
                cancelText="No"
                okButtonProps={{ danger: true }}
            >
                <Tooltip title="Delete Setting">
                    <Button
                        id={`btn-delete-${matchSetting.id}`}
                        danger
                        icon={<DeleteOutlined />}
                    />
                </Tooltip>
            </Popconfirm>
        </Space>
    );
};

export default MatchSettingActionButtons;
