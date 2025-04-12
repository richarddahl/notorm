import {
  LitElement,
  css,
  html,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { haveToken, postData } from "/static/assets/scripts/apiData.js";

export class OKBase extends LitElement {
  static properties = {
    listTitle: { type: String },
    dataUrl: { type: Object },
    filterUrl: { type: Object },
    sortingUrl: { type: Object },
    queryUrl: { type: Object },
    formUrl: { type: Object },
    theme: { type: String },
    logged_in: { type: Boolean },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      .panel {
        height: 90vh;
        overflow-y: auto;
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.25rem;
      }
      ok-footer {
        display: block;
        height: fit-content;
      }
    `,
  ];

  _handleChangeTheme = (e) => {
    e.stopPropagation();
    const oldTheme = localStorage.getItem("theme");
    const theme = e.detail.message;
    if (theme == oldTheme) {
      return;
    }
    localStorage.setItem("theme", theme);
    document.documentElement.classList.add(`sl-theme-${theme}`);
    document.documentElement.classList.remove(`sl-theme-${oldTheme}`);
    this.theme = theme;
  };

  _handleAppMenuSelect = (e) => {
    this.listTitle = e.detail.selectedItem.getTextLabel().trim();
    this.dataUrl = new URL(
      `${window.location.origin}${e.detail.selectedItem.dataurl}`
    );
    this.filterUrl = new URL(
      `${window.location.origin}${e.detail.selectedItem.filterurl}`
    );
    this.sortingUrl = new URL(
      `${window.location.origin}${e.detail.selectedItem.sortingurl}`
    );
    this.queryUrl = new URL(
      `${window.location.origin}${e.detail.selectedItem.queryurl}`
    );
    this.formUrl = new URL(
      `${window.location.origin}${e.detail.selectedItem.formUrl}`
    );
  };

  constructor() {
    super();
    if (!this.logged_in) {
      this.logged_in = haveToken();
    }
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;
    this.theme = localStorage.getItem("theme") || "auto";
    document.documentElement.classList.toggle(
      "sl-theme-dark",
      this.theme === "dark" || (this.theme === "auto" && prefersDark)
    );
    // Responds to selection from app menu
    this.addEventListener("ok-select-menu-item", this._handleAppMenuSelect);
    // Responds to click from change theme button
    this.addEventListener("ok-change-theme", this._handleChangeTheme);
  }

  // Render the UI as a function of component state
  render() {
    if (this.logged_in) {
      return html`
        <ok-header></ok-header>
        <div class="panel">
          <ok-list-panel
            listTitle="${this.listTitle}"
            .dataUrl="${this.dataUrl}"
            .filterUrl="${this.filterUrl}"
            .sortingUrl="${this.sortingUrl}"
            .queryUrl="${this.queryUrl}"
            .formUrl="${this.formUrl}"
            theme="${this.theme}"
          ></ok-list-panel>
          <ok-detail-panel
            accessToken=${this.accessToken || nothing}
            refreshToken=${this.refreshToken || nothing}
            authenticationUrl=${this.authenticationUrl}
          ></ok-detail-panel>
        </div>
        <ok-footer theme="${this.theme}"></ok-footer>
      `;
    }
    return html` <ok-login-notification></ok-login-notification> `;
  }
}

customElements.define("ok-base", OKBase);
