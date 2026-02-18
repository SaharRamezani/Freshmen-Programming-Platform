import { API_BASE_URL } from "./config";
import { isAuthEnabled } from "./authService";

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });

    failedQueue = [];
};

export const apiFetch = async (url, options = {}) => {
    const token = localStorage.getItem("token");
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };

    if (isAuthEnabled() && token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers,
    };

    try {
        const response = await fetch(url, config);

        if (!isAuthEnabled()) {
            return response;
        }

        if (response.status === 401) {
            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then((newToken) => {
                        if (newToken) {
                            config.headers["Authorization"] = `Bearer ${newToken}`;
                        }
                        return fetch(url, config);
                    })
                    .catch((err) => {
                        return Promise.reject(err);
                    });
            }

            isRefreshing = true;

            try {
                const refreshUrl = new URL("/auth/refresh", API_BASE_URL);
                const refreshResponse = await fetch(refreshUrl.toString(), {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });

                if (refreshResponse.ok) {

                    const data = await refreshResponse.json();
                    const newToken = data.access_token;

                    if (newToken) {
                        localStorage.setItem("token", newToken);
                        processQueue(null, newToken);

                        config.headers["Authorization"] = `Bearer ${newToken}`;
                        return fetch(url, config);
                    }
                } else {
                    throw new Error("Failed to refresh token");
                }

            } catch (error) {
                processQueue(error, null);
                localStorage.removeItem("token");
                window.location.href = "/login";
                return Promise.reject(error);
            } finally {
                isRefreshing = false;
            }
        }

        return response;
    } catch (error) {
        return Promise.reject(error);
    }
};
