import {
  LitElement,
  css,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKPlaceholder extends LitElement {
  static properties = {
    theme: {},
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
        text-align: center;
        color: var(--sl-color-neutral-500);
      }
      <h3>
        font-weight: 600;
      </h3>
    `,
  ];

  constructor() {
    super();
  }

  // Render the UI as a function of component state
  render() {
    return html`
      <div>
        <img src="/static/assets/images/logo-tagline-${this.theme}.png" />
        <h3>
          <span>You make Spirits or Liquors?</span>
        </h3>
        <h3>
          <span>You make Beer or Cider?</span>
        </h3>
        <h3>
          <span>You make Wine or Mead?</span>
        </h3>
        <h3>OPPI is the ledger for you.</h3>
        <div>
          <span>Click</span>
          <sl-icon name="three-dots-vertical"></sl-icon>
          <span>in the header to display the app menu</span>
        </div>
      </div>
    `;
  }
}

customElements.define("ok-placeholder", OKPlaceholder);
