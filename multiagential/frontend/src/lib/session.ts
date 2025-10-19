/**
 * Session Management using Cookies
 * Handles user identification and session persistence across page reloads
 */

const SESSION_COOKIE_NAME = 'alkenacode_user_id';
const SESSION_EXPIRY_DAYS = 365; // 1 year

/**
 * Generate a unique user ID
 */
function generateUserId(): string {
  return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Set a cookie
 */
function setCookie(name: string, value: string, days: number): void {
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
}

/**
 * Get a cookie value
 */
function getCookie(name: string): string | null {
  const nameEQ = name + '=';
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
}

/**
 * Delete a cookie
 */
function deleteCookie(name: string): void {
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
}

/**
 * Get or create user session
 * Returns a persistent user ID stored in cookies
 */
export function getUserSession(): string {
  let userId = getCookie(SESSION_COOKIE_NAME);

  if (!userId) {
    // Create new user session
    userId = generateUserId();
    setCookie(SESSION_COOKIE_NAME, userId, SESSION_EXPIRY_DAYS);
    console.log('New user session created:', userId);
  } else {
    console.log('Existing user session found:', userId);
  }

  return userId;
}

/**
 * Clear user session (logout)
 */
export function clearUserSession(): void {
  deleteCookie(SESSION_COOKIE_NAME);
  console.log('User session cleared');
}

/**
 * Check if user has an active session
 */
export function hasActiveSession(): boolean {
  return getCookie(SESSION_COOKIE_NAME) !== null;
}

/**
 * Store adaptive onboarding completion status
 */
const ONBOARDING_COOKIE_NAME = 'alkenacode_onboarding_complete';

export function setOnboardingComplete(userId: string): void {
  setCookie(ONBOARDING_COOKIE_NAME, userId, SESSION_EXPIRY_DAYS);
}

export function getOnboardingStatus(): string | null {
  return getCookie(ONBOARDING_COOKIE_NAME);
}

export function clearOnboardingStatus(): void {
  deleteCookie(ONBOARDING_COOKIE_NAME);
}

/**
 * Session Manager - Main API
 */
export const SessionManager = {
  getUserId: getUserSession,
  clearSession: clearUserSession,
  hasSession: hasActiveSession,
  setOnboardingComplete,
  getOnboardingStatus,
  clearOnboarding: clearOnboardingStatus,
};
