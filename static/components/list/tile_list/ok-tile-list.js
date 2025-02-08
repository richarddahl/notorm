import {
  LitElement,
  css,
  html,
  until,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { getData } from "/static/assets/scripts/apiData.js";

export class OKTileList extends LitElement {
  static properties = {
    listTitle: { type: String },
    dataUrl: { type: Object },
    filterUrl: { type: Object },
    sortingUrl: { type: Object },
    queryUrl: { type: Object },
    formUrl: { type: Object },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
        overscroll-behavior: none;
        position: relative;
      }
      .list {
        height: 79%;
        overflow-y: auto;
      }
      sl-details {
        margin-bottom: 0.25rem;
      }
      .justify {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .justify span {
        font-size: var(--sl-font-size-medium);
        font-weight: var(--sl-font-weight-semibold);
        color: var(--sl-color-neutral-500);
      }
    `,
  ];

  constructor() {
    super();
    this.drawerTab = "Sort Table";
    this.queryParamList = [];
    this.addEventListener("ok-page-change", (e) => {
      this.dataUrl.searchParams.set("page", e.detail.page);
      this.requestUpdate();
    });

    this.addEventListener("ok-limit-change", (e) => {
      this.dataUrl.searchParams.set("limit", e.detail.limit);
      this.dataUrl.searchParams.set("page", 1);
      this.requestUpdate();
    });

    this.addEventListener("ok-select-list-menu-drawer-tab", (e) => {
      this.renderRoot.querySelector("ok-tile-list-drawer").drawerTab =
        e.detail.selectedTab;
      this.renderRoot.querySelector("ok-tile-list-drawer")._show();
    });
  }

  render() {
    if (this.queryParamList) {
      let queryString = "";
      this.queryParamList.forEach(function (queryParam, index) {
        if (index == 0) {
          queryString = `${queryParam.queryString}`;
        } else {
          queryString = `${queryString}&${queryParam.queryString}`;
        }
      });
    }
    return html`
      ${until(
        this._render(),
        html`<ok-loading-notification></ok-loading-notification>`
      )}
    `;
  }
  // Render the UI as a function of component state
  async _render() {
    const data = await getData(this.dataUrl);
    return html`
      <ok-list-menu
        listTitle=${this.listTitle}
        .pagination=${data.pagination}
        .formUrl=${this.formUrl}
      ></ok-list-menu>
      <div class="list">
        ${data.items.map((item) => html` <ok-tile .item="${item}"></ok-tile> `)}
      </div>
      <ok-tile-list-drawer
        listTitle="${this.listTitle}"
        .filterUrl="${this.filterUrl}"
        .sortingUrl="${this.sortingUrl}"
        .queryUrl="${this.queryUrl}"
        .drawerTab="${this.drawerTab}"
      ></ok-tile-list-drawer>
    `;
  }
}

customElements.define("ok-tile-list", OKTileList);
