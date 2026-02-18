import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Modal, Button, Typography, Space } from 'antd';
const { Title, Text } = Typography;

const DodgeTheBugsGame = ({ onClose, visible }) => {
    const canvasRef = useRef(null);
    const requestRef = useRef(null);
    const scoreRef = useRef(0);
    const lastTimeRef = useRef(0);
    
    // Game State
    const [gameState, setGameState] = useState('start'); // start, playing, gameover
    const [score, setScore] = useState(0);
    const [bestScore, setBestScore] = useState(() => {
        return parseFloat(localStorage.getItem('dodgeBugsBest')) || 0;
    });

    // Game Entities (Using refs to avoid re-renders during game loop)
    const player = useRef({ x: 200, y: 350, width: 30, height: 30, speed: 300, dx: 0 }); // speed in px/s
    const bugs = useRef([]);
    const spawnTimer = useRef(0);
    const difficultyTimer = useRef(0);
    const lastScoreUpdate = useRef(0);
    
    // Constants
    const CAN_WIDTH = 400;
    const CAN_HEIGHT = 400;
    const PLAYER_SIZE = 20;
    const BUG_SIZE = 20;
    const INITIAL_SPAWN_RATE = 600; // ms
    
    const settings = useRef({
        spawnRate: INITIAL_SPAWN_RATE,
        bugSpeed: 100, // px/s
        canvasWidth: CAN_WIDTH,
        canvasHeight: CAN_HEIGHT
    });

    // Inputs
    const keys = useRef({ ArrowLeft: false, ArrowRight: false, a: false, d: false });

    // Game Logic
    const spawnBug = () => {
        const x = Math.random() * (settings.current.canvasWidth - BUG_SIZE);
        bugs.current.push({
            x,
            y: -BUG_SIZE,
            width: BUG_SIZE,
            height: BUG_SIZE,
            speed: settings.current.bugSpeed + (Math.random() * 50 - 25) // Variance
        });
    };

    const update = (deltaTime, time) => {
        // Update Difficulty
        difficultyTimer.current += deltaTime;
        if (difficultyTimer.current > 5000) { // Every 5 seconds
            settings.current.spawnRate = Math.max(200, settings.current.spawnRate * 0.95);
            settings.current.bugSpeed *= 1.05;
            difficultyTimer.current -= 5000; // Subtract instead of reset to avoid time drif
        }

        // Spawn Bugs
        spawnTimer.current += deltaTime;
        if (spawnTimer.current > settings.current.spawnRate) {
            spawnBug();
            spawnTimer.current = 0;
        }

        // Move Player
        let moveX = 0;
        if (keys.current.ArrowLeft || keys.current.a || keys.current.A) moveX -= 1;
        if (keys.current.ArrowRight || keys.current.d || keys.current.D) moveX += 1;
        
        player.current.x += moveX * player.current.speed * (deltaTime / 1000);
        
        // Clamp Player
        player.current.x = Math.max(0, Math.min(settings.current.canvasWidth - PLAYER_SIZE, player.current.x));

        // Move Bugs & Collision
        for (let i = bugs.current.length - 1; i >= 0; i--) {
            const bug = bugs.current[i];
            bug.y += bug.speed * (deltaTime / 1000);

            // Remove if off screen
            if (bug.y > settings.current.canvasHeight) {
                bugs.current.splice(i, 1);
                continue;
            }

            // Collision Detection (AABB)
            if (
                player.current.x < bug.x + bug.width &&
                player.current.x + PLAYER_SIZE > bug.x &&
                player.current.y < bug.y + bug.height &&
                player.current.y + PLAYER_SIZE > bug.y
            ) {
                gameOver();
            }
        }

        // Score
        scoreRef.current += deltaTime / 1000;
        
        // Throttle score state update to every 100ms prevents React visual glitches/GC
        if (time - lastScoreUpdate.current > 100) {
            setScore(scoreRef.current);
            lastScoreUpdate.current = time;
        }
    };

    const draw = (ctx) => {
        // Clear
        ctx.fillStyle = '#222';
        ctx.fillRect(0, 0, settings.current.canvasWidth, settings.current.canvasHeight);

        // Player
        ctx.fillStyle = '#4CAF50';
        ctx.beginPath();
        ctx.arc(
            player.current.x + PLAYER_SIZE / 2, 
            player.current.y + PLAYER_SIZE / 2, 
            PLAYER_SIZE / 2, 
            0, Math.PI * 2
        );
        ctx.fill();

        // Bugs
        ctx.fillStyle = '#ff4d4f';
        bugs.current.forEach(bug => {
            ctx.fillRect(bug.x, bug.y, bug.width, bug.height);
        });
    };

    const loop = (time) => {
        if (gameState !== 'playing') return;
        
        if (!lastTimeRef.current) lastTimeRef.current = time;
        const deltaTime = time - lastTimeRef.current;
        lastTimeRef.current = time;

        update(deltaTime, time);
        
        const canvas = canvasRef.current;
        if (canvas) {
            const ctx = canvas.getContext('2d');
            if (ctx) draw(ctx);
        }

        requestRef.current = requestAnimationFrame(loop);
    };

    const startGame = useCallback(() => {
        setGameState('playing');
        setScore(0);
        scoreRef.current = 0;
        lastTimeRef.current = 0;
        lastScoreUpdate.current = 0;
        
        // Reset Entities
        player.current = { x: CAN_WIDTH / 2 - PLAYER_SIZE / 2, y: CAN_HEIGHT - 40, width: PLAYER_SIZE, height: PLAYER_SIZE, speed: 300 };
        bugs.current = [];
        spawnTimer.current = 0;
        difficultyTimer.current = 0;
        settings.current = {
            spawnRate: INITIAL_SPAWN_RATE,
            bugSpeed: 150,
            canvasWidth: CAN_WIDTH,
            canvasHeight: CAN_HEIGHT
        };

        if (requestRef.current) cancelAnimationFrame(requestRef.current);
        requestRef.current = requestAnimationFrame(loop);
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const gameOver = () => {
        setGameState('gameover');
        if (requestRef.current) cancelAnimationFrame(requestRef.current);
        
        if (scoreRef.current > bestScore) {
            setBestScore(scoreRef.current);
            localStorage.setItem('dodgeBugsBest', scoreRef.current.toFixed(2));
        }
    };

    // Key handlers
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && visible) {
                onClose();
            }
            if (keys.current.hasOwnProperty(e.key) || keys.current.hasOwnProperty(e.code) || ['a', 'd', 'A', 'D'].includes(e.key)) {
                keys.current[e.key] = true;
            }
            // Prevent scrolling with arrows if focused on game
            if (['ArrowLeft', 'ArrowRight'].includes(e.key) && visible) {
                e.preventDefault();
            }
        };
        const handleKeyUp = (e) => {
            if (keys.current.hasOwnProperty(e.key) || keys.current.hasOwnProperty(e.code) || ['a', 'd', 'A', 'D'].includes(e.key)) {
                keys.current[e.key] = false;
            }
        };

        if (visible) {
            window.addEventListener('keydown', handleKeyDown);
            window.addEventListener('keyup', handleKeyUp);
        }
        
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, [visible, onClose]);

    // Stop game when closed (Reset to start state for simplicity)
    useEffect(() => {
        if (!visible) {
            setGameState('start');
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        }
    }, [visible]);

    // Loop trigger
    useEffect(() => {
        if (gameState === 'playing') {
            requestRef.current = requestAnimationFrame(loop);
        }
        return () => {
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        };
    }, [gameState]); // eslint-disable-line react-hooks/exhaustive-deps

    if (!visible) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 9999
        }} onClick={onClose}>
            <div 
                style={{
                    backgroundColor: '#fff',
                    padding: '20px',
                    borderRadius: '8px',
                    textAlign: 'center',
                    minWidth: '440px',
                    position: 'relative'
                }}
                onClick={e => e.stopPropagation()}
            >
                <Title level={4}>Dodge the Bugs</Title>
                <Space style={{ marginBottom: 10, justifyContent: 'space-between', width: '100%' }}>
                    <Text strong>Survival: {score.toFixed(2)}s</Text>
                    <Text type="secondary">Best: {typeof bestScore === 'number' ? bestScore.toFixed(2) : parseFloat(bestScore).toFixed(2)}s</Text>
                </Space>

                <div style={{ position: 'relative', width: CAN_WIDTH, height: CAN_HEIGHT, margin: '0 auto', backgroundColor: '#222' }}>
                    <canvas 
                        ref={canvasRef}
                        width={CAN_WIDTH}
                        height={CAN_HEIGHT}
                        style={{ display: 'block' }}
                    />
                    
                    {gameState === 'start' && (
                        <div style={{
                            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                            display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
                            backgroundColor: 'rgba(0,0,0,0.5)', color: 'white'
                        }}>
                            <Button type="primary" size="large" onClick={startGame}>Start Game</Button>
                            <Text style={{ color: '#ccc', marginTop: 10 }}>← → or A/D to move</Text>
                        </div>
                    )}

                    {gameState === 'gameover' && (
                        <div style={{
                            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                            display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
                            backgroundColor: 'rgba(0,0,0,0.7)', color: 'white'
                        }}>
                            <Title level={3} style={{ color: '#ff4d4f', margin: 0 }}>Game Over</Title>
                            <Text style={{ color: 'white', fontSize: '1.2em' }}>Time: {score.toFixed(2)}s</Text>
                            <Button type="primary" onClick={startGame} style={{ marginTop: 15 }}>Restart</Button>
                        </div>
                    )}
                </div>

                <div style={{ marginTop: 15, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>Esc to close</Text>
                    <Space>
                        {gameState === 'playing' && <Button onClick={() => setGameState('start')}>Pause</Button>}
                        <Button onClick={onClose}>Close</Button>
                    </Space>
                </div>
            </div>
        </div>
    );
};

export default DodgeTheBugsGame;
