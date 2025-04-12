import {
  LitElement,
  css,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKLoadingNotification extends LitElement {
  /*
  renders an icon within a padded div to provide user guidance that data is being loaded
  */

  static styles = [
    css`
      sl-spinner {
        font-size: var(--sl-font-size-2x-large);
      }
      div {
        margin-top: 1rem;
        font-family: var(--sl-font-sans);
        font-size: var(--sl-font-size-small);
        font-weight: var(--sl-font-weight-semibold);
        line-height: var(--sl-line-height-normal);
        letter-spacing: var(--sl-letter-spacing-normal);
        color: var(--sl-color-neutral-500);
      }
    `,
  ];

  constructor() {
    super();
  }

  // Render the UI as a function of component state
  render() {
    return html`
      <div style="text-align: center; padding: 2rem;">
        <sl-spinner></sl-spinner>
        <div class="">Loading, please stand by...</div>
      </div>
    `;
  }
}
customElements.define("ok-loading-notification", OKLoadingNotification);
