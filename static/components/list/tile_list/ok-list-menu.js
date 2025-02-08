import {
  LitElement,
  css,
  html,
  until,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKListMenu extends LitElement {
  static properties = {
    listTitle: { type: String },
    pagination: { type: Object },
    formUrl: { type: Object },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
        overscroll-behavior: none;
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
  }

  _openDrawer(e) {
    let okSelectListMenuDrawerTab = new CustomEvent(
      "ok-select-list-menu-drawer-tab",
      {
        detail: { selectedTab: e.column.label },
        bubbles: true,
        composed: true,
      }
    );
    this.dispatchEvent(okSelectListMenuDrawerTab);
  }

  _openDialog(e) {
    this.renderRoot.querySelector("ok-dialog").open = true;
  }

  render() {
    return html`
      <div class="menu">
        <div class="justify">
          <span>${this.listTitle ? html`${this.listTitle}` : nothing}</span>
          <span>
            <sl-tooltip content="Create New">
              <sl-icon-button
                name="plus-circle"
                @click=${this._openDialog}
                label="Create New"
              ></sl-icon-button>
            </sl-tooltip>
            <ok-dialog
              .formUrl=${this.formUrl}
              backdrop="static"
              hide-footer
            ></ok-dialog>
            <sl-tooltip content="Sort Table">
              <sl-icon-button
                name="arrow-down-up"
                @click=${this._openDrawer}
                label="Sort Table"
              ></sl-icon-button>
            </sl-tooltip>
            <sl-tooltip content="Filter Table">
              <sl-icon-button
                name="filter-circle"
                @click=${this._openDrawer}
                label="Filter Table"
              ></sl-icon-button>
            </sl-tooltip>
            <sl-tooltip content="Table Queries">
              <sl-icon-button
                name="database-check"
                @click=${this._openDrawer}
                label="Table Queries"
              ></sl-icon-button>
            </sl-tooltip>
            <sl-tooltip content="Table Actions">
              <sl-icon-button
                name="toggles"
                @click=${this._openDrawer}
                label="Table Actions"
              ></sl-icon-button>
            </sl-tooltip>
          </span>
        </div>
        <ok-list-pagination
          .pagination=${this.pagination}
          listTitle=${this.listTitle}
        ></ok-list-pagination>
      </div>
    `;
  }
}

customElements.define("ok-list-menu", OKListMenu);
