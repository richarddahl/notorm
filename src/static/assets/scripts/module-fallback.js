/**
 * module-fallback.js - Dynamic module resolution fallback
 * 
 * This script provides last-resort fallbacks for module resolution errors
 * by intercepting module loading errors and providing polyfills.
 */

// Define a map of fallback modules to load for problematic imports
const FALLBACK_MODULES = {
  '@lit/reactive-element': '/static/assets/scripts/reactive-element.js',
  'lit': '/static/assets/scripts/lit-loader.js',
  'lit-html': '/static/assets/scripts/lit-loader.js',
  'lit-element': '/static/assets/scripts/lit-loader.js'
};

// Keep track of which modules we've already tried to load
const loadedModules = new Set();

// Create global error handler for module resolution issues
window.addEventListener('error', (event) => {
  // Only handle module resolution errors
  if (!event.error || !event.error.message || !event.error.message.includes('Failed to resolve module specifier')) {
    return;
  }
  
  // Extract the module name from the error message
  const errorMsg = event.error.message;
  console.error('Module resolution error:', errorMsg);
  
  // Look for quoted module name in the error message
  const moduleMatch = errorMsg.match(/"([^"]+)"/);
  if (!moduleMatch) {
    console.error('Could not extract module name from error');
    return;
  }
  
  const moduleName = moduleMatch[1];
  console.log(`Attempting to load fallback for module: ${moduleName}`);
  
  // Check if we have a fallback for this module
  if (FALLBACK_MODULES[moduleName] && !loadedModules.has(moduleName)) {
    loadedModules.add(moduleName);
    
    // Dynamically load the fallback module
    const script = document.createElement('script');
    script.type = 'module';
    script.src = FALLBACK_MODULES[moduleName];
    script.onload = () => console.log(`Fallback loaded for ${moduleName}`);
    script.onerror = (err) => console.error(`Failed to load fallback for ${moduleName}`, err);
    
    document.head.appendChild(script);
    console.log(`Added fallback script for ${moduleName}: ${FALLBACK_MODULES[moduleName]}`);
    
    // Prevent the error from bubbling up
    event.preventDefault();
    return false;
  }
});

console.log('Module fallback system initialized');