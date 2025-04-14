/**
 * Vector Search module index
 * This file registers and exports all vector search-related components
 */

import './wa-semantic-search.js';
import { WebAwesomeSemanticSearch } from './wa-semantic-search.js';

// Create alias classes with proper extension
// We need to create separate classes for each tag name 
// because we can't reuse the same constructor for multiple custom elements

// Alias for okui-semantic-search
class OkUISemanticSearch extends WebAwesomeSemanticSearch {
  constructor() {
    super();
    console.log('OkUISemanticSearch constructor (alias for wa-semantic-search)');
  }
}

// Alias for okui-vector-search-dashboard
class OkUIVectorSearchDashboard extends WebAwesomeSemanticSearch {
  constructor() {
    super();
    console.log('OkUIVectorSearchDashboard constructor (alias for wa-semantic-search)');
  }
}

// Register alternative tag names if not already registered
if (!customElements.get('okui-semantic-search')) {
  try {
    customElements.define('okui-semantic-search', OkUISemanticSearch);
    console.log('okui-semantic-search alias component registered');
  } catch (e) {
    console.warn('Failed to register okui-semantic-search:', e);
  }
}

if (!customElements.get('okui-vector-search-dashboard')) {
  try {
    customElements.define('okui-vector-search-dashboard', OkUIVectorSearchDashboard);
    console.log('okui-vector-search-dashboard alias component registered');
  } catch (e) {
    console.warn('Failed to register okui-vector-search-dashboard:', e);
  }
}

// Export all component classes for reuse
export { 
  WebAwesomeSemanticSearch,
  OkUISemanticSearch,
  OkUIVectorSearchDashboard
};

console.log('Vector Search module components registered');