import { useState, useEffect } from "react";
import { getStudentGameStatus } from "../services/phaseOneService";

const useActiveGame = () => {
    const [activeGame, setActiveGame] = useState(null);
    const [timeLeft, setTimeLeft] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchActiveGame = async () => {
        try {
            setLoading(true);
            const gameStatus = await getStudentGameStatus();
            if (gameStatus.has_active_game && gameStatus.current_phase !== "ended") {
                setActiveGame(gameStatus);
                setTimeLeft(gameStatus.remaining_seconds);
            } else {
                setActiveGame(null);
                setTimeLeft(null);
            }
        } catch (err) {
            console.error("Failed to fetch active game:", err);
            setActiveGame(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchActiveGame();
    }, []);

    useEffect(() => {
        if (timeLeft === null || timeLeft <= 0) return;

        const timer = setInterval(() => {
            setTimeLeft((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [timeLeft]);

    return { activeGame, timeLeft, loading, refreshActiveGame: fetchActiveGame };
};

export default useActiveGame;
