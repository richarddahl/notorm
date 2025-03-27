import {
  LitElement,
  css,
  html,
  until,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { getData } from "/static/assets/scripts/apiData.js";

export class OKFilterTile extends LitElement {
  static properties = {
    filter: { type: Object },
    open: { type: Boolean },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      sl-details {
        margin-bottom: 0.25rem;
      }
    `,
  ];

  constructor() {
    super();
    this.filterURL = "";
    this.open = false;
  }

  firstUpdated() {
    this.filterURL = this.filter.url;
  }

  _handleGetDetail(e) {
    this.open = true;
  }

  // Render the UI as a function of component state
  render() {
    return html`
      <sl-details @sl-show=${this._handleGetDetail}>
        <div slot="summary" class="summary">${this.filter.label}</div>
        <ok-filter-tile-detail
          .filterUrl=${this.filter.url}
          .open=${this.open}
        ></ok-filter-tile-detail>
      </sl-details>
    `;
  }
}

customElements.define("ok-filter-tile", OKFilterTile);
