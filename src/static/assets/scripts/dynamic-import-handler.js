/**
 * dynamic-import-handler.js
 * 
 * A utility script that provides robust handling of dynamic imports,
 * particularly for bare module specifiers that would otherwise cause errors.
 */

// CDN URLs for common dependencies
const MODULE_URLS = {
  // Lit and related
  '@lit/reactive-element': 'https://cdn.jsdelivr.net/npm/@lit/reactive-element@1.6.3/reactive-element.js',
  'lit': 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js',
  'lit-element': 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js',
  'lit-html': 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js',
  
  // Chart.js
  'chart.js/auto': 'https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.js',
  'chart.js': 'https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.js',
  
  // Lit components
  'lit-element/lit-element.js': 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js',
  'lit-html/lit-html.js': 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js',
  'lit-html/is-server.js': '/static/assets/scripts/is-server.js',
  
  // Add additional dependencies here as needed
};

// Module cache to avoid re-importing the same modules
const moduleCache = new Map();

// Import promises for handling parallel imports of the same modules
const importPromises = new Map();

// Module mapping function to handle bare specifiers
window.dynamicImport = async (specifier) => {
  try {
    // Check cache first
    if (moduleCache.has(specifier)) {
      return moduleCache.get(specifier);
    }
    
    // Check if this import is already in progress (avoid duplicate requests)
    if (importPromises.has(specifier)) {
      return importPromises.get(specifier);
    }
    
    // Create a new promise for this import
    const importPromise = (async () => {
      try {
        // If we have a known CDN URL for this module, use it
        if (MODULE_URLS[specifier]) {
          console.log(`Using CDN URL for ${specifier}: ${MODULE_URLS[specifier]}`);
          const module = await import(MODULE_URLS[specifier]);
          moduleCache.set(specifier, module);
          return module;
        }
        
        // If it's a URL or relative path, try to import directly
        if (specifier.startsWith('http') || specifier.startsWith('/') || 
            specifier.startsWith('./') || specifier.startsWith('../')) {
          const module = await import(specifier);
          moduleCache.set(specifier, module);
          return module;
        }
        
        // For any other format, assume it might be a subpath of a known module
        for (const [baseModule, url] of Object.entries(MODULE_URLS)) {
          if (specifier.startsWith(`${baseModule}/`)) {
            console.log(`Using base module ${baseModule} for ${specifier}`);
            const module = await import(url);
            moduleCache.set(specifier, module);
            return module;
          }
        }
        
        // If global module is available, return it
        if (specifier === 'lit' && window.lit) {
          console.log('Using globally loaded Lit');
          return window.lit;
        }
        if (specifier === '@lit/reactive-element' && window.ReactiveElement) {
          console.log('Using globally loaded ReactiveElement');
          return { ReactiveElement: window.ReactiveElement };
        }
        if ((specifier === 'chart.js' || specifier === 'chart.js/auto') && window.Chart) {
          console.log('Using globally loaded Chart.js');
          return { Chart: window.Chart };
        }
        
        // If we get here, try the original import as a last resort
        console.warn(`No mapped URL for ${specifier}, attempting direct import`);
        const module = await import(specifier);
        moduleCache.set(specifier, module);
        return module;
      } catch (error) {
        console.error(`Failed to dynamically import ${specifier}:`, error);
        
        // Create a fallback module with console warnings for common exports
        if (specifier === 'lit' || specifier === 'lit-element' || specifier === 'lit-html') {
          console.warn(`Creating minimal Lit fallback for ${specifier}`);
          const fallback = {
            LitElement: window.LitElement || class LitElement extends HTMLElement {},
            html: window.html || ((strings, ...values) => {
              console.warn('Using fallback html tagged template literal');
              return strings.reduce((result, string, i) => {
                return result + string + (values[i] !== undefined ? values[i] : '');
              }, '');
            }),
            css: window.css || ((strings, ...values) => {
              console.warn('Using fallback css tagged template literal');
              return strings.reduce((result, string, i) => {
                return result + string + (values[i] !== undefined ? values[i] : '');
              }, '');
            }),
            nothing: window.nothing || '',
          };
          moduleCache.set(specifier, fallback);
          return fallback;
        }
        
        if (specifier === '@lit/reactive-element') {
          console.warn('Creating minimal ReactiveElement fallback');
          const fallback = {
            ReactiveElement: window.ReactiveElement || class ReactiveElement extends HTMLElement {},
          };
          moduleCache.set(specifier, fallback);
          return fallback;
        }
        
        if (specifier === 'chart.js/auto' || specifier === 'chart.js') {
          console.warn('Creating Chart.js fallback');
          class MockChart {
            constructor(ctx, config) {
              console.warn('Using mock Chart class, chart will not render');
              this.ctx = ctx;
              this.config = config;
            }
            update() {}
            destroy() {}
          }
          
          const fallback = {
            Chart: window.Chart || MockChart,
          };
          moduleCache.set(specifier, fallback);
          return fallback;
        }
        
        throw error;
      } finally {
        // Clean up the import promise after it completes or fails
        importPromises.delete(specifier);
      }
    })();
    
    // Store the promise so parallel imports can reuse it
    importPromises.set(specifier, importPromise);
    return importPromise;
  } catch (error) {
    console.error(`Critical error in dynamicImport for ${specifier}:`, error);
    throw error;
  }
};

