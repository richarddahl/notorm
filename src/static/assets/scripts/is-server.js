/**
 * Minimal implementation of lit-html/is-server.js
 * This provides a simple fallback for the is-server.js module
 * which is used by Lit to determine if the code is running in a server environment
 */

// Export a constant indicating this is not a server environment
export const isServer = false;

// Some implementations also need this
export default isServer;