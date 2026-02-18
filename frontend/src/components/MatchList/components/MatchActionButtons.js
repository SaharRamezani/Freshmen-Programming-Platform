import React from 'react';
import { Button, Space, Tooltip, Popconfirm } from 'antd';
import {
  EyeOutlined,
  EditOutlined,
  CopyOutlined,
  DeleteOutlined,
} from '@ant-design/icons';

/**
 * MatchActionButtons - Action buttons for each match row
 * Provides view, clone, edit, and delete actions with confirmations
 */
const MatchActionButtons = ({
  match,
  onView,
  onClone,
  onEdit,
  onDelete,
}) => {
  return (
    <Space size="small">
      {/* View Details */}
      <Tooltip title="View Match">
        <Button
          id={`btn-view-match-${match.match_id}`}
          icon={<EyeOutlined />}
          onClick={() => onView(match)}
        />
      </Tooltip>

      {/* Clone */}
      <Tooltip title="Clone Match">
        <Popconfirm
          title="Clone Match"
          description="Are you sure you want to clone this match?"
          onConfirm={() => onClone(match.match_id)}
          okText="Yes"
          cancelText="No"
        >
          <Button
            id={`btn-clone-match-${match.match_id}`}
            icon={<CopyOutlined />}
            style={{ color: 'rgba(0, 0, 0, 0.88)' }}
          />
        </Popconfirm>
      </Tooltip>

      {/* Edit */}
      <Tooltip title="Edit Match">
        <Button
          id={`btn-edit-match-${match.match_id}`}
          icon={<EditOutlined />}
          onClick={() => onEdit(match)}
          style={{ color: '#1890ff', borderColor: '#1890ff' }}
        />
      </Tooltip>

      {/* Delete */}
      <Popconfirm
        title="Delete Match"
        description="Are you sure you want to delete this match?"
        onConfirm={() => onDelete(match.match_id)}
        okText="Yes"
        cancelText="No"
        okButtonProps={{ danger: true }}
      >
        <Tooltip title="Delete Match">
          <Button
            id={`btn-delete-match-${match.match_id}`}
            danger
            icon={<DeleteOutlined />}
          />
        </Tooltip>
      </Popconfirm>
    </Space>
  );
};

export default MatchActionButtons;
