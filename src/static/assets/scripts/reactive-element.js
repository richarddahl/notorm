/**
 * reactive-element.js - Wrapper for @lit/reactive-element
 * 
 * This script provides a direct export of @lit/reactive-element to help with module resolution
 */

// Import from CDN
import * as reactiveElement from 'https://cdn.jsdelivr.net/npm/@lit/reactive-element@1.6.3/reactive-element.js';

// Export everything from the module
export * from 'https://cdn.jsdelivr.net/npm/@lit/reactive-element@1.6.3/reactive-element.js';

// Also make it available globally
window.ReactiveElement = reactiveElement;

console.log('ReactiveElement module loaded and available as window.ReactiveElement');