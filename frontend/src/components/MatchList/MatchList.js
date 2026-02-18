import React, { useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Table, Typography, Tooltip, Input, Tag } from "antd";
import { ArrowLeftOutlined, ClockCircleOutlined } from "@ant-design/icons";
import { useMatches } from "./hooks/useMatches";
import MatchActionButtons from "./components/MatchActionButtons";
import PopupAlert from "../common/PopupAlert";
import "./MatchList.css";

const { Title, Text } = Typography;

const DIFFICULTY_LABELS = {
  1: { label: "Easy", color: "success" },
  2: { label: "Medium", color: "warning" },
  3: { label: "Hard", color: "error" },
};

/**
 * MatchList - Component for displaying and managing matches
 * Features: browse, view, clone, edit, delete
 */
const MatchList = () => {
  const navigate = useNavigate();

  const [searchTerm, setSearchTerm] = useState("");
  const [sortOrder, setSortOrder] = useState({ field: "match_id", order: "descend" });

  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const showAlert = useCallback((type, msg) => {
    if (type === "error") setError(msg);
    else if (type === "success") setSuccess(msg);
  }, []);

  const showSuccess = useCallback((msg) => {
    setSuccess(msg);
  }, []);

  const {
    items,
    loading,
    deleteMatch,
    cloneMatch,
  } = useMatches(showAlert, showSuccess);

  // Navigate to CreateMatchForm in view mode
  const handleView = useCallback((match) => {
    navigate(`/matches/${match.match_id}/view`);
  }, [navigate]);

  // Navigate to CreateMatchForm in edit mode
  const handleEdit = useCallback((match) => {
    navigate(`/matches/${match.match_id}/edit`);
  }, [navigate]);

  const handleTableChange = (_pagination, _filters, sorter) => {
    if (sorter.order) {
      setSortOrder({ field: sorter.field, order: sorter.order });
    } else {
      setSortOrder({ field: "match_id", order: "descend" });
    }
  };

  const toggleCreatedSort = () => {
    const isNewest = sortOrder.field === "match_id" && sortOrder.order === "descend";
    setSortOrder({
      field: "match_id",
      order: isNewest ? "ascend" : "descend",
    });
  };

  const processedItems = useMemo(() => {
    let result = items.filter((item) =>
      item.title.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (sortOrder.field && sortOrder.order) {
      result.sort((a, b) => {
        let valA = a[sortOrder.field];
        let valB = b[sortOrder.field];
        if (typeof valA === "string") valA = valA.toLowerCase();
        if (typeof valB === "string") valB = valB.toLowerCase();
        if (valA < valB) return sortOrder.order === "ascend" ? -1 : 1;
        if (valA > valB) return sortOrder.order === "ascend" ? 1 : -1;
        return 0;
      });
    }
    return result;
  }, [items, searchTerm, sortOrder]);

  const columns = [
    {
      title: "Title",
      dataIndex: "title",
      key: "title",
      sorter: true,
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: "Difficulty",
      dataIndex: "difficulty_level",
      key: "difficulty_level",
      width: 120,
      render: (level) => {
        const info = DIFFICULTY_LABELS[level] || { label: `Level ${level}`, color: "default" };
        return <Tag color={info.color}>{info.label}</Tag>;
      },
    },
    {
      title: "Phase 1 (min)",
      dataIndex: "duration_phase1",
      key: "duration_phase1",
      width: 120,
      align: "center",
    },
    {
      title: "Phase 2 (min)",
      dataIndex: "duration_phase2",
      key: "duration_phase2",
      width: 120,
      align: "center",
    },
    {
      title: "Actions",
      key: "actions",
      align: "right",
      width: 200,
      render: (_, record) => (
        <MatchActionButtons
          match={record}
          onView={handleView}
          onClone={cloneMatch}
          onEdit={handleEdit}
          onDelete={deleteMatch}
        />
      ),
    },
  ];

  return (
    <div className="match-list-container">
      <Card className="match-list-card">
        <div className="page-header">
          <Tooltip title="Back to Home">
            <Button
              id="back-to-home-button"
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate("/home")}
              shape="circle"
              size="large"
            />
          </Tooltip>
          <Title level={2} className="page-title" id="page-title">
            Matches
          </Title>
          <span />
        </div>

        <div className="subheader">
          <Text type="secondary">
            Browse, clone, edit, delete, or view your created matches.
          </Text>
        </div>

        {error && (
          <PopupAlert
            message={error}
            type="error"
            onClose={() => setError(null)}
          />
        )}

        {success && (
          <PopupAlert
            message={success}
            type="success"
            onClose={() => setSuccess(null)}
          />
        )}

        <div className="filter-bar">
          <div className="filter-controls">
            <div className="left-filters">
              <Input
                placeholder="Search by title..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ width: 220 }}
                allowClear
              />
            </div>

            <div className="right-filters">
              <Tooltip
                title={
                  sortOrder.field === "match_id" && sortOrder.order === "descend"
                    ? "Sort by Oldest First"
                    : "Sort by Latest First"
                }
              >
                <Button
                  icon={<ClockCircleOutlined />}
                  onClick={toggleCreatedSort}
                  type={sortOrder.field === "match_id" ? "primary" : "default"}
                  ghost={sortOrder.field === "match_id"}
                  className="sort-button"
                >
                  {sortOrder.field === "match_id" && sortOrder.order === "descend"
                    ? " Latest"
                    : " Oldest"}
                </Button>
              </Tooltip>
            </div>
          </div>
        </div>

        <Table
          dataSource={processedItems}
          columns={columns}
          loading={loading}
          pagination={{ pageSize: 8, showSizeChanger: false }}
          onChange={handleTableChange}
          rowKey="match_id"
          className="match-list-table"
          locale={{ emptyText: "No matches found." }}
        />
      </Card>
    </div>
  );
};

export default MatchList;
