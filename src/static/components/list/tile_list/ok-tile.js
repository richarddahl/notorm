/*
Provides a tile to display information in a list or similar widget.
*/
import {
  LitElement,
  css,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKTile extends LitElement {
  static properties = {
    item: { type: Object },
    open: { type: Boolean },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      .title {
        font-weight: bold;
        margin-bottom: 0.25rem;
      }
      .summary {
        font-family: var(--sl-font-sans);
        font-size: var(--sl-font-size-small);
        font-weight: var(--sl-font-weight-semibold);
        line-height: var(--sl-line-height-normal);
        letter-spacing: var(--sl-letter-spacing-normal);
        color: var(--sl-color-neutral-500);
      }
      sl-card {
        display: block;
        margin-bottom: 0.5rem;
      }
      .card-header {
        display: flex;
        justify-content: space-between;
        margin-top: 0.25rem;
        margin-bottom: 0.25rem;
      }
    `,
  ];

  _handleGetDetail(e) {
    this.open = true;
  }

  constructor() {
    super();
    this.open = false;
  }

  // Render the UI as a function of component state
  render() {
    return html`
      <sl-card>
        <div class="card-header">
          ${this.item.title}
          <div style="display: flex; align-items: center !important;">
            <sl-tooltip content="Edit in Dialog">
              <sl-icon-button
                @click="${this._editClickListener}"
                name="pencil-square"
                label="Edit ${this.item.title} in Dialog"
              ></sl-icon-button>
            </sl-tooltip>
            <sl-tooltip content="Open In Detail Panel">
              <sl-icon-button
                @click="${this._detailClickListener}"
                name="arrow-right-square"
                label="Open ${this.item.title} in Detail Panel"
              ></sl-icon-button>
            </sl-tooltip>
            <sl-tooltip content="Delete">
              <sl-icon-button
                @click="${this._deleteClickListener}"
                name="trash3"
                label="Delete ${this.item.title}"
              ></sl-icon-button>
            </sl-tooltip>
            <sl-tooltip content="Select">
              <sl-switch
                label="select ${this.item.title}"
                size="small"
              ></sl-switch>
            </sl-tooltip>
          </div>
        </div>
        <sl-details
          summary=${this.item.summary}
          @sl-show=${this._handleGetDetail}
        >
          <ok-tile-detail
            obj_id_uri=${this.item.obj_id_uri}
            obj_id=${this.item.obj_id}
            .open=${this.open}
          ></ok-tile-detail>
        </sl-details>
      </sl-card>
    `;
  }
}

customElements.define("ok-tile", OKTile);
