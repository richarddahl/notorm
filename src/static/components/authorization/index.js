/**
 * Authorization module index
 * This file registers and exports all authorization-related components
 */

import './wa-role-manager.js';
import { WebAwesomeRoleManager } from './wa-role-manager.js';

// Create alias classes for URL compatibility
class OkUIRoleManager extends WebAwesomeRoleManager {
  constructor() {
    super();
    console.log('OkUIRoleManager constructor (alias for wa-role-manager)');
  }
}

class OkUIAuthorizationDashboard extends WebAwesomeRoleManager {
  constructor() {
    super();
    console.log('OkUIAuthorizationDashboard constructor (alias for wa-role-manager)');
  }
}

// Register alternate component names for URL compatibility
if (!customElements.get('okui-role-manager')) {
  try {
    customElements.define('okui-role-manager', OkUIRoleManager);
    console.log('okui-role-manager alias component registered');
  } catch (e) {
    console.warn('Failed to register okui-role-manager:', e);
  }
}

if (!customElements.get('okui-authorization-dashboard')) {
  try {
    customElements.define('okui-authorization-dashboard', OkUIAuthorizationDashboard);
    console.log('okui-authorization-dashboard alias component registered');
  } catch (e) {
    console.warn('Failed to register okui-authorization-dashboard:', e);
  }
}

// Export components for reuse
export {
  WebAwesomeRoleManager,
  OkUIRoleManager,
  OkUIAuthorizationDashboard
};

console.log('Authorization module components registered');