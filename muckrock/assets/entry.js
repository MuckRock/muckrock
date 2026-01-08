// Vite module preload polyfill
import "vite/modulepreload-polyfill";

// Make jQuery available globally for legacy code FIRST
import jQuery from "jquery";
window.$ = window.jQuery = jQuery;

// Import styles (doesn't depend on jQuery)
import './scss/style.scss'

// Use dynamic import to ensure jQuery is set up before muckrock.js loads
import('./js/muckrock.js')
