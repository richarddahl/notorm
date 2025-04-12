import {
  LitElement,
  css,
  html,
  until,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKListPanel extends LitElement {
  /* 
  The overall container for the list of objects obtained from the API
  */

  static properties = {
    listTitle: { type: String },
    dataUrl: { type: Object },
    filterUrl: { type: Object },
    sortingUrl: { type: Object },
    queryUrl: { type: Object },
    formUrl: { type: Object },
    theme: { type: String },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
        padding: 0.75rem;
        padding-left: 1rem;
        padding-right: 1rem;
        background: var(--sl-color-neutral-200);
        border-bottom-left-radius: calc(var(--docs-border-radius) * 2);
        border-bottom-right-radius: calc(var(--docs-border-radius) * 2);
        width: 35vw;
        overflow: hidden;
      }
    `,
  ];

  constructor() {
    super();
  }

  // Render the UI as a function of component state
  render() {
    if (this.listTitle) {
      return html`
        <ok-tile-list
          .dataUrl="${this.dataUrl}"
          .filterUrl="${this.filterUrl}"
          .sortingUrl="${this.sortingUrl}"
          .queryUrl="${this.queryUrl}"
          .formUrl="${this.formUrl}"
          theme=${this.theme}
          listTitle="${this.listTitle}"
        ></ok-tile-list>
      `;
    } else {
      return html`<ok-placeholder theme=${this.theme}></ok-placeholder>`;
    }
  }
}

customElements.define("ok-list-panel", OKListPanel);
