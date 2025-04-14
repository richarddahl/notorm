/**
 * module-fallback.js - Dynamic module resolution fallback
 * 
 * This script provides last-resort fallbacks for module resolution errors
 * by intercepting module loading errors and providing polyfills.
 */

// Define a map of fallback modules to load for problematic imports
const FALLBACK_MODULES = {
  '@lit/reactive-element': 'https://cdn.jsdelivr.net/npm/@lit/reactive-element@1.6.3/reactive-element.js',
  'lit': 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js',
  'lit-html': 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js',
  'lit-element': 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js',
  'chart.js/auto': 'https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.js',
  'chart.js': 'https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.js',
  'lit-element/lit-element.js': 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js',
  'lit-html/lit-html.js': 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js',
  'lit-html/is-server.js': '/static/assets/scripts/is-server.js'
};

// Keep track of which modules we've already tried to load
const loadedModules = new Set();

// Create a fallback map for common exports
const EXPORT_FALLBACKS = {
  'lit': {
    LitElement: class LitElement extends HTMLElement {
      constructor() {
        super();
        console.warn('Using fallback LitElement class');
        this.attachShadow({ mode: 'open' });
      }
      render() { return ''; }
    },
    html: (strings, ...values) => {
      console.warn('Using fallback html tagged template literal');
      return strings.reduce((result, string, i) => {
        return result + string + (values[i] !== undefined ? values[i] : '');
      }, '');
    },
    css: (strings, ...values) => {
      console.warn('Using fallback css tagged template literal');
      return strings.reduce((result, string, i) => {
        return result + string + (values[i] !== undefined ? values[i] : '');
      }, '');
    },
    nothing: '',
    repeat: (items, keyFn, template) => items.map(template),
    choose: (value, cases) => cases[value] || cases.default || '',
    guard: (value, fn) => fn(value),
    cache: (value) => value,
    classMap: (classes) => Object.keys(classes).filter(key => classes[key]).join(' '),
    styleMap: (styles) => Object.entries(styles).map(([key, value]) => `${key}: ${value}`).join(';'),
  },
  '@lit/reactive-element': {
    ReactiveElement: class ReactiveElement extends HTMLElement {
      constructor() {
        super();
        console.warn('Using fallback ReactiveElement class');
      }
    }
  },
  'chart.js': {
    Chart: class MockChart {
      constructor(ctx, config) {
        console.warn('Using mock Chart class, chart will not render');
        this.ctx = ctx;
        this.config = config;
      }
      update() {}
      destroy() {}
    }
  }
};

// Inject fallbacks for module resolution
function injectModuleFallback(moduleName) {
  if (loadedModules.has(moduleName)) return false;
  
  console.log(`Attempting to load fallback for module: ${moduleName}`);
  loadedModules.add(moduleName);
  
  // If we have a CDN fallback, load it dynamically
  if (FALLBACK_MODULES[moduleName]) {
    console.log(`Loading fallback from CDN for ${moduleName}: ${FALLBACK_MODULES[moduleName]}`);
    
    // Use dynamic import when possible
    if (window.dynamicImport) {
      window.dynamicImport(FALLBACK_MODULES[moduleName])
        .then(module => {
          console.log(`Fallback dynamically loaded for ${moduleName}`);
          
          // Make the common exports globally available
          if (moduleName === 'lit' || moduleName === 'lit-element' || moduleName === 'lit-html') {
            if (!window.LitElement && module.LitElement) window.LitElement = module.LitElement;
            if (!window.html && module.html) window.html = module.html;
            if (!window.css && module.css) window.css = module.css;
          }
          
          if (moduleName === '@lit/reactive-element') {
            if (!window.ReactiveElement && module.ReactiveElement) window.ReactiveElement = module.ReactiveElement;
          }
          
          if (moduleName === 'chart.js' || moduleName === 'chart.js/auto') {
            if (!window.Chart && module.Chart) window.Chart = module.Chart;
          }
        })
        .catch(error => {
          console.error(`Failed to load CDN fallback for ${moduleName}:`, error);
          injectJsFallback(moduleName);
        });
      return true;
    }
    
    // Fallback to script tag if dynamicImport is not available
    const script = document.createElement('script');
    script.type = 'module';
    script.src = FALLBACK_MODULES[moduleName];
    script.onload = () => console.log(`Fallback loaded for ${moduleName}`);
    script.onerror = (err) => {
      console.error(`Failed to load fallback for ${moduleName}`, err);
      injectJsFallback(moduleName);
    };
    
    document.head.appendChild(script);
    return true;
  }
  
  // If we don't have a CDN fallback, use JS object fallback
  return injectJsFallback(moduleName);
}

