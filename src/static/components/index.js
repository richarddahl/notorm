/**
 * Main components module loader
 * This file imports all component modules to ensure they are available
 * when the application starts.
 */

// Initialize critical modules - preload critical dependencies
const preloadDependencies = async () => {
  // First, load Lit
  try {
    const litModule = await import('https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js');
    window.LitModule = litModule;
    window.LitElement = litModule.LitElement;
    window.html = litModule.html;
    window.css = litModule.css;
    window.nothing = litModule.nothing;
    console.log('Lit preloaded successfully');
  } catch (e) {
    console.error('Failed to preload Lit:', e);
  }
  
  // Load ReactiveElement
  try {
    const reactiveElement = await import('https://cdn.jsdelivr.net/npm/@lit/reactive-element@1.6.3/reactive-element.js');
    window.ReactiveElementModule = reactiveElement;
    console.log('ReactiveElement preloaded successfully');
  } catch (e) {
    console.error('Failed to preload ReactiveElement:', e);
  }
  
  // Load Chart.js
  try {
    const chartModule = await import('https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.js');
    window.Chart = chartModule.Chart;
    console.log('Chart.js preloaded successfully');
  } catch (e) {
    console.error('Failed to preload Chart.js:', e);
  }
  
  // Install module resolution handler
  window.moduleResolutionHandler = (specifier) => {
    // Handle Lit and ReactiveElement imports
    if (specifier === '@lit/reactive-element') {
      return window.ReactiveElementModule || {};
    }
    if (specifier === 'lit-html' || specifier === 'lit-element' || specifier === 'lit') {
      return window.LitModule || {};
    }
    if (specifier === 'chart.js/auto' || specifier === 'chart.js') {
      return { Chart: window.Chart };
    }
    console.warn(`Unknown module requested: ${specifier}`);
    return {};
  };
};

// Execute preloading before importing components
await preloadDependencies();

// First import core components
// Note: app shell is loaded directly in admin.html
import './app/index.js';
import './admin/index.js';
import './base/index.js';

// Import core UI building blocks
import './detail/index.js';
import './dialogs/index.js';
import './forms/index.js';
import './list/index.js';
import './utilities/index.js';

// Import functional modules
import './attributes/index.js';
import './authorization/index.js';
import './values/index.js';
import './queries/index.js';
import './reports/index.js';
import './security/index.js';
import './monitoring/index.js';
import './jobs/index.js';
import './workflows/index.js';
import './vector-search/index.js';
import './generic/index.js';

console.log('All UNO UI components loaded successfully');