import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import HomePage from './components/Home';
import { CreateMatchForm } from './components/CreateMatchForm';
import { MatchList } from './components/MatchList';
import { MatchSettingsList } from './components/MatchSettings';
import CreateMatchSetting from './components/CreateMatchSetting';
import { GameSessionCreation } from './components/GameSessionCreation';
import { GameSessionList } from './components/GameSessionList';
import { StartGameSession } from './components/StartGameSession';
import { PreStartGameSession } from './components/PreStartGameSession';
import { Login } from './components/Login';
import { JoinGameSession } from './components/JoinGameSession';
import { Lobby } from './components/Lobby';
import HallOfFame from './components/HallOfFame';
import GameResults from './components/GameResults';
import ProtectedRoute from './components/ProtectedRoute';
import PublicRoute from './components/PublicRoute';
import AppLayout from './components/AppLayout';
import { setToken } from './services/authService';
import AlgorithmMatchPhaseOne from './components/PhaseOne/AlgorithmMatchPhaseOne';
import { SolutionReview } from './components/SolutionReview';
import SolutionResults from './components/SolutionResults';
import Profile from './components/Profile';
import AdminDashboard from './components/AdminDashboard/AdminDashboard';
import TutorialPage from './components/Tutorials/TutorialPage';

import './App.css';

function App() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('access_token');
    if (token) {
      setToken(token);
      window.history.replaceState({}, document.title, '/');
      window.location.href = '/';
    }
  }, []);

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      <Router>
        <div className="App">
          <Routes>
            {/* Protected route - home page */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <HomePage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            {/* Backwards-compat route - many components still navigate('/home') */}
            <Route
              path="/home"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <HomePage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            {/* Public route - login page */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            {/* Protected routes - require authentication */}
            <Route
              path="/create-match"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <CreateMatchForm />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/matches"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <MatchList />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/matches/:id/edit"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <CreateMatchForm />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/matches/:id/view"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <CreateMatchForm />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/match-settings"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <MatchSettingsList />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/match-settings/create"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <CreateMatchSetting />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/match-settings/:id/edit"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <CreateMatchSetting />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/create-game-session"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <GameSessionCreation />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/game-sessions"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <GameSessionList />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/start-game-session/:id"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <StartGameSession />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/pre-start-game-session/:id"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <PreStartGameSession />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/join-game-session"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <JoinGameSession />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/lobby"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Lobby />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/hall-of-fame"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <HallOfFame />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/solution-results/:solutionId"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <SolutionResults />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/game-results"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <GameResults />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Profile />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/phase-one"
              element={
                <ProtectedRoute>
                  <AlgorithmMatchPhaseOne />
                </ProtectedRoute>
              }
            />
            <Route
              path="/voting"
              element={
                <ProtectedRoute>
                  <SolutionReview />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin-dashboard"
              element={
                <ProtectedRoute>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/tutorials"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <TutorialPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            {/* Catch-all route - redirects to root */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </ConfigProvider>
  );
}

export default App;
