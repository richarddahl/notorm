/**
 * Admin module components
 * This file exports all components in the admin module
 */

// Check if okui-admin-dashboard is already registered before importing
if (!customElements.get('okui-admin-dashboard')) {
  // Import components - only if not already registered
  import('./okui-admin-dashboard.js').then(() => {
    console.log('Admin dashboard component loaded');
  }).catch(error => {
    console.error('Failed to load admin dashboard component:', error);
  });
} else {
  console.log('Admin dashboard component already registered');
}

console.log('Admin components loaded successfully');