// Create a workaround for environments where import.meta is not available
// We can't directly assign to import.meta, but we can use this for fallback logic
const getImportMetaUrl = () => {
  try {
    return import.meta.url;
  } catch (e) {
    return window.location.href;
  }
};

// Store a backup URL for module resolution
window.__importMetaUrl = getImportMetaUrl();

// Patch dynamic imports globally for consistent handling
const originalImport = window.importShim || (s => import(s));
window.importShim = async (specifier, ...args) => {
  try {
    return await originalImport(specifier, ...args);
  } catch (error) {
    console.warn(`importShim failed for ${specifier}, falling back to dynamicImport`);
    return window.dynamicImport(specifier);
  }
};

// Preload common dependencies to ensure they're available
const preloadCommonDependencies = async () => {
  try {
    // Lit
    const lit = await dynamicImport('lit');
    if (!window.LitElement) window.LitElement = lit.LitElement;
    if (!window.html) window.html = lit.html;
    if (!window.css) window.css = lit.css;
    if (!window.nothing) window.nothing = lit.nothing;
    if (!window.repeat) window.repeat = lit.repeat;
    if (!window.choose) window.choose = lit.choose;
    if (!window.guard) window.guard = lit.guard;
    if (!window.cache) window.cache = lit.cache;
    if (!window.classMap) window.classMap = lit.classMap;
    if (!window.styleMap) window.styleMap = lit.styleMap;
    
    // ReactiveElement
    const reactiveElement = await dynamicImport('@lit/reactive-element');
    if (!window.ReactiveElement) window.ReactiveElement = reactiveElement.ReactiveElement;
    
    // Chart.js
    const chartJs = await dynamicImport('chart.js/auto');
    if (!window.Chart) window.Chart = chartJs.Chart;
    
    console.log('Common dependencies preloaded successfully');
  } catch (error) {
    console.error('Error preloading dependencies:', error);
  }
};

// Start preloading immediately
preloadCommonDependencies();

// Add global error handler for unhandled promise rejections related to imports
window.addEventListener('unhandledrejection', (event) => {
  if (event.reason && event.reason.message && 
      (event.reason.message.includes('Failed to fetch') || 
       event.reason.message.includes('Failed to resolve module') ||
       event.reason.message.includes('import') ||
       event.reason.message.includes('module'))) {
    console.warn('Caught unhandled module loading rejection:', event.reason);
    event.preventDefault();
  }
});

console.log('Enhanced dynamic import handler initialized');

// Make dynamicImport available as a global function
window.dynamicImport = window.dynamicImport || dynamicImport;