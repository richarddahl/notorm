/**
 * Base module components
 * This file exports all components in the base module
 */

// Components to import with their element names for checking
const componentsToImport = [
  { path: './ok-base.js', name: 'ok-base' },
  { path: './ok-data-provider.js', name: 'ok-data-provider' },
  { path: './wa-data-provider.js', name: 'wa-data-provider' },
  { path: './wa-entity-list.js', name: 'wa-entity-list' },
  { path: './header/ok-header.js', name: 'ok-header' },
  { path: './header/ok-user-menu.js', name: 'ok-user-menu' },
  { path: './footer/ok-footer.js', name: 'ok-footer' },
  { path: './menu/ok-menu.js', name: 'ok-menu' },
  { path: './menu/ok-menu-button.js', name: 'ok-menu-button' }
];

// Import components only if not already registered
for (const component of componentsToImport) {
  if (!customElements.get(component.name)) {
    import(component.path)
      .then(() => console.log(`Component ${component.name} loaded`))
      .catch(err => console.error(`Error loading ${component.name}:`, err));
  } else {
    console.log(`Component ${component.name} already registered`);
  }
}

console.log('Base components initialization complete');