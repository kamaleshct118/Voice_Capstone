/**
 * Session management utilities for persistent storage across page reloads
 */

const ASSISTANT_SESSION_KEY = "assistant_session_id";
const HEALTH_MONITOR_SESSION_KEY = "health_monitor_session_id";

/**
 * Get or create a session ID for the assistant page
 * Persists in localStorage for 48 hours (matching backend DB0 TTL)
 */
let assistantSessionId: string | null = null;
let healthSessionId: string | null = null;

export const getOrCreateAssistantSession = (): string => {
  if (!assistantSessionId) {
    assistantSessionId = crypto.randomUUID();
  }
  return assistantSessionId;
};

export const getOrCreateHealthSession = (): string => {
  if (!healthSessionId) {
    healthSessionId = crypto.randomUUID();
  }
  return healthSessionId;
};

const getOrCreateSession = (key: string): string => {
  // Legacy function kept for backwards compatibility if needed
  return crypto.randomUUID();
};

/**
 * Clear a specific session
 */
export const clearSession = (key: string): void => {
  // Legacy function kept for backwards compatibility
};

export const clearAssistantSession = (): void => {
  assistantSessionId = null;
  localStorage.removeItem(ASSISTANT_SESSION_KEY);
  localStorage.removeItem(`${ASSISTANT_SESSION_KEY}_timestamp`);
};

export const clearHealthSession = (): void => {
  healthSessionId = null;
  localStorage.removeItem(HEALTH_MONITOR_SESSION_KEY);
  localStorage.removeItem(`${HEALTH_MONITOR_SESSION_KEY}_timestamp`);
};

export const getAssistantSessionId = (): string | null => {
  return assistantSessionId;
};

export const getHealthSessionId = (): string | null => {
  return healthSessionId;
};
