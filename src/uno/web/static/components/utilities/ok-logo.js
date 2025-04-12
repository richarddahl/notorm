import {
  LitElement,
  css,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKLogo extends LitElement {
  static properties = {
    logoHref: {},
    logoAlt: {},
    logoSrcLight: {},
    logoSrcDark: {},
    tagline: {},
    theme: {},
  };

  static styles = [
    css`
      img {
        object-fit: contain;
        max-width: 100%;
        height: auto;
      }
      div {
        text-align: right;
        font-family: var(--sl-font-sans);
        opacity: 50%;
        font-size: 0.9em;
      }
    `,
  ];

  constructor() {
    super();
  }

  // Render the UI as a function of component state
  render() {
    let logoSrc;
    if (this.theme == "dark") {
      logoSrc = this.logoSrcDark;
    } else {
      logoSrc = this.logoSrcLight;
    }
    return html`
      <a href="${this.logoHref}">
        <img src="${logoSrc}" alt="${this.logoAlt}"></img>
      </a>
      <div>${this.tagline}</div>
    `;
  } // end render
}

customElements.define("ok-logo", OKLogo);
