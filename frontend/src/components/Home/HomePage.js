import React from 'react';
import { useNavigate } from "react-router-dom";
import { Typography, message } from "antd";
import {
  PlusOutlined,
  SettingOutlined,
  PlayCircleOutlined,
  UnorderedListOutlined,
  TeamOutlined,
  AppstoreOutlined,
  TrophyOutlined,
  FileAddOutlined,
  SafetyCertificateOutlined,
  ReadOutlined
} from "@ant-design/icons";
import { getToken } from "../../services/authService";
import "./HomePage.css";
import "../common/ActiveGame.css";
import useActiveGame from "../../hooks/useActiveGame";

const { Title, Paragraph } = Typography;

/**
 * Decode the role from the JWT access token stored in localStorage.
 * The JWT payload contains { sub, email, role, exp, iat, type }.
 * Returns the role string or null if the token is missing/invalid.
 */
const getRoleFromToken = () => {
  try {
    const token = getToken();
    if (!token || token === "dev_mode_token") return null;
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.role || null;
  } catch {
    return null;
  }
};

const HomePage = () => {
  const navigate = useNavigate();
  const role = getRoleFromToken();
  const { activeGame, timeLeft } = useActiveGame();

  const bentoItems = [
    // Creation actions first
    {
      id: "create-match-settings",
      title: "Create Match Settings",
      description: "Design new coding problems with test cases and solutions",
      icon: <FileAddOutlined />,
      route: "/match-settings/create",
      accent: "#6366f1",
      roles: ["teacher"]
    },
    // 2. Match Settings (View/Manage)
    {
      id: "match-settings",
      title: "Match Settings",
      description: "Browse and manage all available match settings",
      icon: <SettingOutlined />,
      route: "/match-settings",
      accent: "#10b981",
      roles: ["teacher"]
    },
    // 3. Create New Match
    {
      id: "create-match",
      title: "Create New Match",
      description: "Set up a new match with settings, difficulty, and duration",
      icon: <PlusOutlined />,
      route: "/create-match",
      accent: "#3b82f6",
      roles: ["teacher"]
    },
    {
      id: "matches",
      title: "Matches",
      description: "Browse, clone, edit, delete, or view your created matches",
      icon: <UnorderedListOutlined />,
      route: "/matches",
      accent: "#0ea5e9",
      roles: ["teacher"]
    },
    {
      id: "create-session",
      title: "Create Game Session",
      description: "Create a new game session for students to join",
      icon: <PlayCircleOutlined />,
      route: "/create-game-session",
      accent: "#f59e0b",
      roles: ["teacher"]
    },
    // 5. View Game Sessions
    {
      id: "view-sessions",
      title: "View Game Sessions",
      description: "Browse, clone, delete, view, or modify your created game sessions",
      icon: <UnorderedListOutlined />,
      route: "/game-sessions",
      accent: "#8b5cf6",
      roles: ["teacher"]
    },
    // 6. Hall of Fame
    {
      id: "hall-of-fame",
      title: "Hall of Fame",
      description: "View the leaderboard and top performers",
      icon: <TrophyOutlined />,
      route: "/hall-of-fame",
      accent: "#eab308",
      roles: ["teacher", "student"]
    },
    // 7. Tutorials
    {
      id: "tutorials",
      title: "Tutorials",
      description: "Learn how to use the platform with step-by-step guides",
      icon: <ReadOutlined />,
      route: "/tutorials",
      accent: "#14b8a6", // Teal color
      roles: ["teacher", "student", "admin"]
    },
    // Student specific cards (Student checks use filtering so order here matters less for mixed roles, but good to keep organized)
    {
      id: "join-session",
      title: "Join Game Sessions",
      description: "Join or list future and past game sessions",
      icon: <TeamOutlined />,
      route: "/join-game-session",
      accent: "#ec4899",
      roles: ["student"]
    },
    {
      id: "lobby",
      title: "Lobby",
      description: "View and manage your current game lobby",
      icon: <AppstoreOutlined />,
      route: "/lobby",
      accent: "#06b6d4",
      roles: ["student"]
    },
    {
      id: "admin-dashboard",
      title: "Admin Dashboard",
      description: "Manage users, roles, and system settings",
      icon: <SafetyCertificateOutlined />,
      route: "/admin-dashboard",
      accent: "#ef4444",
      roles: ["admin"]
    }
  ];

  const filteredItems = role
    ? bentoItems.filter((item) => item.roles.includes(role))
    : [];

  return (
    <div className="home-container">
      <div className="home-header">
        <Title level={1} className="home-title">
          Welcome to Codify
        </Title>
        <Paragraph className="home-subtitle">
          Select an option below to get started with creating and managing your matches.
        </Paragraph>
      </div>

      <div className="bento-grid">
        {filteredItems.map((item) => {
          const isActiveLobby = item.id === "lobby" && activeGame;
          return (
            <div
              key={item.id}
              id={`bento-card-${item.id}`}
              className={`bento-card ${isActiveLobby ? 'active-session-card' : ''}`}
              onClick={() => {
                if (isActiveLobby) {
                  const routes = {
                    lobby: `/lobby?gameId=${activeGame.game_id}`,
                    phase_one: `/phase-one?gameId=${activeGame.game_id}`,
                    phase_two: `/voting?gameId=${activeGame.game_id}`
                  };
                  const targetRoute = routes[activeGame.current_phase];

                  if (targetRoute) {
                    navigate(targetRoute);
                  } else {
                    message.error("Unable to continue session: Unknown game phase");
                    // Fallback to lobby
                    navigate(`/lobby?gameId=${activeGame.game_id}`);
                  }
                } else {
                  navigate(item.route);
                }
              }}
            >
              {/* Internal tag that follows card hover transforms */}
              {isActiveLobby && (
                <div id="active-session-tag" className="internal-status-tag">
                  IN PROGRESS
                </div>
              )}

              <div className="bento-card-inner">
                <div className="bento-header">
                  <div
                    className="bento-icon"
                    style={{
                      backgroundColor: `${item.accent}15`,
                      color: item.accent
                    }}
                  >
                    {isActiveLobby ? <PlayCircleOutlined /> : item.icon}
                  </div>
                  <h3 className="bento-title">
                    {isActiveLobby ? "Active Session" : item.title}
                  </h3>
                </div>
                <div className="bento-text">
                  <p id={isActiveLobby ? "active-session-description" : undefined} className="bento-description">
                    {isActiveLobby
                      ? `Continue: ${activeGame.game_name || 'Current Game'}`
                      : item.description}
                  </p>
                  {isActiveLobby && timeLeft > 0 && (
                    <div id="active-session-timer" className="card-timer">
                      {Math.floor(timeLeft / 60)}m {(timeLeft % 60).toString().padStart(2, "0")}s left
                    </div>
                  )}
                </div>
              </div>
              <div
                className="bento-accent-bar"
                style={{ backgroundColor: isActiveLobby ? "#10b981" : item.accent }}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default HomePage;
