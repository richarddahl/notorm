/*
Provides a tile to display information in a list or similar widget.
*/
import {
  LitElement,
  css,
  html,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { login } from "/static/assets/scripts/apiData.js";

export class OKLoginFormDialog extends LitElement {
  static properties = {
    open: { type: Boolean },
    siteName: { type: String },
    error: { type: Boolean },
    emailError: { type: String },
    passwordError: { type: String },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
        display: -webkit-flex;
        display: flex;
        -webkit-align-items: center;
        align-items: center;
        -webkit-justify-content: center;
        justify-content: center;
      }
      form {
        padding: 1rem;
      }
      sl-input {
        display: block;
        margin-bottom: 1rem;
      }
      sl-alert {
        margin-bottom: 1rem;
      }
      sl-button {
        margin-top: 0.5rem;
        margin-left: auto;
      }
      label {
        margin-bottom: 1rem;
      }
      .help-text {
        margin-bottom: 1rem;
        margin-top: 0.5rem;
        font-size: var(--sl-font-size-small);
        color: var(--sl-color-gray-500);
      }
      .custom-input {
        display: block;
        width: 100%;
        padding: 0.375rem 0.75rem;
        font-size: 1rem;
        line-height: 1.5;
      }
      .custom-input:focus {
        border-color: #80bdff;
        outline: 0;
      }
    `,
  ];

  constructor() {
    super();
    this.emailHelpText = html`Please enter your email address`;
    this.passwordHelpText = html`Please enter your password`;
  }

  firstUpdated() {
    this.email = this.shadowRoot.querySelector(".username");
    this.password = this.shadowRoot.querySelector(".password");
    this.email.addEventListener("input", (e) => {
      if (!this.email.validity.valid) {
        this.emailError = html`
          <ok-form-input-validation-error
            .error=${this.email.validationMessage}
            .helpText=${this.emailHelpText}
            open
          ></ok-form-input-validation-error>
        `;
      }
    });
    this.password.addEventListener("input", (e) => {
      if (!this.password.validity.valid) {
        this.passwordError = html`
          <ok-form-input-validation-error
            .error=${this.password.validationMessage}
            .helpText=${this.passwordHelpText}
            open
          ></ok-form-input-validation-error>
        `;
      }
    });
    this.requestUpdate();
  }

  showDialog() {
    this.shadowRoot.querySelector("sl-dialog").show();
  }

  async _handleLogin(e) {
    e.preventDefault();
    const dialog = this.shadowRoot.querySelector("sl-dialog");
    const form = this.shadowRoot.querySelector("#loginForm");
    let formData;
    let invalid = false;
    this.error = false;

    if (!this.email.validity.valid) {
      this.emailError = html`
        <ok-form-input-validation-error
          .error=${this.email.validationMessage}
          .helpText=${this.emailHelpText}
          open
        ></ok-form-input-validation-error>
      `;
      invalid = true;
    } else {
      this.emailError = undefined;
    }
    if (!this.password.validity.valid) {
      this.passwordError = html`
        <ok-form-input-validation-error
          .error=${this.password.validationMessage}
          .helpText=${this.passwordHelpText}
          open
        ></ok-form-input-validation-error>
      `;
      invalid = true;
    }
    if (invalid) {
      return;
    }

    formData = new FormData(form);

    if (await login(formData, form)) {
      dialog.hide();
    } else {
      this.error = true;
    }
  }

  _clearForm() {
    this.email.value = "";
    this.password.value = "";
    this.error = false;
  }

  render() {
    let error = undefined;
    if (this.error) {
      error = html`
        <sl-alert variant="danger" open>
          <sl-icon slot="icon" name="exclamation-octagon"></sl-icon>
          <strong>Invalid Credentials</strong><br />
          Please try again.
        </sl-alert>
      `;
    }

    return html`
      <sl-dialog
        @sl-hide=${this._clearForm}
        @sl-show=${this._clearForm}
        label="Sign In to ${this.siteName}"
        open=${this.open || nothing}
      >
        <form id="loginForm" action="/" method="post" autocomplete="on">
          ${error || nothing}
          <label for="username">Email *</label>
          <input
            id="username"
            class="custom-input username"
            type="email"
            name="username"
            autocomplete="username"
            required
          />
          <div class="help-text">${this.emailError || this.emailHelpText}</div>
          <label for="password">Password *</label>
          <input
            id="password"
            class="custom-input password"
            type="password"
            name="password"
            autocomplete="current-password"
            minlength="12"
            maxlength="120"
            required
          />
          <div class="help-text">
            ${this.passwordError || this.passwordHelpText}
          </div>
        </form>
        <sl-button
          slot="footer"
          variant="primary"
          @click=${this._handleLogin}
          type="Submit"
          >Sign in
        </sl-button>
      </sl-dialog>
    `;
  }
}

customElements.define("ok-login-form-dialog", OKLoginFormDialog);
