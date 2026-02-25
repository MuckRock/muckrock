// Make jQuery available globally for third-party jQuery plugins (formBuilder,
// jquery-ui, tooltipster, etc.) that expect `jQuery` / `$` on `window`.
//
// ES module `import` declarations are hoisted, so `window.jQuery = ...` in a
// module's body runs AFTER all imports have been evaluated.  By isolating the
// assignment in its own module we guarantee it executes before any plugin that
// is imported after this one in the dependency graph.
import jQuery from 'jquery';
window.$ = window.jQuery = jQuery;
