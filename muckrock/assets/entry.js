// Vite module preload polyfill
import "vite/modulepreload-polyfill";

// Make jQuery available globally for legacy code FIRST.
// This MUST be imported before muckrock.js because ES modules evaluate
// in dependency order — jquery-global.js will run before muckrock.js.
import './jquery-global.js';

// Import styles (doesn't depend on jQuery)
import './scss/style.scss'

// Static import so the full module graph (including fine-uploader which sets
// window.qq) loads as part of this module's dependency tree. This ensures
// inline <script type="module"> tags in templates execute AFTER all globals
// are available.
import './js/muckrock.js'
