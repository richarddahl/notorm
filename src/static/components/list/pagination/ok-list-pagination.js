import {
  LitElement,
  css,
  html,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
export class OKListPagination extends LitElement {
  static properties = {
    listTitle: { type: String },
    pagination: { type: Object },
  };
  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
        font-size: var(--sl-input-help-text-font-size-medium);
      }
      .justify {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
        color: var(--sl-color-neutral-500);
      }
      sl-switch {
        margin-left: 0.5rem;
      }
      .help-text {
        margin-top: 1rem;
      }
      .label-on-left {
        --gap-width: 0.5rem;
      }
      .label-on-left::part(form-control) {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .label-on-left::part(form-control-label) {
        margin-right: var(--gap-width);
      }
      .label-on-left::part(form-control-help-text) {
        margin-left: var(--gap-width);
      }
      .label-on-left::part(input) {
        width: 5rem;
        padding: 0 var(--sl-spacing-x-small);
      }
      .label-on-left::part(input):hover:not(:focus) {
        border: 1px solid var(--sl-color-primary-200);
      }
      sl-range {
        --track-color-active: var(--sl-color-neutral-300);
        --track-color-inactive: var(--sl-color-neutral-300);
        --thumb-size: var(--sl-toggle-size-small);
        padding-left: 1rem;
        padding-right: 1rem;
      }
    `,
  ];
  constructor() {
    super();
  }
  /**
   * Lifecycle method called when the element is first updated.
   * @returns {Promise<void>}
   */
  async firstUpdated() {
    const range = this.renderRoot.querySelector("sl-range");
    range.tooltipFormatter = (value) => `Page ${value}`;
    await this.updateComplete;
    range.focus();
  }
  // Responds to change in limit
  _limitChangeListener(e) {
    const limit = e.column.value;
    const event = new CustomEvent("ok-limit-change", {
      bubbles: true,
      composed: true,
      detail: { limit: limit },
    });
    this.dispatchEvent(event);
  }
  // Responds to change in page number via page input or range slider
  _pageChangeListener(e) {
    const page = e.column.value;
    const event = new CustomEvent("ok-page-change", {
      bubbles: true,
      composed: true,
      detail: { page: page },
    });
    this.dispatchEvent(event);
  }
  _rangeChangeListener(e) {
    const range = this.shadowRoot.querySelector("sl-range");
    if (e.column.checked) {
      range.min = this.pagination.complete_page_range[0];
      range.max = this.pagination.complete_page_range[1];
      this.shadowRoot.querySelector(
        ".range-help-text"
      ).innerHTML = `Use Mouse or Arrow Keys to Select Pages
      ${this.pagination.complete_page_range[0]} -
      ${this.pagination.complete_page_range[1]}`;
    } else {
      range.min = this.pagination.default_page_range[0];
      range.max = this.pagination.default_page_range[1];
      this.shadowRoot.querySelector(
        ".range-help-text"
      ).innerHTML = `Use Mouse or Arrow Keys to Select Pages
      ${this.pagination.default_page_range[0]} -
      ${this.pagination.default_page_range[1]}`;
    }
  }
  // Render the UI as a function of component state
  render() {
    const switchState =
      this.pagination.complete_page_range[0] ==
        this.pagination.default_page_range[0] &&
      this.pagination.complete_page_range[1] ==
        this.pagination.default_page_range[1];
    const noPagination =
      this.pagination.default_page_range[0] ==
      this.pagination.default_page_range[1];
    return html`
      <div class="range">
        <div class="justify">
          <sl-input
            class="label-on-left"
            label="Page"
            size="small"
            type="number"
            no-spin-buttons
            min=${this.pagination.default_page_range[0]}
            max=${this.pagination.default_page_range[1]}
            disabled=${noPagination || nothing}
            placeholder="${this.pagination.page_number}"
            help-text="of ${this.pagination.page_count}"
            @sl-change=${this._pageChangeListener}
          ></sl-input>
          <sl-input
            class="label-on-left"
            label="Limit"
            size="small"
            type="number"
            no-spin-buttons
            min="1"
            max="1000"
            placeholder="${this.pagination.page_size}"
            help-text="${this.pagination.obj_start} to ${this.pagination
              .obj_end}
              of ${this.pagination.obj_count}"
            @sl-change=${this._limitChangeListener}
          ></sl-input>
        </div>
        <sl-range
          min="${this.pagination.default_page_range[0]}"
          max="${this.pagination.default_page_range[1]}"
          step="1"
          disabled=${noPagination || nothing}
          value="${this.pagination.page_number}"
          @sl-change=${this._pageChangeListener}
        ></sl-range>
        <div class="help-text" slot="help-text">
          <div class="justify">
            <span class="label range-help-text">
              Use Mouse or Arrow Keys to Select Pages
              ${this.pagination.default_page_range[0]} -
              ${this.pagination.default_page_range[1]}
            </span>
            <span class="label">
              All Pages in Slider
              <sl-switch
                size="small"
                class="label"
                checked=${switchState || nothing}
                disabled=${switchState || nothing}
                @sl-change=${this._rangeChangeListener}
              ></sl-switch>
            </span>
          </div>
        </div>
      </div>
    `;
  }
}
customElements.define("ok-list-pagination", OKListPagination);
