import { API_BASE_URL, API_ENDPOINTS } from "./config";
import { apiFetch } from "./api";

export async function createGameSession(matchIds, creatorId, name, startDate, duration_phase1, duration_phase2) {
  try {
    const url = new URL(API_ENDPOINTS.GAME_SESSIONS, API_BASE_URL);
    const res = await apiFetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        match_id: matchIds,
        creator_id: creatorId,
        name: name,
        start_date: startDate,
        duration_phase1: duration_phase1,
        duration_phase2: duration_phase2
      }),
    });
    if (!res.ok) {
      let errorMessage = `Failed to create game session: ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData && errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (jsonErr) {
        // Ignore JSON parse errors
      }
      throw new Error(errorMessage);
    }
    return await res.json();
  } catch (err) {
    throw new Error(err.message);
  }
}

export async function getGameSessionsByCreator(creatorId) {
  try {
    const url = new URL(`${API_ENDPOINTS.GAME_SESSIONS}/by_creator/${creatorId}`, API_BASE_URL);
    const res = await apiFetch(url.toString());
    if (!res.ok) {
      let errorMessage = `Failed to fetch game sessions: ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData && errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (jsonErr) {
        // Ignore JSON parse errors
      }
      throw new Error(errorMessage);
    }
    return await res.json();
  } catch (err) {
    throw new Error(err.message);
  }
}

export async function deleteGameSession(gameId) {
  try {
    const url = new URL(`${API_ENDPOINTS.GAME_SESSIONS}/${gameId}`, API_BASE_URL);
    const res = await apiFetch(url.toString(), {
      method: "DELETE",
    });
    if (!res.ok) {
      let errorMessage = `Failed to delete game session: ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData && errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (jsonErr) {
        // Ignore JSON parse errors
      }
      throw new Error(errorMessage);
    }
    return true;
  } catch (err) {
    throw new Error(err.message);
  }
}

export async function cloneGameSession(gameId) {
  try {
    const url = new URL(`${API_ENDPOINTS.GAME_SESSIONS}/${gameId}/clone`, API_BASE_URL);
    const res = await apiFetch(url.toString(), {
      method: "POST",
    });
    if (!res.ok) {
      let errorMessage = `Failed to clone game session: ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData && errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (jsonErr) {
        // Ignore JSON parse errors
      }
      throw new Error(errorMessage);
    }
    return await res.json();
  } catch (err) {
    throw new Error(err.message);
  }
}

/**
 * Updates an existing game session with the specified updates.
 *
 * @param {string|number} gameId - The ID of the game session to update.
 * @param {Object} updates - An object containing the fields to update in the game session.
 * @returns {Promise<Object>} A promise that resolves to the updated game session object.
 */
export async function updateGameSession(gameId, updates) {
  try {
    const url = new URL(`${API_ENDPOINTS.GAME_SESSIONS}/${gameId}`, API_BASE_URL);
    const res = await apiFetch(url.toString(), {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updates),
    });
    if (!res.ok) {
      let errorMessage = `Failed to update game session: ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData && errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (jsonErr) {
        // Ignore JSON parse errors
      }
      throw new Error(errorMessage);
    }
    return await res.json();
  } catch (err) {
    throw new Error(err.message);
  }
}

/**
 * Fetches a game session by its ID.
 *
 * @param {string|number} gameId - The ID of the game session to fetch.
 * @returns {Promise<Object>} A promise that resolves to the game session object.
 */
export async function getGameSessionById(gameId) {
  try {
    const url = new URL(`${API_ENDPOINTS.GAME_SESSIONS}/${gameId}`, API_BASE_URL);
    const res = await apiFetch(url.toString());
    if (!res.ok) {
      let errorMessage = `Failed to fetch game session: ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData && errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (jsonErr) {
        // Ignore JSON parse errors, use statusText
      }
      throw new Error(errorMessage);
    }
    return await res.json();
  } catch (err) {
    throw new Error(`Failed to create game session: ${err.message}`);
  }
}

/**
 * Fetches a game session by its ID.
 *
 * @param {string|number} gameId - The ID of the game session to fetch.
 * @returns {Promise<Object>} A promise that resolves to the game session object.
 */
export async function getGameSessionDetails(gameId) {
  try {
    const url = new URL(`${API_ENDPOINTS.GAME_SESSIONS}/${gameId}/details`, API_BASE_URL);
    const res = await apiFetch(url.toString());
    if (!res.ok) {
      let errorMessage = `Failed to fetch game session details: ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData && errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (jsonErr) {
        // Ignore JSON parse errors, use statusText
      }
      throw new Error(errorMessage);
    }
    return await res.json();
  } catch (err) {
    throw new Error(`Failed to fetch game session: ${err.message}`);
  }
}

export async function startGameSession(gameId) {
  try {
    const url = new URL(`${API_ENDPOINTS.GAME_SESSIONS}/${gameId}/start`, API_BASE_URL);
    const res = await apiFetch(url.toString(), {
      method: "POST",
    });
    if (!res.ok) {
      let errorMessage = `Failed to start game session: ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData && errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (jsonErr) {
        // Ignore JSON parse errors
      }
      throw new Error(errorMessage);
    }
    return await res.json();
  } catch (err) {
    throw new Error(err.message);
  }
}

/**
 * Checks if a game session has started (actual_start_date is set).
 *
 * @param {string|number} gameId - The ID of the game session to check.
 * @returns {Promise<Object>} A promise that resolves to an object with has_started, game_id, and actual_start_date.
 */
export async function checkGameSessionStatus(gameId) {
  try {
    const url = new URL(`${API_ENDPOINTS.GAME_SESSIONS}/${gameId}/status`, API_BASE_URL);
    const res = await apiFetch(url.toString());
    if (!res.ok) {
      let errorMessage = `Failed to check game session status: ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData && errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (jsonErr) {
        // Ignore JSON parse errors
      }
      throw new Error(errorMessage);
    }
    return await res.json();
  } catch (err) {
    throw new Error(err.message);
  }
}
