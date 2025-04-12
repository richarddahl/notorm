import {
  LitElement,
  css,
  html,
  until,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { getData } from "/static/assets/scripts/apiData.js";

export class OKTileDetail extends LitElement {
  static properties = {
    obj_id_uri: { type: String },
    obj_id: { type: String },
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
        margin-right: 0.5rem;
      }
    `,
  ];

  constructor() {
    super();
    this.open = false;
  }

  /**
   * Converts a string to title case.
   *
   * @param {string} str - The string to convert.
   * @returns {string} The converted string in title case.
   */
  _convertKey(str) {
    if (!str) {
      return "";
    }
    return str
      .replace(/_/g, " ")
      .replace(/\b\w/g, (match) => match.toUpperCase());
  }

  /**
   * Converts a string value to a formatted date or number.
   * If the string can be parsed as a valid date, it returns the date in a localized string format.
   * If the string can be parsed as a valid number, it returns the number in a localized string format.
   * Otherwise, it returns the original string.
   *
   * @param {string} str - The string value to be converted.
   * @returns {string} The converted value.
   */
  _convertValue(value) {
    const date = new Date(value);
    const number = new Number(value);

    if (
      value === true ||
      value === false ||
      value === "true" ||
      value === "false"
    ) {
      return value ? "Yes" : "No";
    }

    if (number instanceof Number && !isNaN(number)) {
      return html`<sl-format-number value=${number}></sl-format-number>`;
    }

    if (date instanceof Date && !isNaN(date)) {
      return html`
        <sl-format-date
          hour="numeric"
          minute="numeric"
          month="numeric"
          day="numeric"
          year="numeric"
        ></sl-format-date>
      `;
    }

    if (typeof value === "object" && value.currency) {
      return html`
        <sl-format-number
          type="currency"
          currency="${value.currency}"
          value="${value.amount}"
          lang="en-US"
        ></sl-format-number>
      `;
    }

    if (typeof value === "object" && value !== null) {
      return value.title || "Title not found";
    }

    return value;
  }

  /**
   * Renders the tile detail component.
   * If the component is open, it renders the content returned by _render() method.
   * If the component is closed, it renders "NO DETAIL YET".
   * @returns {TemplateResult} The rendered HTML template.
   */
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

  /**
   * Renders the tile detail by fetching data from the API and generating HTML markup.
   * @returns {Promise<string>} The HTML markup representing the tile detail.
   */
  async _render() {
    const data = await getData(`${this.obj_id_uri}`);
    const items = Object.entries(data).reduce((acc, [key, value]) => {
      if (
        !["obj_id", "list_url", "obj_id_uri", "title", "summary"].includes(key)
      ) {
        const convertedKey = this._convertKey(key);
        const convertedValue = this._convertValue(value);
        acc.push({ key: convertedKey, value: convertedValue });
      }
      return acc;
    }, []);

    return html`
      <div>
        ${items.map(
          ({ key, value }) => html`
            <div class="row">
              <label>${key}:</label> <span class="label-value">${value}</span>
            </div>
          `
        )}
      </div>
    `;
  }
}
customElements.define("ok-tile-detail", OKTileDetail);
