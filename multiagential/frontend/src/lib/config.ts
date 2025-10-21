/**
 * Configuration utility for accessing environment variables
 */

export const config = {
  /**
   * Get the API base URL from environment variable
   * Falls back to localhost if not set
   */
  apiUrl: 'https://school.alkenacode.dev/api',
} as const;

/**
 * Helper function to get the API base URL
 * Use this in components that need to make direct fetch calls
 */
export const getApiUrl = () => config.apiUrl;