// Inject JS object fallbacks
function injectJsFallback(moduleName) {
  if (EXPORT_FALLBACKS[moduleName]) {
    console.log(`Using JavaScript fallback for ${moduleName}`);
    
    // Add exports to window
    const fallbacks = EXPORT_FALLBACKS[moduleName];
    for (const [exportName, implementation] of Object.entries(fallbacks)) {
      if (!window[exportName]) {
        window[exportName] = implementation;
        console.log(`Added fallback for ${moduleName}.${exportName}`);
      }
    }
    
    return true;
  }
  
  return false;
}

// Create global error handler for module resolution issues
window.addEventListener('error', (event) => {
  // Only handle module resolution errors
  if (!event.error || !event.error.message || 
      (!event.error.message.includes('Failed to resolve module specifier') && 
       !event.error.message.includes('Cannot find module')) &&
       !event.error.message.includes('module is not defined')) {
    return;
  }
  
  // Extract the module name from the error message
  const errorMsg = event.error.message;
  console.error('Module resolution error:', errorMsg);
  
  // Common patterns in error messages to extract module names
  const patterns = [
    /"([^"]+)"/, // "module-name"
    /module '([^']+)'/, // module 'module-name'
    /Cannot find module "([^"]+)"/, // Cannot find module "module-name"
    /Failed to resolve module specifier "([^"]+)"/ // Failed to resolve module specifier "module-name"
  ];
  
  let moduleName = null;
  for (const pattern of patterns) {
    const match = errorMsg.match(pattern);
    if (match && match[1]) {
      moduleName = match[1];
      break;
    }
  }
  
  if (!moduleName) {
    console.error('Could not extract module name from error');
    return;
  }
  
  // Try to load a fallback
  if (injectModuleFallback(moduleName)) {
    // Prevent the error from bubbling up
    event.preventDefault();
    return false;
  }
});

// Listen for unhandled promise rejections (for async imports)
window.addEventListener('unhandledrejection', (event) => {
  if (!event.reason || !event.reason.message) return;
  
  const errorMsg = event.reason.message;
  
  // Check if this is a module loading error
  if (errorMsg.includes('Failed to resolve module specifier') || 
      errorMsg.includes('Cannot find module') ||
      errorMsg.includes('module is not defined') ||
      errorMsg.includes('import')) {
    
    console.warn('Caught unhandled module loading rejection:', errorMsg);
    
    // Extract module name using the same patterns as the error handler
    const patterns = [
      /"([^"]+)"/, // "module-name"
      /module '([^']+)'/, // module 'module-name'
      /Cannot find module "([^"]+)"/, // Cannot find module "module-name"
      /Failed to resolve module specifier "([^"]+)"/ // Failed to resolve module specifier "module-name"
    ];
    
    let moduleName = null;
    for (const pattern of patterns) {
      const match = errorMsg.match(pattern);
      if (match && match[1]) {
        moduleName = match[1];
        break;
      }
    }
    
    if (moduleName && injectModuleFallback(moduleName)) {
      event.preventDefault();
    }
  }
});

// Preload common critical dependencies
setTimeout(() => {
  ['lit', '@lit/reactive-element', 'chart.js/auto'].forEach(module => {
    if (!loadedModules.has(module) && window.dynamicImport) {
      window.dynamicImport(module).catch(error => {
        console.warn(`Preloading ${module} failed:`, error);
        injectModuleFallback(module);
      });
    }
  });
}, 0);

console.log('Enhanced module fallback system initialized');