/**
 * chart-loader.js
 * 
 * A utility script to ensure Chart.js is properly loaded and globally available
 * for all components that need it. This script loads Chart.js and exposes it 
 * as a global variable.
 */

// Create a promise that will resolve when Chart.js is loaded
window.chartJsLoadPromise = new Promise((resolve, reject) => {
  // Check if Chart.js is already loaded
  if (window.Chart) {
    console.log('Chart.js already loaded globally');
    resolve(window.Chart);
    return;
  }
  
  // If not loaded, create a script element and load it
  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.js';
  script.async = true;
  
  // Resolve the promise when the script loads
  script.onload = () => {
    console.log('Chart.js loaded successfully');
    resolve(window.Chart);
  };
  
  // Reject the promise if loading fails
  script.onerror = () => {
    console.error('Failed to load Chart.js from CDN');
    
    // Provide a fallback mock implementation
    window.Chart = class MockChart {
      constructor(ctx, config) {
        console.warn('Using mock Chart implementation');
        this.ctx = ctx;
        this.config = config;
      }
      update() {}
      destroy() {}
    };
    
    resolve(window.Chart); // We resolve with the mock for graceful degradation
  };
  
  // Add the script to the document
  document.head.appendChild(script);
});

// Expose a helper function to await chart loading before using it
window.ensureChartJsLoaded = async function() {
  return window.chartJsLoadPromise;
};

// Immediately start loading Chart.js
window.ensureChartJsLoaded()
  .then(Chart => {
    console.log('Chart.js is ready to use');
  })
  .catch(error => {
    console.error('Error initializing Chart.js:', error);
  });