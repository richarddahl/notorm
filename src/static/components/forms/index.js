/**
 * Forms module components
 * This file exports all components in the forms module
 */

// Components to import with their element names for checking
const componentsToImport = [
  { path: './ok-form.js', name: 'ok-form' },
  { path: './ok-form-field.js', name: 'ok-form-field' },
  { path: './ok-form-input-validation-error.js', name: 'ok-form-input-validation-error' },
  { path: './ok-list-filter-form.js', name: 'ok-list-filter-form' },
  { path: './ok-login-form-dialog.js', name: 'ok-login-form-dialog' }
  // Note: ok-login-form-dialog-inputs.js is commented out as it tries to register the same component name
  // { path: './ok-login-form-dialog-inputs.js', name: 'ok-login-form-dialog' }
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

console.log('Form components initialization complete');