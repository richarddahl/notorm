import {
  LitElement,
  css,
  html,
  until,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { getData } from "/static/assets/scripts/apiData.js";

export class OKListSortMenu extends LitElement {
  static properties = {
    sorting: { type: Array },
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

  render() {
    return html`
      ${this.sorting.map(
        (sort) =>
          html`
            <div>
              <sl-tooltip content="Sort ${sort.label} Descending">
                <sl-icon-button
                  @click="${this._sortIconClicked}"
                  value="${sort.value}"
                  name="sort-down-alt"
                  label="Sort ${sort.label} Descending"
                ></sl-icon-button>
              </sl-tooltip>
              <sl-tooltip content="Sort ${sort.label} Ascending">
                <sl-icon-button
                  @click="${this._sortIconClicked}"
                  value="-${sort.value}"
                  name="sort-up-alt"
                  label="Sort ${sort.label} Ascending"
                ></sl-icon-button>
              </sl-tooltip>
              <span style="padding: var(--sl-spacing-2x-small);"
                >${sort.label}</span
              >
            </div>
          `
      )}
    `;
  }
}
customElements.define("ok-list-sort-menu", OKListSortMenu);
