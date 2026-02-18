# Codify – Freshmen Programming Platform

Codify is an interactive, gamified programming platform designed for university freshmen. Teachers create coding challenges and game sessions, while students solve problems, write test cases, and review each other's solutions in real time. The platform features two main phases, a **Coding Challenge** and a **Peer Review**, followed by automatic scoring and leaderboard rankings.

---

## Platform Overview

### Teacher Experience

#### Teacher Dashboard

After logging in, teachers see their main control panel to manage match settings, matches, game sessions, and results.

![Teacher home dashboard](frontend/public/tutorials/images/teacher-home.png)

#### Creating Match Settings

Teachers define challenge parameters such as difficulty, time limits, and test cases.

![Create match setting - step 1](frontend/public/tutorials/images/create-match-setting-1-teacher.png)

![Create match setting - step 2](frontend/public/tutorials/images/create-match-setting-2-teacher.png)

#### Viewing Match Settings

All saved match settings can be browsed and managed.

![List of match settings](frontend/public/tutorials/images/list-match-setting-teacher.png)

#### Creating a Match

Teachers create matches by selecting a match setting and filling in the details.

![Create new match](frontend/public/tutorials/images/create-new-match-teacher.png)

#### Creating & Managing Game Sessions

Sessions define when and how students participate. Teachers set the session name, start time, duration, and associated match.

![Create game session](frontend/public/tutorials/images/create-game-session-teacher.png)

![List of game sessions](frontend/public/tutorials/images/list-game-session-teacher.png)

#### Starting the Game

Once students are in the lobby, teachers start the session from the control panel.

![Start game session](frontend/public/tutorials/images/start-game-session-teacher.png)

#### Monitoring Phase 1

Teachers can monitor student progress, see submissions, and track time remaining during the coding phase.

![Phase 1 teacher view](frontend/public/tutorials/images/phase1-teacher.png)

#### End of Game

After all phases complete, scores are calculated and rankings are updated automatically.

![End of game results](frontend/public/tutorials/images/end-of-game-teacher.png)

#### Teacher Profile

![Teacher profile](frontend/public/tutorials/images/profile-teacher.png)

---

### Student Experience

#### Student Home Page

Students see their dashboard with options to join sessions, enter the lobby, and view the Hall of Fame.

![Student home](frontend/public/tutorials/images/student-home.png)

#### Joining a Game Session

Students browse available sessions and click **Join** to participate.

![Join game session](frontend/public/tutorials/images/join-game-session-student.png)

#### The Lobby (Waiting Room)

After joining, students wait in the lobby until the teacher starts the game. A mini-game is available to pass the time!

![Lobby](frontend/public/tutorials/images/lobby-student.png)

![Mini-game](frontend/public/tutorials/images/mini-game-student.png)

![Mini-game over](frontend/public/tutorials/images/mini-game-gameover-student.png)

#### Phase 1 – Coding Challenge

Students read the problem, review test cases, and write their solution in the code editor under a time limit.

![Phase 1 coding challenge](frontend/public/tutorials/images/phase1-student.png)

Students can add custom test cases to verify edge cases:

![Add custom test case](frontend/public/tutorials/images/add-test-case-phase1-student.png)

Test results are shown immediately — **pass** or **fail**:

![Tests passed](frontend/public/tutorials/images/phase1-passed-student.png)

![Tests failed](frontend/public/tutorials/images/phase1-failed-student.png)

When the solution is correct:

![Correct solution](frontend/public/tutorials/images/correct-code-phase1-student.png)

#### Phase 2 – Peer Review

After coding ends, students review each other's solutions and vote:

![Solution review](frontend/public/tutorials/images/solution-review-student.png)

- **Correct** – the solution works as expected:

  ![Vote correct](frontend/public/tutorials/images/phase2-correct-vote-student.png)

- **Incorrect** – a mistake was found (a failing test case must be provided):

  ![Vote incorrect](frontend/public/tutorials/images/phase2-incorrect-vote-student.png)

- **Skip** – unable to evaluate:

  ![Vote skip](frontend/public/tutorials/images/phase2-skip-vote-student.png)

#### Hall of Fame

The global leaderboard shows rankings, scores, and allows searching for classmates.

![Hall of Fame](frontend/public/tutorials/images/hall-of-fame-student.png)

#### Student Profile

![Student profile](frontend/public/tutorials/images/profile-student.png)

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) & Docker Compose

### Launch

```bash
docker compose up --build
```

### Rebuild from scratch

```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

---

## Environment Variables

This repo uses a root `.env` file (ignored by git) for local configuration.

### Frontend

| Variable | Default | Description |
|---|---|---|
| `REACT_APP_API_URL` | `http://localhost:8000` | Backend API URL |
| `REACT_APP_AUTH_ENABLED` | `false` | When `false`, route protection, token validation, and Google auth UI are bypassed (useful for development/testing) |

### API

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | Secret key for JWT token signing |
| `SECRET_KEY` | Application secret key |
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth 2.0 client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth 2.0 client secret |
| `GOOGLE_OAUTH_REDIRECT_URI` | Google OAuth redirect URI |

---

## 📂 Project Structure

```
├── api/                  # Backend API (Python / FastAPI)
│   └── src/
│       ├── authentication/   # Auth module (OAuth, JWT)
│       ├── models.py         # Database models
│       ├── phase_one.py      # Coding challenge logic
│       ├── phase_two.py      # Peer review logic
│       └── ...
├── frontend/             # Frontend (React)
│   ├── public/
│   │   ├── badges/           # Badge images
│   │   └── tutorials/        # Tutorial docs & screenshots
│   └── src/
│       ├── components/       # React components
│       ├── services/         # API service layers
│       └── hooks/            # Custom React hooks
├── postgres/             # Database initialization scripts
├── test/                 # Integration / E2E tests (Java)
└── docker-compose.yml
```