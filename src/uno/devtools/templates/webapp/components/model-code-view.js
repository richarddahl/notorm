/**
 * Model Code View component
 * 
 * A web component for displaying and copying the generated code from the model.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * Model Code View
 * 
 * @element model-code-view
 */
@customElement('model-code-view')
export class ModelCodeView extends LitElement {
  static styles = css`
    :host {
      display: block;
      height: 100%;
      width: 100%;
      box-sizing: border-box;
    }
    
    .code-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      padding: 0;
      overflow: hidden;
    }
    
    .code-tabs {
      display: flex;
      background-color: #f5f5f5;
      border-bottom: 1px solid #ddd;
      overflow-x: auto;
    }
    
    .code-tab {
      padding: 8px 15px;
      cursor: pointer;
      white-space: nowrap;
      border-right: 1px solid #ddd;
    }
    
    .code-tab.active {
      background-color: white;
      border-bottom: 2px solid #0078d7;
    }
    
    .entity-tabs {
      display: flex;
      background-color: #f9f9f9;
      border-bottom: 1px solid #ddd;
      overflow-x: auto;
    }
    
    .entity-tab {
      padding: 6px 12px;
      cursor: pointer;
      white-space: nowrap;
      font-size: 0.9em;
      border-right: 1px solid #eee;
    }
    
    .entity-tab.active {
      background-color: white;
      border-bottom: 2px solid #0078d7;
    }
    
    .code-content {
      flex: 1;
      overflow: auto;
      position: relative;
    }
    
    pre {
      margin: 0;
      padding: 15px;
      background-color: #fafafa;
      border-radius: 4px;
      overflow: auto;
      font-family: 'Fira Code', 'Courier New', monospace;
      font-size: 14px;
      line-height: 1.5;
      white-space: pre-wrap;
      position: absolute;
      top: 0;
      bottom: 0;
      left: 0;
      right: 0;
    }
    
    .code-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 15px;
      background-color: #f5f5f5;
      border-bottom: 1px solid #ddd;
    }
    
    .copy-button {
      padding: 5px 10px;
      background-color: #0078d7;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
    }
    
    .copy-button:hover {
      background-color: #005a9e;
    }
    
    .file-path {
      font-size: 12px;
      color: #555;
      margin: 0;
    }
    
    .placeholder {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #777;
      font-style: italic;
    }
    
    /* Syntax highlighting */
    .keyword { color: #0000ff; }
    .string { color: #a31515; }
    .comment { color: #008000; }
    .type { color: #267f99; }
    .function { color: #795e26; }
    .decorator { color: #af00db; }
  `;

  @property({ type: Object }) code = null;
  @property({ type: String }) activeTab = 'entities';
  @property({ type: String }) activeEntity = '';
  
  updated(changedProperties) {
    if (changedProperties.has('code') && this.code) {
      // Set first entity as active when code changes
      const entityNames = Object.keys(this.code?.entities || {});
      if (entityNames.length > 0 && !entityNames.includes(this.activeEntity)) {
        this.activeEntity = entityNames[0];
      }
    }
  }
  
  changeTab(tab) {
    this.activeTab = tab;
  }
  
  changeEntity(entity) {
    this.activeEntity = entity;
  }
  
  getFilePathForActiveTab() {
    if (!this.activeEntity) return '';
    
    switch(this.activeTab) {
      case 'entities':
        return `domain/${this.activeEntity.toLowerCase()}_entity.py`;
      case 'repositories':
        return `infrastructure/repositories/${this.activeEntity.toLowerCase()}_repository.py`;
      case 'services':
        return `domain/services/${this.activeEntity.toLowerCase()}_service.py`;
      default:
        return '';
    }
  }
  
  getActiveCode() {
    if (!this.code || !this.activeEntity) return '';
    
    switch(this.activeTab) {
      case 'entities':
        return this.code.entities[this.activeEntity] || '';
      case 'repositories':
        return this.code.repositories[this.activeEntity] || '';
      case 'services':
        return this.code.services[this.activeEntity] || '';
      default:
        return '';
    }
  }
  
  async copyCode() {
    const code = this.getActiveCode();
    if (!code) return;
    
    try {
      await navigator.clipboard.writeText(code);
      
      // Show a temporary copy success indicator
      const copyButton = this.shadowRoot.querySelector('.copy-button');
      if (copyButton) {
        const originalText = copyButton.textContent;
        copyButton.textContent = 'Copied!';
        copyButton.disabled = true;
        
        setTimeout(() => {
          copyButton.textContent = originalText;
          copyButton.disabled = false;
        }, 2000);
      }
    } catch (error) {
      console.error('Failed to copy code:', error);
    }
  }
  
  // Basic syntax highlighting
  highlightSyntax(code) {
    if (!code) return '';
    
    // Replace special characters first
    let highlighted = code
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    
    // Highlight Python syntax
    highlighted = highlighted
      // Keywords
      .replace(/\b(import|from|class|def|return|if|else|elif|for|while|try|except|finally|with|as|async|await|raise|in|is|not|and|or|None|True|False|self|pass)\b/g, '<span class="keyword">$1</span>')
      // Decorators
      .replace(/(@\w+)/g, '<span class="decorator">$1</span>')
      // Strings
      .replace(/("(?:\\.|[^"\\])*")/g, '<span class="string">$1</span>')
      .replace(/('(?:\\.|[^'\\])*')/g, '<span class="string">$1</span>')
      // Multi-line docstrings
      .replace(/(""\".+?""")/gs, '<span class="string">$1</span>')
      .replace(/(""\"\s*(?:\n[^"]*)*\s*""")/gs, '<span class="string">$1</span>')
      // Comments
      .replace(/(#.*)$/gm, '<span class="comment">$1</span>')
      // Types
      .replace(/\b(str|int|float|bool|list|dict|tuple|set|Optional|List|Dict|Any|UUID|datetime|date)\b/g, '<span class="type">$1</span>')
      // Function definitions
      .replace(/\b(def\s+)(\w+)/g, '$1<span class="function">$2</span>');
    
    return highlighted;
  }
  
  render() {
    if (!this.code) {
      return html`
        <div class="code-container">
          <div class="placeholder">
            No code generated yet. Create and save a model first.
          </div>
        </div>
      `;
    }
    
    const entityNames = Object.keys(this.code.entities || {});
    
    return html`
      <div class="code-container">
        <div class="code-tabs">
          <div class="code-tab ${this.activeTab === 'entities' ? 'active' : ''}" 
               @click=${() => this.changeTab('entities')}>
            Entities
          </div>
          <div class="code-tab ${this.activeTab === 'repositories' ? 'active' : ''}" 
               @click=${() => this.changeTab('repositories')}>
            Repositories
          </div>
          <div class="code-tab ${this.activeTab === 'services' ? 'active' : ''}" 
               @click=${() => this.changeTab('services')}>
            Services
          </div>
        </div>
        
        <div class="entity-tabs">
          ${entityNames.map(entityName => html`
            <div class="entity-tab ${this.activeEntity === entityName ? 'active' : ''}" 
                 @click=${() => this.changeEntity(entityName)}>
              ${entityName}
            </div>
          `)}
        </div>
        
        <div class="code-header">
          <p class="file-path">${this.getFilePathForActiveTab()}</p>
          <button class="copy-button" @click=${this.copyCode}>Copy Code</button>
        </div>
        
        <div class="code-content">
          <pre>${this.getActiveCode() ? html`<code>${this.highlightSyntax(this.getActiveCode())}</code>` : 'No code available'}</pre>
        </div>
      </div>
    `;
  }
}