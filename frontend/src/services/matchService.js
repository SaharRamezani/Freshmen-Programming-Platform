import { API_BASE_URL, API_ENDPOINTS } from './config';
import { apiFetch } from './api';

export const createMatch = async (matchData) => {
  try {
    const url = `${API_BASE_URL}${API_ENDPOINTS.MATCHES}`;
    const response = await apiFetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(matchData),
    });

    if (!response.ok) {
      let errorMessage = `Failed to create match: ${response.statusText}`;
      const status = response.status;
      const contentType = response.headers.get('content-type');

      try {
        if (contentType && contentType.includes('application/json')) {
          const errorData = await response.json();
          const serverMessage = errorData.detail || errorData.message;

          if (status === 400) {
            errorMessage = serverMessage || 'Invalid match data. Please check your inputs.';
          } else if (status === 404) {
            errorMessage = 'The selected match setting was not found. It may have been deleted.';
          } else if (status === 409) {
            errorMessage = serverMessage || 'A match with this configuration already exists.';
          } else if (status >= 500) {
            errorMessage = 'Server error. Please try again later.';
          } else {
            errorMessage = serverMessage || `Failed to create match: ${response.statusText}`;
          }
        } else {
          const errorText = await response.text();
          if (errorText && status >= 500) {
            errorMessage = 'Server error. Please try again later.';
          } else {
            errorMessage = errorText.substring(0, 200) + (errorText.length > 200 ? '...' : '') || `Failed to create match: ${response.statusText}`;
          }
        }
      } catch (parseError) {
        if (status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else if (status >= 400) {
          errorMessage = 'Invalid request. Please check your inputs.';
        } else {
          errorMessage = `Failed to create match: ${response.statusText}`;
        }
      }

      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

export const getMatches = async () => {
  try {
    const response = await apiFetch(`${API_BASE_URL}${API_ENDPOINTS.MATCHES}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Error fetching matches: ${response.statusText}`);
    }

    const data = await response.json();
    return data; // Return the list of matches
  } catch (error) {
    throw error;
  }
};

export const getMatch = async (matchId) => {
  const response = await apiFetch(`${API_BASE_URL}${API_ENDPOINTS.MATCHES}/${matchId}`, {
    method: 'GET',
  });
  if (!response.ok) {
    throw new Error(`Error fetching match: ${response.statusText}`);
  }
  return response.json();
};

export const updateMatch = async (matchId, matchData) => {
  const response = await apiFetch(`${API_BASE_URL}${API_ENDPOINTS.MATCHES}/${matchId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(matchData),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to update match');
  }
  return response.json();
};

export const deleteMatch = async (matchId) => {
  const response = await apiFetch(`${API_BASE_URL}${API_ENDPOINTS.MATCHES}/${matchId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to delete match');
  }
};

export const cloneMatch = async (matchId) => {
  const response = await apiFetch(`${API_BASE_URL}${API_ENDPOINTS.MATCHES}/${matchId}/clone`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to clone match');
  }
  return response.json();
};
