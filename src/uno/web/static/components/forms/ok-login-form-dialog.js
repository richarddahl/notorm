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
      sl-input::part(help-text) {
        margin-top: 1rem;
      }
    `,
  ];

  constructor() {
    super();
    this.emailHelpText = html`Please enter your email address`;
    this.passwordHelpText = html`Please enter your password`;
    this.formInvalid = false;
  }

  firstUpdated() {
    this.email = this.shadowRoot.querySelector(".username");
    this.password = this.shadowRoot.querySelector(".password");

    this.email.addEventListener("input", (e) => {
      this._checkEmailValidation();
    });
    this.password.addEventListener("input", (e) => {
      this._checkPasswordValidation();
    });
    // This is needed to get the emailError and passwordError
    // properties to update, will not fire nothing has changed
    // i.e. there are no errors
    this.requestUpdate();
  }

  // called from external script to show the dialog
  showDialog() {
    this.shadowRoot.querySelector("sl-dialog").show();
  }

  _checkEmailValidation() {
    if (!this.email.validity.valid) {
      this.emailError = html`
        <ok-form-input-validation-error
          .error=${this.email.validationMessage}
          .helptText=${this.emailHelpText}
          open
        ></ok-form-input-validation-error>
      `;
      this.formInvalid = true;
    } else {
      this.emailError = undefined;
      this.formInvalid = false;
    }
  }

  _checkPasswordValidation() {
    if (!this.password.validity.valid) {
      this.passwordError = html`
        <ok-form-input-validation-error
          .error=${this.password.validationMessage}
          .helptText=${this.passwordHelpText}
          open
        ></ok-form-input-validation-error>
      `;
      this.formInvalid = true;
    } else {
      this.passwordError = undefined;
      this.formInvalid = false;
    }
  }

  async _handleLogin(e) {
    e.preventDefault();
    const dialog = this.shadowRoot.querySelector("sl-dialog");
    const form = this.shadowRoot.querySelector("#loginForm");
    let formData;
    this.error = false;

    this._checkEmailValidation();
    this._checkPasswordValidation();
    if (this.formInvalid) {
      return;
    }

    formData = new FormData(form);

    if (await login(formData)) {
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

          <sl-input
            form="loginForm"
            class="username"
            label="Email"
            name="username"
            type="email"
            clearable
            required
            autocomplete="username"
            autofocus
          >
            <sl-icon name="envelope" slot="prefix"></sl-icon>
            <div slot="help-text">${this.emailError || this.emailHelpText}</div>
          </sl-input>
          <sl-input
            form="loginForm"
            class="password"
            label="Password"
            name="password"
            type="password"
            password-toggle
            minlength="12"
            maxlength="120"
            clearable
            required
            autocomplete="current-password"
          >
            <sl-icon name="key" slot="prefix"></sl-icon>
            <div slot="help-text">
              ${this.passwordError || this.passwordHelpText}
            </div>
          </sl-input>
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
