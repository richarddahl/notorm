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

export class OKFListFilterForm extends LitElement {
  static properties = {
    filter: { type: Object },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
      form {
        padding: 0.5rem;
        background-color: var(--sl-color-neutral-100);
        margin-bottom: 0.5rem;
      }
      .formFieldGroup {
        display: flex;
        justify-content: space-between;
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
      .error::part(form-control-help-text) {
        color: var(--sl-color-danger-600);
      }
      .error::part(form-control-input) {
        border-color: var(--sl-color-danger-600);
      }
    `,
  ];

  constructor() {
    super();
  }

  firstUpdated() {
    const inputs = this.shadowRoot.querySelectorAll("sl-input");
    const textareas = this.shadowRoot.querySelectorAll("sl-textarea");
    const checkboxes = this.shadowRoot.querySelectorAll("sl-checkbox");
    const selects = this.shadowRoot.querySelectorAll("sl-select");
    inputs.forEach((input) => {
      input.addEventListener("input", (e) => {
        if (input.validity.valid) {
          input.classList.remove("error");
        } else {
          input.classList.add("error");
        }
      });
    });
  }

  _changeLookupListener(e) {
    e.stopPropagation();
    e.preventDefault();
    if (e.column.value == "isnull") {
      this.shadowRoot.querySelector(
        `#id_${this.filter.obj_id}`
      ).disabled = true;
    } else {
      this.shadowRoot.querySelector(
        `#id_${this.filter.obj_id}`
      ).disabled = false;
    }
  }

  render() {
    return html`
      <form>
        ${choose(
          this.filter.value_type,
          [
            [
              "string",
              () => html`
                <sl-input
                  id="id_${this.filter.obj_id}"
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.obj_id}"
                ></sl-input>
              `,
            ],
            [
              "money",
              () => html`
                <sl-input
                  id="id_${this.filter.obj_id}"
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.obj_id}"
                  value="${this.filter.initial}"
                  type="currency"
                ></sl-input>
              `,
            ],
            [
              "integer",
              () => html`
                <sl-input
                  id="id_${this.filter.obj_id}"
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.obj_id}"
                  value="${this.filter.initial}"
                  type="number"
                ></sl-input>
              `,
            ],
            [
              "decimal",
              () => html`
                <sl-input
                  id="id_${this.filter.obj_id}"
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.obj_id}"
                  value="${this.filter.initial}"
                  type="number"
                ></sl-input>
              `,
            ],
            [
              "float",
              () => html`
                <sl-input
                  id="id_${this.filter.obj_id}"
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.obj_id}"
                  value="${this.filter.initial}"
                  type="number"
                ></sl-input>
              `,
            ],
            [
              "date",
              () => html`
                <sl-input
                  id="id_${this.filter.obj_id}"
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.obj_id}"
                  value="${this.filter.initial}"
                  type="date"
                ></sl-input>
              `,
            ],
            [
              "time",
              () => html`
                <sl-input
                  id="id_${this.filter.obj_id}"
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.obj_id}"
                  value="${this.filter.initial}"
                  type="time"
                ></sl-input>
              `,
            ],
            [
              "datetime",
              () => html`
                <sl-input
                  id="id_${this.filter.obj_id}"
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.obj_id}"
                  value="${this.filter.initial}"
                  type="datetime-local"
                ></sl-input>
              `,
            ],
            [
              "text",
              () => html`
                <sl-input
                  id="id_${this.filter.obj_id}"
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.obj_id}"
                ></sl-input>
              `,
            ],
            [
              "boolean",
              () => html`
                <sl-switch
                  id="id_${this.filter.obj_id}"
                  size="small"
                  name="${this.filter.name}"
                  value="${this.filter.initial}"
                  >${this.filter.label}</sl-switch
                >
              `,
            ],
            [
              "select",
              () => html`
                <sl-select
                  id="id_${this.filter.obj_id}"
                  hoist
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.name}"
                  value="${this.filter.initial}"
                  multiple="true"
                  clearable="true"
                >
                  ${this.filter.value_options.map(
                    (option) => html`
                      <sl-option value="${option.value}">
                        ${option.label}
                      </sl-option>
                    `
                  )}
                </sl-select>
              `,
            ],
            [
              "model",
              () => html`
                <sl-select
                  id="id_${this.filter.obj_id}"
                  hoist
                  size="small"
                  label="${this.filter.label}"
                  name="${this.filter.name}"
                  value="${this.filter.initial}"
                  multiple="true"
                  clearable="true"
                >
                </sl-select>
              `,
            ],
          ],
          () => console.log(this.filter)
        )}
        <div class="formFieldGroup">
          <sl-select
            size="small"
            @sl-change="${this._changeLookupListener}"
            hoist
            name="${this.filter.obj_id}__lookup"
            value="${this.filter.lookups[0].value}"
          >
            ${this.filter.lookups.map(
              (lookup) =>
                html`
                  <sl-option value="${lookup.value}">${lookup.label}</sl-option>
                `
            )}
          </sl-select>
          <sl-select
            hoist
            size="small"
            name="${this.filter.obj_id}__include"
            value="include"
          >
            <sl-option value="include">Include</sl-option>
            <sl-option value="exclude">Exclude</sl-option>
          </sl-select>
        </div>
        <sl-select
          size="small"
          hoist
          name="${this.filter.name}__match"
          value="and"
        >
          <sl-option value="and">Match this filter AND ALL others</sl-option>
          <sl-option value="or">Match this filters OR ANY others</sl-option>
        </sl-select>
      </form>
    `;
  }
}

customElements.define("ok-list-filter-form", OKFListFilterForm);
