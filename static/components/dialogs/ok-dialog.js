import {
  LitElement,
  css,
  html,
  until,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { getData } from "/static/assets/scripts/apiData.js";

export class OKDialog extends LitElement {
  static properties = {
    formUrl: { type: Object },
    open: { type: Boolean },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      sl-dialog {
        --width: 50vw;
      }
      sl-dialog div {
        min-height: 20vh;
      }
    `,
  ];

  constructor() {
    super();
  }

  render() {
    if (this.open) {
      return html` ${until(this._render(), html``)} `;
    }
  }

  // Render the UI as a function of component state
  async _render() {
    const schema = await getData(this.formUrl);
    return html`
      <sl-dialog
        open=${this.open || nothing}
        label="Create New ${schema.title}"
      >
        <div>
          <ok-form .schema="${schema}"></ok-form>
        </div>
      </sl-dialog>
    `;
  }
}

customElements.define("ok-dialog", OKDialog);
