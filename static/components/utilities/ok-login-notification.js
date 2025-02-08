import {
  LitElement,
  css,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKLoginNotification extends LitElement {
  /*
  renders an icon within a padded div to provide user guidance that data is being loaded
  */

  static styles = [
    css`
      :host {
        color: var(--sl-color-danger-600);
        text-align: center;
        padding: 2rem;
        margin-top: 1rem;
        font-family: var(--sl-font-sans);
        font-weight: var(--sl-font-weight-semibold);
      }
      sl-icon-button {
        font-size: var(--sl-font-size-2x-large);
        color: var(--sl-color-danger-600);
      }
    `,
  ];

  constructor() {
    super();
  }

  _showLoginDialog = (e) => {
    /*
    const formDialog = document.querySelector('ok-login-form-dialog');
    formDialog.open = true;
    formDialog.requestUpdate();
    */
    const loginEvent = new CustomEvent("ok-prompt-login", {
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(loginEvent);
  };

  // Render the UI as a function of component state
  render() {
    return html`
      <div>
        <sl-icon-button
          name="box-arrow-in-right"
          @click=${this._showLoginDialog}
        ></sl-icon-button>
        <div>You must login</div>
      </div>
    `;
  }
}
customElements.define("ok-login-notification", OKLoginNotification);
