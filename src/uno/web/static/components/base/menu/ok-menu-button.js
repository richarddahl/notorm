import {
  LitElement,
  css,
  html,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { haveToken } from "/static/assets/scripts/apiData.js";

export class OKNavigationMenuButton extends LitElement {
  static properties = {
    theme: {},
    haveToken: { type: Boolean },
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
    this.haveToken = haveToken();
    this.addEventListener("sl-select", this._selectMenuItem);
  }

  _showDrawer = (e) => {
    const drawer = this.renderRoot.querySelector("sl-drawer");
    if (!this.haveToken) {
      return false;
    }
    drawer.show();
  };

  _selectMenuItem = (e) => {
    const drawer = this.renderRoot.querySelector("sl-drawer");
    drawer.hide();
    let okSelectMenuItem = new CustomEvent("ok-select-menu-item", {
      detail: { selectedItem: e.detail.item },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(okSelectMenuItem);
  };

  // Render the UI as a function of component state
  render() {
    if (!this.haveToken) {
      this.opern = undefined;
    }
    return html`
      <sl-icon-button
        @click="${this._showDrawer}"
        name="three-dots-vertical"
        label="Menu"
      ></sl-icon-button>
      <sl-drawer open=${this.open || nothing} label="Menu" placement="start">
        <ok-menu theme="${this.theme}"></ok-menu>
      </sl-drawer>
    `;
  }
}
customElements.define("ok-menu-button", OKNavigationMenuButton);
