// Vite module preload polyfill
import "vite/modulepreload-polyfill";

// Make jQuery available globally for inline <script type="module"> tags in
// templates. Bundled JS files import jQuery directly and don't need this.
import jQuery from "jquery";
window.$ = window.jQuery = jQuery;

// Import styles
import './scss/style.scss'

// Static import so the full module graph (including fine-uploader which sets
// window.qq) loads as part of this module's dependency tree. This ensures
// inline <script type="module"> tags in templates execute AFTER all globals
// are available.
import './js/muckrock.js'
