import {
  LitElement,
  css,
  html,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { haveToken } from "/static/assets/scripts/apiData.js";

export class OKUserMenu extends LitElement {
  static properties = {
    theme: {},
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
    `,
  ];

  constructor() {
    super();
  }

  _changeTheme = (e) => {
    const theme = e.detail.item.value;
    let okChangeTheme = new CustomEvent("ok-change-theme", {
      detail: { message: theme },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(okChangeTheme);
  };

  // Render the UI as a function of component state
  render() {
    let userButton;
    let themeIcon = "sun";
    let theme = localStorage.getItem("theme");
    if (theme === null) {
      theme = "light";
    } else if (theme.match("dark")) {
      themeIcon = "moon";
    }
    this.addEventListener("sl-select", this._changeTheme);

    return html`
      <sl-icon-button name="person-circle" label="Profile"></sl-icon-button>
      <sl-icon-button name="box-arrow-right" label="Logout"></sl-icon-button>
      <sl-dropdown placement="bottom-end">
        <sl-icon-button
          slot="trigger"
          name="${themeIcon}"
          label="Select Theme"
        ></sl-icon-button>
        <sl-menu role="menu">
          <sl-menu-item value="light" aria-checked="false" tabindex="0">
            <sl-icon-button name="sun" label="Light"></sl-icon-button>
            Light
          </sl-menu-item>
          <sl-menu-item value="dark" aria-checked="false" tabindex="-1">
            <sl-icon-button name="moon" label="Dark"></sl-icon-button>
            Dark
          </sl-menu-item>
        </sl-menu>
      </sl-dropdown>
    `;
  }
}
customElements.define("ok-user-menu", OKUserMenu);
