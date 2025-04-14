/**
 * App components module index
 * This file exports all components in the app directory
 */

// Skip importing app shell here to avoid duplicate registration
// The okui-app-shell.js component is loaded directly in admin.html
// and defined in /src/static/components/okui-app-shell.js

// Log status of app components
console.log('App components module loaded successfully');
console.log('App shell registration status:', customElements.get('okui-app-shell') ? 'Registered' : 'Not registered');