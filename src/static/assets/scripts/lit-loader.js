/**
 * lit-loader.js - Universal Lit loader for UNO components
 * 
 * This script provides a consistent way to load Lit dependencies for all components,
 * regardless of how they try to import them (bare specifiers, direct URLs, etc.)
 */

// First, load the core Lit dependencies from the CDN
import * as lit from 'https://cdn.jsdelivr.net/npm/lit@2.8.0/index.js';
import * as litHtml from 'https://cdn.jsdelivr.net/npm/lit-html@2.8.0/lit-html.js';
import * as reactiveElement from 'https://cdn.jsdelivr.net/npm/@lit/reactive-element@1.6.3/reactive-element.js';

// Import individual directives
import { repeat } from 'https://cdn.jsdelivr.net/npm/lit@2.8.0/directives/repeat.js';
import { cache } from 'https://cdn.jsdelivr.net/npm/lit@2.8.0/directives/cache.js';
import { classMap } from 'https://cdn.jsdelivr.net/npm/lit@2.8.0/directives/class-map.js';
import { styleMap } from 'https://cdn.jsdelivr.net/npm/lit@2.8.0/directives/style-map.js';
import { guard } from 'https://cdn.jsdelivr.net/npm/lit@2.8.0/directives/guard.js';
import { choose } from 'https://cdn.jsdelivr.net/npm/lit@2.8.0/directives/choose.js';

// Make all components available globally to help with module resolution
const { LitElement, html, css } = lit;

// Create a complete Lit object with all exports
const LitComplete = {
  // Core Lit exports
  LitElement,
  html,
  css,
  
  // Add lit-html exports
  ...litHtml,
  
  // Add reactive-element exports
  ...reactiveElement,
  
  // Add directives
  directives: {
    repeat,
    cache,
    classMap,
    styleMap,
    guard,
    choose
  }
};

// Export for direct imports
export { LitElement, html, css };
export { nothing } from 'https://cdn.jsdelivr.net/npm/lit-html@2.8.0/lit-html.js';
export { repeat };
export { choose };
export { guard };
export { cache };
export { classMap };
export { styleMap };

// Make everything available globally
window.Lit = LitComplete;
window.LitElement = LitElement;
window.html = html;
window.css = css;
window.nothing = nothing;
window.repeat = repeat;
window.choose = choose;

// Install a global module resolution handler for bare specifiers
if (window.moduleResolutionFallback === undefined) {
  window.moduleResolutionFallback = (specifier) => {
    if (specifier === '@lit/reactive-element') {
      return reactiveElement;
    }
    if (specifier === 'lit-html') {
      return litHtml;
    }
    if (specifier === 'lit') {
      return lit;
    }
    if (specifier === 'lit/directives/repeat.js') {
      return { repeat };
    }
    if (specifier === 'lit/directives/choose.js') {
      return { choose };
    }
    if (specifier === 'lit/directives/guard.js') {
      return { guard };
    }
    if (specifier === 'lit/directives/cache.js') {
      return { cache };
    }
    if (specifier === 'lit/directives/class-map.js') {
      return { classMap };
    }
    if (specifier === 'lit/directives/style-map.js') {
      return { styleMap };
    }
    if (specifier === 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js') {
      return { LitElement, css, html, nothing, choose, repeat, guard, cache, classMap, styleMap };
    }
    throw new Error(`Unknown module: ${specifier}`);
  };
}

console.log('Lit libraries loaded and globally available:', window.Lit);