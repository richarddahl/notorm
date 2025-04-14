/**
 * Vector Search module index
 * This file registers and exports all vector search-related components
 */

import './wa-semantic-search.js';

// Create an alias class for the okui-vector-search-dashboard component
import { WebAwesomeSemanticSearch } from './wa-semantic-search.js';

// Register alternate component names for URL compatibility
if (!customElements.get('okui-semantic-search')) {
  customElements.define('okui-semantic-search', WebAwesomeSemanticSearch);
  console.log('okui-semantic-search alias component registered');
}

if (!customElements.get('okui-vector-search-dashboard')) {
  customElements.define('okui-vector-search-dashboard', WebAwesomeSemanticSearch);
  console.log('okui-vector-search-dashboard alias component registered');
}

console.log('Vector Search module components registered');