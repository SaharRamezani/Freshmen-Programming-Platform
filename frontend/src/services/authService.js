import { API_BASE_URL } from "./config";

// Auth enabled by default unless testing mode is on or explicitly disabled
const AUTH_ENABLED_DEFAULT = process.env.REACT_APP_TESTING_MODE === 'true' 
  ? false 
  : (process.env.REACT_APP_AUTH_ENABLED === 'false' ? false : true);

const DEV_MODE_KEY = "dev_mode_bypass";

export const isAuthEnabled = () => {
  return AUTH_ENABLED_DEFAULT;
};

export const isDevModeEnabled = () => {
  return localStorage.getItem(DEV_MODE_KEY) === "true";
};

export const enableDevMode = () => {
  localStorage.setItem(DEV_MODE_KEY, "true");
  localStorage.setItem("token", "dev_mode_token");
};

export const disableDevMode = () => {
  localStorage.removeItem(DEV_MODE_KEY);
  if (localStorage.getItem("token") === "dev_mode_token") {
    localStorage.removeItem("token");
  }
};

export const hasToken = () => {
  return !!localStorage.getItem("token");
};

export const getToken = () => {
  return localStorage.getItem("token");
};

export const removeToken = () => {
  localStorage.removeItem("token");
};

export const setToken = (token) => {
  localStorage.setItem("token", token);
};

export const validateToken = async () => {
  if (!isAuthEnabled()) {
    return true;
  }

  // Check if dev mode is enabled
  // SECURITY NOTE: This bypasses backend token validation when dev mode is enabled.
  // Any code path that relies on validateToken for authorization will be circumvented.
  // Ensure dev mode is only enabled in controlled development environments.
  if (isDevModeEnabled()) {
    const token = getToken();
    if (token === "dev_mode_token") {
      console.warn("⚠️ DEV MODE: Authentication bypassed");
      return true;
    }
  }

  const token = getToken();
  if (!token) {
    return false;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/validate`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      credentials: "include", // Include cookies for refresh token
    });

    if (response.ok) {
      return true;
    }

    // If 401, try to refresh the token
    if (response.status === 401) {
      return await refreshToken();
    }

    return false;
  } catch (error) {
    console.error("Error validating token:", error);
    return false;
  }
};

/**
 * Refresh the access token using the refresh token cookie
 */
export const refreshToken = async () => {
  // If auth is disabled, skip refresh attempts.
  if (!isAuthEnabled()) {
    return true;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include", // Include cookies for refresh token
    });

    if (response.ok) {
      const data = await response.json();
      if (data.access_token) {
        setToken(data.access_token);
        return true;
      }
    }

    // Refresh failed, remove token
    removeToken();
    return false;
  } catch (error) {
    console.error("Error refreshing token:", error);
    removeToken();
    return false;
  }
};

/**
 * Logout the user by revoking the refresh token
 */
export const logout = async () => {
  try {
    // If auth is disabled, just clear local state (no backend calls).
    if (!isAuthEnabled()) {
      return;
    }

    // Only call backend logout if not in dev mode
    const token = getToken();
    if (token !== "dev_mode_token") {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Include cookies for refresh token
      });
    }
  } catch (error) {
    console.error("Error during logout:", error);
  } finally {
    // Always remove token and disable dev mode
    disableDevMode();
    removeToken();
  }
};
