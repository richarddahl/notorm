import {
  LitElement,
  css,
  html,
  until,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { getData } from "/static/assets/scripts/apiData.js";

export class OKTileListDrawer extends LitElement {
  static properties = {
    listTitle: { type: String },
    filterUrl: { type: String },
    sortingUrl: { type: String },
    open: { type: Boolean },
    drawerTab: { type: String },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      sl-details {
        margin-bottom: 0.25rem;
      }
      sl-drawer {
        --size: 90%;
      }
    `,
  ];

  constructor() {
    super();
    this.open = false;
  }

  _show() {
    this.open = true;
    this.requestUpdate();
  }

  _mapFilter(filter) {
    if (filter.children.length === 0) {
      return html`
        <ok-list-filter-form .filter="${filter}"></ok-list-filter-form>
      `;
    }
    return html`
      <ok-list-filter-form .filter="${filter}"></ok-list-filter-form>
      ${filter.children.map((child) => html`${this._mapFilter(child)}`)}
    `;
  }

  // Render the UI as a function of component state
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
    const filters = await getData(this.filterUrl);
    const sorting = await getData(this.sortingUrl);
    const queries = [];
    return html`
      <sl-drawer
        hoist
        contained
        open=${this.open || nothing}
        label="${this.listTitle}"
      >
        <sl-tab-group>
          <sl-tab
            slot="nav"
            active=${this.drawerTab == "Sort Table" ? true : nothing}
            panel="sort"
            >Sort</sl-tab
          >
          <sl-tab
            slot="nav"
            active=${this.drawerTab == "Filter Table" ? true : nothing}
            panel="filter"
            >Filter</sl-tab
          >
          <sl-tab
            slot="nav"
            active=${this.drawerTab == "Table Queries" ? true : nothing}
            panel="queries"
            >Queries</sl-tab
          >
          <sl-tab
            slot="nav"
            active=${this.drawerTab == "Table Actions" ? true : nothing}
            panel="actions"
            >Actions</sl-tab
          >

          <sl-tab-panel name="sort">
            <ok-list-sort-menu .sorting="${sorting}"></ok-list-sort-menu>
          </sl-tab-panel>

          <sl-tab-panel name="filter">
            ${filters.map(
              (filter) =>
                html`<ok-filter-tile .filter="${filter}"></ok-filter-tile>`
            )}
          </sl-tab-panel>

          <sl-tab-panel name="queries">
            <sl-menu>
              <sl-menu-item @click=${this._createNewListener}
                >Create Query From Filters</sl-menu-item
              >
              ${queries.map(
                (query) => html`<sl-menu-item>${query.label}</sl-menu-item>`
              )}
            </sl-menu>
          </sl-tab-panel>

          <sl-tab-panel name="actions">
            <ok-list-action-menu></ok-list-action-menu>
          </sl-tab-panel>
        </sl-tab-group>
      </sl-drawer>
    `;
  }
}

customElements.define("ok-tile-list-drawer", OKTileListDrawer);
