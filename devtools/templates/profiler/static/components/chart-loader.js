/**
 * Chart.js Loader
 * 
 * Utility to load Chart.js and related dependencies
 */

/**
 * Load Chart.js and its dependencies
 * @returns {Promise} Promise that resolves when Chart.js is loaded
 */
export function loadChartJS() {
  if (window.Chart) {
    return Promise.resolve(window.Chart);
  }
  
  return new Promise((resolve, reject) => {
    // Load Chart.js
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
    script.integrity = 'sha256-+8RZJua0aEWg+QVVKg4LEzEEm/8RFez5Tb4JBNiV5xA=';
    script.crossOrigin = 'anonymous';
    
    script.onload = () => {
      // Load the date-fns adapter for time axis
      const adapterScript = document.createElement('script');
      adapterScript.src = 'https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@2.0.0/dist/chartjs-adapter-date-fns.bundle.min.js';
      adapterScript.integrity = 'sha256-xl/Tj1qlcJYqlHDlUeJr3K+1MkIX56JGz6t2nB1AuwE=';
      adapterScript.crossOrigin = 'anonymous';
      
      adapterScript.onload = () => {
        // Register some default settings
        if (window.Chart) {
          // Apply theme defaults
          const fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
          
          Chart.defaults.font.family = fontFamily;
          Chart.defaults.font.size = 12;
          Chart.defaults.color = '#666';
          Chart.defaults.plugins.tooltip.titleFont.weight = 'normal';
          Chart.defaults.animation.duration = 800;
          Chart.defaults.responsive = true;
          Chart.defaults.maintainAspectRatio = false;
          
          // Resolve with Chart instance
          resolve(window.Chart);
        } else {
          reject(new Error('Failed to load Chart.js'));
        }
      };
      
      adapterScript.onerror = () => {
        reject(new Error('Failed to load Chart.js date adapter'));
      };
      
      document.head.appendChild(adapterScript);
    };
    
    script.onerror = () => {
      reject(new Error('Failed to load Chart.js'));
    };
    
    document.head.appendChild(script);
  });
}

/**
 * Create a time series chart
 * @param {HTMLCanvasElement} canvas - Canvas element
 * @param {Object} options - Chart options
 * @returns {Chart} Chart instance
 */
export function createTimeSeriesChart(canvas, options) {
  const {
    datasets,
    title,
    yAxisTitle,
    yMin = 0,
    yMax = 100,
    tooltipMode = 'index',
    timeUnit = 'minute',
  } = options;
  
  // Destroy existing chart if it exists
  if (canvas._chart) {
    canvas._chart.destroy();
  }
  
  // Create new chart
  canvas._chart = new Chart(canvas, {
    type: 'line',
    data: {
      datasets: datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: 'time',
          time: {
            unit: timeUnit,
            tooltipFormat: 'PP HH:mm:ss',
          },
          title: {
            display: true,
            text: 'Time',
          },
        },
        y: {
          beginAtZero: yMin === 0,
          min: yMin,
          max: yMax || undefined,
          title: {
            display: !!yAxisTitle,
            text: yAxisTitle || '',
          },
        },
      },
      plugins: {
        title: {
          display: !!title,
          text: title || '',
        },
        tooltip: {
          mode: tooltipMode,
          intersect: false,
        },
        legend: {
          position: 'top',
        },
      },
    },
  });
  
  return canvas._chart;
}

/**
 * Safely parse a date string into a JavaScript Date object
 * @param {string} dateString - Date string in ISO format
 * @returns {Date} JavaScript Date object
 */
export function parseDate(dateString) {
  try {
    return new Date(dateString);
  } catch (e) {
    console.error('Failed to parse date:', dateString);
    return new Date();
  }
}

/**
 * Format a number as a human-readable string
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
export function formatNumber(num) {
  if (num === undefined || num === null) {
    return '0';
  }
  
  return new Intl.NumberFormat().format(num);
}

/**
 * Format a duration in seconds as a human-readable string
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration
 */
export function formatDuration(seconds) {
  if (seconds === undefined || seconds === null) {
    return '0ms';
  }
  
  if (seconds < 0.001) {
    return `${(seconds * 1000000).toFixed(0)}μs`;
  } else if (seconds < 1) {
    return `${(seconds * 1000).toFixed(1)}ms`;
  } else {
    return `${seconds.toFixed(2)}s`;
  }
}

/**
 * Get a CSS class based on duration thresholds
 * @param {number} duration - Duration in seconds
 * @returns {string} CSS class name
 */
export function getDurationClass(duration) {
  if (duration < 0.1) {
    return 'status-success';
  } else if (duration < 1.0) {
    return 'status-warning';
  } else {
    return 'status-error';
  }
}