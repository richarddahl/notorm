import {
  LitElement,
  css,
  html,
  until,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";
import { getData } from "/static/assets/scripts/apiData.js";

export class OKListActionMenu extends LitElement {
  static properties = {
    anySelected: { type: Boolean },
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
      }
    `,
  ];

  get _dropdown() {
    return this.renderRoot.querySelector("sl-dropdown");
  }

  constructor() {
    super();
  }

  render() {
    return html`
      <div>
        <sl-tooltip content="Expand All">
          <sl-icon-button
            value="expandAll"
            name="chevron-down"
            label="Expand All"
          ></sl-icon-button>
        </sl-tooltip>
        <span>Expand All</span>
      </div>
      <div>
        <sl-tooltip content="Collapse All">
          <sl-icon-button
            value="collapseAll"
            name="chevron-right"
            label="Collapse All"
          ></sl-icon-button>
        </sl-tooltip>
        <span>Collapse All</span>
      </div>
      <div>
        <sl-tooltip content="Select All">
          <sl-icon-button
            value="selectAll"
            name="toggle-on"
            label="Select All"
          ></sl-icon-button>
        </sl-tooltip>
        <span>Select All</span>
      </div>
      <div>
        <sl-tooltip content="Select None">
          <sl-icon-button
            value="selectNone"
            name="toggle-off"
            label="Select None"
          ></sl-icon-button>
        </sl-tooltip>
        <span>Select None</span>
      </div>
      <div>
        <sl-tooltip content="Delete Selected">
          <sl-icon-button
            value="deleteSelected"
            name="trash"
            label="Delete Selected"
          ></sl-icon-button>
        </sl-tooltip>
        <span>Delete Selected</span>
      </div>
      <div>
        <sl-tooltip content="Compare Selected">
          <sl-icon-button
            value="compareSelected"
            name="ui-checks"
            label="Compare Selected"
          ></sl-icon-button>
        </sl-tooltip>
        <span>Compare Selected</span>
      </div>
    `;
  }
}
customElements.define("ok-list-action-menu", OKListActionMenu);
