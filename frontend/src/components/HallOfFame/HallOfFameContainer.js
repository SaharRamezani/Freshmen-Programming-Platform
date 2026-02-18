import React, { useState, useEffect, useRef, useCallback } from 'react';
import { message } from 'antd';
import { getLeaderboard } from '../../services/leaderboardService';
import HallOfFameView from './HallOfFameView';
import './HallOfFame.css';
import { getUserProfile } from '../../services/userService';

/**
 * HallOfFameContainer
 * 
 * Logic and state management for the Hall of Fame feature.
 */

const DEFAULT_PAGE_SIZE = 10;

const HallOfFameContainer = () => {
    const [leaderboardData, setLeaderboardData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalStudents, setTotalStudents] = useState(0);
    const [totalPages, setTotalPages] = useState(0);
    const [currentUserRank, setCurrentUserRank] = useState(null);
    const [currentStudentId, setCurrentStudentId] = useState(null);
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const pageSize = DEFAULT_PAGE_SIZE;

    const tableRef = useRef(null);

    // Fetch leaderboard data
    const fetchLeaderboard = useCallback(async (page) => {
        setLoading(true);
        try {
            const data = await getLeaderboard(page, pageSize, currentStudentId);
            setLeaderboardData(data.leaderboard);
            setTotalStudents(data.total_students);
            setTotalPages(data.total_pages);
            console.log(data);
            setCurrentUserRank(data.current_user_rank);
            const dataProf = await getUserProfile();
            setCurrentStudentId(dataProf.user_id);
        } catch (error) {
            message.error(`Failed to load leaderboard: ${error.message}`);
        } finally {
            setLoading(false);
        }
    }, [currentStudentId, pageSize]);

    useEffect(() => {

        fetchLeaderboard(currentPage);
    }, [currentPage, fetchLeaderboard]);

    // Handle page change
    const handlePageChange = (page) => {
        setCurrentPage(page);
    };

    // Scroll to current user's position based on their student_id/name
    const handleWhereAmI = () => {
        if (!currentUserRank) {
            message.info('Your rank information is not available');
            return;
        }

        // Use the position (1-based index) instead of rank to handle tied ranks correctly
        const userPosition = currentUserRank.position;
        if (!userPosition) {
            message.info('Your position information is not available');
            return;
        }

        const userPage = Math.ceil(userPosition / pageSize);

        if (userPage !== currentPage) {
            setCurrentPage(userPage);
            message.info(`Found you! Navigating to page ${userPage}...`);
        }

        // Scroll to the table and highlight the row after a short delay to allow re-render
        setTimeout(() => {
            if (tableRef.current) {
                tableRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

            // Flash-highlight the current user's row
            const userRow = tableRef.current?.querySelector(
                `tr[data-row-key="${currentStudentId}"]`
            );
            if (userRow) {
                userRow.classList.add('highlight-flash');
                setTimeout(() => userRow.classList.remove('highlight-flash'), 2000);
            }
        }, userPage !== currentPage ? 500 : 100);
    };

    // Render rank with medal icons for top 3, but only if score > 0
    const renderRank = (rank, record) => {
        if (record && record.score > 0) {
            if (rank === 1) return <span className="medal gold" data-testid="medal-gold">🥇</span>;
            if (rank === 2) return <span className="medal silver" data-testid="medal-silver">🥈</span>;
            if (rank === 3) return <span className="medal bronze" data-testid="medal-bronze">🥉</span>;
        }
        return <span className="rank-number" data-testid="rank-number">{rank}</span>;
    };

    // Table columns configuration
    const columns = [
        {
            title: 'Rank',
            dataIndex: 'rank',
            key: 'rank',
            width: 100,
            align: 'center',
            render: renderRank,
        },
        {
            title: 'Player',
            dataIndex: 'username',
            key: 'username',
            render: (text) => (
                <div className="player-info" data-testid="player-info">
                    <span className="player-name" data-testid="player-name">{text}</span>
                </div>
            ),
        },
        {
            title: 'Score',
            dataIndex: 'score',
            key: 'score',
            width: 150,
            align: 'right',
            render: (score) => <span className="hall-of-fame-score" data-testid="score-value">{score.toFixed(2)}</span>,
        },
    ];

    const pagination = {
        current: currentPage,
        pageSize: pageSize,
        total: totalStudents,
        onChange: handlePageChange,
        showSizeChanger: false,
        showTotal: (total) => `Total ${total} students`,
    };

    const toggleDrawer = () => {
        setIsDrawerOpen(!isDrawerOpen);
    };

    return (
        <HallOfFameView
            columns={columns}
            leaderboardData={leaderboardData}
            loading={loading}
            pagination={pagination}
            currentStudentId={currentStudentId}
            currentUserRank={currentUserRank}
            handleWhereAmI={handleWhereAmI}
            tableRef={tableRef}
            isDrawerOpen={isDrawerOpen}
            toggleDrawer={toggleDrawer}
        />
    );
};

export default HallOfFameContainer;
