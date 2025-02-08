import {
  LitElement,
  css,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKToolbar extends LitElement {
  static properties = {
    theme: {},
    authenicationUrl: { type: String },
    accessToken: { type: String },
    refreshToken: { type: String },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      #toolbar {
        padding: 0.5rem;
        margin-bottom: 0.25rem;
        display: flex;
        justify-content: space-between;
        z-index: 10;
        background: var(--sl-color-neutral-200);
        border-bottom-left-radius: calc(var(--docs-border-radius) * 2);
        border-bottom-right-radius: calc(var(--docs-border-radius) * 2);
      }
    `,
  ];

  constructor() {
    super();
  }

  // Render the UI as a function of component state
  render() {
    return html`
      <div id="toolbar">
        <div>
          <ok-menu-button></ok-menu-button>
          <img src="/static/assets/images/logo-light.png" alt="OPPI: Operations Ledger "style="height:1.5em; vertical-align:sub;"></img>
        </div>
        <div>
          <ok-user-menu></ok-user-menu>
        </div>
      </div>
    `;
  }
}
customElements.define("ok-header", OKToolbar);
