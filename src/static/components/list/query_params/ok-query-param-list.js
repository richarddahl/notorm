import {
  LitElement,
  css,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKQueryParamList extends LitElement {
  static properties = {
    queryParamList: { type: Array },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      div {
        margin-bottom: 0.75rem;
      }
      sl-tag {
        margin-right: 0.25rem;
      }
    `,
  ];

  constructor() {
    super();
  }

  _removeQueryParam(e) {
    this.dispatchEvent(
      new CustomEvent("ok-remove-query-param", {
        bubbles: true,
        composed: true,
        detail: {
          index: e.column.getAttribute("index"),
        },
      })
    );
  }

  // Render the UI as a function of component state
  render() {
    if (this.queryParamList.length == 0) {
      return html` <sl-tag variant="neutral">No Filters or Sort</sl-tag> `;
    }
    return html`
      <div>
        ${this.queryParamList.map(
          (queryParam) => html`
            <sl-tag
              @sl-remove="${this._removeQueryParam}"
              index="${queryParam.index}"
              removable
              variant="primary"
            >
              ${queryParam.fieldLabel}
            </sl-tag>
          `
        )}
      </div>
    `;
  }
}

customElements.define("ok-query-param-list", OKQueryParamList);
