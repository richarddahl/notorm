import {
  LitElement,
  css,
  html,
  until,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { getData } from "/static/assets/scripts/apiData.js";

export class OKFilterTileDetail extends LitElement {
  static properties = {
    filterUrl: { type: String },
    open: { type: Boolean },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      .row {
        margin-bottom: 0.5rem;
      }
      .row:last-child {
        margin-bottom: 0;
      }
      label {
        color: var(--sl-color-neutral-500);
      }
    `,
  ];

  constructor() {
    super();
    this.open = false;
  }

  _mapFilter(filter) {
    if (filter.children.length === 0) {
      return html`
        <ok-list-filter-form .filter="${filter}"></ok-list-filter-form>
      `;
    }
  }

  render() {
    if (this.open) {
      return html`
        ${until(
          this._render(),
          html`<ok-loading-notification></ok-loading-notification>`
        )}
      `;
    } else {
      return html`NO DETAIL YET`;
    }
  }

  async _render() {
    const filter = await getData(`${this.filterUrl}`);
    return html`
      <div>
        <ok-list-filter-form .filter="${filter}"></ok-list-filter-form>
      </div>
      ${filter.children.map((child) => html`${this._mapFilter(child)}`)}
    `;
  }
}
customElements.define("ok-filter-tile-detail", OKFilterTileDetail);
