import { useState, useEffect, useCallback } from 'react';
import {
  getMatches,
  deleteMatch as deleteMatchService,
  cloneMatch as cloneMatchService,
} from '../../../services/matchService';

const ERROR_MESSAGES = {
  LOAD_FAILED: 'Failed to load matches',
  DELETE_FAILED: 'Failed to delete match',
  CLONE_FAILED: 'Failed to clone match',
};

const SUCCESS_MESSAGES = {
  DELETED: 'Match deleted successfully',
  CLONED: 'Match cloned successfully',
};

/**
 * Custom hook for managing matches CRUD operations
 */
export const useMatches = (showAlert, showSuccess) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchItems = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getMatches();
      const formatted = data.map((item) => ({
        match_id: item.match_id,
        title: item.title,
        match_set_id: item.match_set_id,
        creator_id: item.creator_id,
        difficulty_level: item.difficulty_level,
        review_number: item.review_number,
        duration_phase1: item.duration_phase1,
        duration_phase2: item.duration_phase2,
      }));
      setItems(formatted);
    } catch (err) {
      console.error('Error fetching matches:', err);
      showAlert?.('error', ERROR_MESSAGES.LOAD_FAILED);
    } finally {
      setLoading(false);
    }
  }, [showAlert]);

  const handleDelete = useCallback(async (matchId) => {
    try {
      setLoading(true);
      await deleteMatchService(matchId);
      setItems(prev => prev.filter(m => m.match_id !== matchId));
      showSuccess?.(SUCCESS_MESSAGES.DELETED);
      return true;
    } catch (err) {
      console.error('Error deleting match:', err);
      showAlert?.('error', err.message || ERROR_MESSAGES.DELETE_FAILED);
      return false;
    } finally {
      setLoading(false);
    }
  }, [showAlert, showSuccess]);

  const handleClone = useCallback(async (matchId) => {
    try {
      setLoading(true);
      await cloneMatchService(matchId);
      await fetchItems();
      showSuccess?.(SUCCESS_MESSAGES.CLONED);
      return true;
    } catch (err) {
      console.error('Error cloning match:', err);
      showAlert?.('error', err.message || ERROR_MESSAGES.CLONE_FAILED);
      return false;
    } finally {
      setLoading(false);
    }
  }, [showAlert, showSuccess, fetchItems]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  return {
    items,
    loading,
    fetchItems,
    deleteMatch: handleDelete,
    cloneMatch: handleClone,
  };
};
