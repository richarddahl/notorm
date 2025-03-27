import {
  LitElement,
  css,
  html,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

export class OKFooter extends LitElement {
  static properties = {
    theme: {},
  };

  static styles = [
    css`
      :host {
        font-family: var(--sl-font-sans);
        padding: 0.75rem;
        padding-left: 1rem;
        padding-right: 1rem;
        background: var(--sl-color-neutral-200);
      }
      .justify {
        display: flex;
        justify-content: space-evenly;
      }
      .img {
        margin-bottom: 0.5rem;
        text-align: center;
      }
      a {
        text-decoration: none;
      }
      span > div {
        margin-bottom: 0.5rem;
      }
    `,
  ];

  constructor() {
    super();
  }

  // Render the UI as a function of component state
  render() {
    return html`
      <div class="img">
        <img
          src="/static/assets/images/logo-tagline-${this.theme}.png"
          width="200px"
        />
      </div>
      <div class="justify">
        <span>
          <div><a href="#">Home</a></div>
          <div><a href="#">Signup</a></div>
        </span>
        <span>
          <div><a href="#">Company</a></div>
          <div><a href="#">Contact</a></div>
        </span>
        <span>
          <div><a href="#">FAQ</a></div>
          <div><a href="#">About</a></div>
        </span>
      </div>
      <div style="text-align: center; margin-top: 1rem; color:brown;">
        &copy; 2021 OPPI LLC
      </div>
    `;
  }
}

customElements.define("ok-footer", OKFooter);
