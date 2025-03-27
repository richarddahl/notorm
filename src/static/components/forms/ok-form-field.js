/*
Provides a tile to display information in a list or similar widget.
*/
import {
  LitElement,
  css,
  html,
  choose,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKForm extends LitElement {
  static properties = {
    field: { type: Object },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      sl-button {
        margin-top: 0.5rem;
        margin-left: auto;
      }
      sl-input,
      sl-textarea,
      sl-checkbox,
      sl-select {
        margin-top: 0.5em;
      }
      sl-option::part(label) {
        font-size: var(--sl-font-size-small);
      }
      sl-tag .tag--medium {
        font-size: var(--sl-button-font-size-small);
        height: calc(var(--sl-input-height-small) * 0.8);
      }
    `,
  ];

  constructor() {
    super();
  }

  render() {
    return html`
      ${choose(
        this.field.value_type,
        [
          [
            "string",
            () => html`
              <sl-input
                size="small"
                label="${this.field.label}"
                name="${this.field.name}"
                help-text="${this.field.help_text}"
              ></sl-input>
            `,
          ],
          [
            "money",
            () => html`
              <sl-input
                size="small"
                label="${this.field.label}"
                name="${this.field.name}"
                value="${this.field.default}"
                type="currency"
                help-text="${this.field.help_text}"
              ></sl-input>
            `,
          ],
          [
            "integer",
            () => html`
              <sl-input
                size="small"
                label="${this.field.label}"
                name="${this.field.name}"
                value="${this.field.default}"
                type="number"
                help-text="${this.field.help_text}"
              ></sl-input>
            `,
          ],
          [
            "decimal",
            () => html`
              <sl-input
                size="small"
                label="${this.field.label}"
                name="${this.field.name}"
                value="${this.field.default}"
                type="number"
                help-text="${this.field.help_text}"
              ></sl-input>
            `,
          ],
          [
            "float",
            () => html`
              <sl-input
                size="small"
                label="${this.field.label}"
                name="${this.field.name}"
                value="${this.field.default}"
                type="number"
                help-text="${this.field.help_text}"
              ></sl-input>
            `,
          ],
          [
            "date",
            () => html`
              <sl-input
                size="small"
                label="${this.field.label}"
                name="${this.field.name}"
                value="${this.field.default}"
                type="date"
                help-text="${this.field.help_text}"
              ></sl-input>
            `,
          ],
          [
            "time",
            () => html`
              <sl-input
                size="small"
                label="${this.field.label}"
                name="${this.field.name}"
                value="${this.field.default}"
                type="time"
                help-text="${this.field.help_text}"
              ></sl-input>
            `,
          ],
          [
            "datetime",
            () => html`
              <sl-input
                size="small"
                label="${this.field.label}"
                name="${this.field.name}"
                value="${this.field.default}"
                type="datetime-local"
                help-text="${this.field.help_text}"
              ></sl-input>
            `,
          ],
          [
            "text",
            () => html`
              <sl-input
                size="small"
                label="${this.field.label}"
                name="${this.field.name}"
                value="${this.field.default}"
                help-text="${this.field.help_text}"
              ></sl-input>
            `,
          ],
          [
            "boolean",
            () => html`
              <sl-switch
                size="small"
                label="${this.field.label}"
                name="${this.field.name}"
                checked="${this.field.default || nothing}"
                help-text="${this.field.help_text}"
                >${this.field.label}</sl-switch
              >
            `,
          ],
          [
            "select",
            () => html`
              <sl-select
                hoist
                size="small"
                name="${this.field.name}"
                value="${this.field.default}"
                multiple="${this.field.multiple || nothing}"
                clearable=${!this.field.required || nothing}
                help-text="${this.field.help_text}"
              >
                <div slot="label">
                  <ok-list-menu
                    .dataUrl=${this.dataUrl}
                    .formUrl=${this.formUrl}
                    .sortingUrl=${this.sortingUrl}
                    .filterUrl=${this.filterUrl}
                  ></ok-list-menu>
                </div>
                ${this.field.options.map(
                  (option) => html`
                    <sl-option value="${option[0]}"> ${option[1]} </sl-option>
                  `
                )}
              </sl-select>
            `,
          ],
          [
            "model",
            () => html`
              <sl-select
                hoist
                size="small"
                name="${this.field.name}"
                value="${this.field.default}"
                multiple="${this.field.multiple || nothing}"
                clearable=${!this.field.required || nothing}
                help-text="${this.field.help_text}"
              >
                <div slot="label">
                  <ok-list-menu
                    .dataUrl=${this.field.dataUrl}
                    .formUrl=${this.field.formUrl}
                    .sortingUrl=${this.field.sortingUrl}
                    .filterUrl=${this.field.filterUrl}
                  ></ok-list-menu>
                </div>
                ${this.field.options.map(
                  (option) => html`
                    <sl-option value="${option[0]}"> ${option[1]} </sl-option>
                  `
                )}
              </sl-select>
            `,
          ],
        ],
        () => console.log(this.field)
      )}
    `;
  }
}

customElements.define("ok-form-field", OKForm);
