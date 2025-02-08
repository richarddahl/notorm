/*
Provides a tile to display information in a list or similar widget.
*/
import {
  LitElement,
  css,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKFormInputValidationError extends LitElement {
  static properties = {
    open: { type: Boolean },
    error: { type: String },
    helpText: { type: String },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      sl-alert::part(message) {
        padding: var(--sl-spacing-small);
      }
    `,
  ];

  constructor() {
    super();
  }

  render() {
    if (this.open) {
      return html`
        <sl-alert class="short" input" variant="danger" open>
          <strong>${this.error}</strong><br />
            ${this.helpText}
        </sl-alert>
      `;
    }
  }
}

customElements.define(
  "ok-form-input-validation-error",
  OKFormInputValidationError
);
