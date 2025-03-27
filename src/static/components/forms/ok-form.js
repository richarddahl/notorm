/*
Provides a tile to display information in a list or similar widget.
*/
import {
  LitElement,
  css,
  html,
  choose,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKForm extends LitElement {
  static properties = {
    schema: { type: Object },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      form {
        padding: 0.5rem;
        margin-bottom: 0.5rem;
      }
      ok-form-field {
        display: block;
        margin-bottom: 1rem;
      }
      sl-button {
        margin-top: 0.5rem;
        margin-left: auto;
      }
      sl-input,
      sl-textarea,
      sl-checkbox,
      sl-select {
        margin-top: 0.5em;
      }
      sl-option::part(label) {
        font-size: var(--sl-font-size-small);
      }
    `,
  ];

  constructor() {
    super();
  }

  render() {
    return html`
      <form>
        ${this.schema.fields.map(
          (field) => html` <ok-form-field .field="${field}"></ok-form-field> `
        )}
      </form>
    `;
  }
}

customElements.define("ok-form", OKForm);
