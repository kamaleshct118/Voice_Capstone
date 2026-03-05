/**
 * Session management utilities for persistent storage across page reloads
 */

const ASSISTANT_SESSION_KEY = "assistant_session_id";
const HEALTH_MONITOR_SESSION_KEY = "health_monitor_session_id";

/**
 * Get or create a session ID for the assistant page
 * Persists in localStorage for 48 hours (matching backend DB0 TTL)
 */
export const getOrCreateAssistantSession = (): string => {
  return getOrCreateSession(ASSISTANT_SESSION_KEY);
};

/**
 * Get or create a session ID for the health monitor page
 * Persists in localStorage for 48 hours (matching backend DB0 TTL)
 */
export const getOrCreateHealthSession = (): string => {
  return getOrCreateSession(HEALTH_MONITOR_SESSION_KEY);
};

/**
 * Generic session ID getter/creator with expiration check
 */
const getOrCreateSession = (key: string): string => {
  try {
    const stored = localStorage.getItem(key);
    const timestampKey = `${key}_timestamp`;
    const timestamp = localStorage.getItem(timestampKey);

    // Check if session exists and is not expired (48 hours = 172800000 ms)
    if (stored && timestamp) {
      const age = Date.now() - parseInt(timestamp, 10);
      const TTL_MS = 48 * 60 * 60 * 1000; // 48 hours in milliseconds

      if (age < TTL_MS) {
        return stored;
      }
    }

    // Create new session
    const newId = crypto.randomUUID();
    localStorage.setItem(key, newId);
    localStorage.setItem(timestampKey, Date.now().toString());
    return newId;
  } catch (err) {
    console.error("Failed to access localStorage:", err);
    // Fallback to temporary session if localStorage is unavailable
    return crypto.randomUUID();
  }
};

/**
 * Clear a specific session
 */
export const clearSession = (key: string): void => {
  try {
    localStorage.removeItem(key);
    localStorage.removeItem(`${key}_timestamp`);
  } catch (err) {
    console.error("Failed to clear session:", err);
  }
};

/**
 * Clear assistant session
 */
export const clearAssistantSession = (): void => {
  clearSession(ASSISTANT_SESSION_KEY);
};

/**
 * Clear health monitor session
 */
export const clearHealthSession = (): void => {
  clearSession(HEALTH_MONITOR_SESSION_KEY);
};

/**
 * Get current assistant session ID without creating a new one
 */
export const getAssistantSessionId = (): string | null => {
  try {
    return localStorage.getItem(ASSISTANT_SESSION_KEY);
  } catch {
    return null;
  }
};

/**
 * Get current health monitor session ID without creating a new one
 */
export const getHealthSessionId = (): string | null => {
  try {
    return localStorage.getItem(HEALTH_MONITOR_SESSION_KEY);
  } catch {
    return null;
  }
};
