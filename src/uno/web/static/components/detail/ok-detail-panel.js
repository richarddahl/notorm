import {
  LitElement,
  css,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKDetailPanel extends LitElement {
  static properties = {};

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
        padding: 0.75rem;
        padding-left: 1rem;
        padding-right: 1rem;
        background: var(--sl-color-neutral-200);
        width: 60vw;
      }
    `,
  ];

  constructor() {
    super();
  }

  // Render the UI as a function of component state
  render() {
    return html` Object Detail `;
  }
}

customElements.define("ok-detail-panel", OKDetailPanel);
