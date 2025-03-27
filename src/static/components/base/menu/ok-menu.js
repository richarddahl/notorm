import {
  LitElement,
  css,
  html,
  until,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { getData, haveToken } from "/static/assets/scripts/apiData.js";

export class OKNavigationMenu extends LitElement {
  static properties = {
    theme: {},
  };

  static styles = [
    css`
      :host {
        width: 100%;
      }
      sl-menu {
        border: none;
        border-radius: none;
      }
      sl-menu-label {
        color: var(--sl-color-primary-500);
      }
      sl-menu-item {
        padding-left: var(--sl-spacing-2x-small);
      }
    `,
  ];

  constructor() {
    super();
  }

  render() {
    return html`
      ${until(
        this._render(),
        html`<ok-loading-notification></ok-loading-notification>`
      )}
    `;
  }

  // Render the UI as a function of component state
  async _render() {
    if (!(await haveToken())) {
      return html`<ok-login-notification></ok-login-notification>`;
    }
    const jsonData = await getData(`/app/menu`);
    return html`
      <sl-menu>
        ${jsonData.map(
          (menu) =>
            html`
              <sl-divider></sl-divider>
              <sl-menu-label>${menu.module}</sl-menu-label>
              ${menu.models.map(
                (model) =>
                  html`<sl-menu-item
                    .module="${menu.module}"
                    .dataurl="${model.data_url}"
                    .filterurl="${model.filter_url}"
                    .sortingurl="${model.sorting_url}"
                    .queryurl="${model.query_url}"
                    .formUrl="${model.schema_url}"
                    .value="${model.value}"
                  >
                    ${model.name}
                  </sl-menu-item>`
              )}
            `
        )}
      </sl-menu>
    `;
  }
}

customElements.define("ok-menu", OKNavigationMenu);
