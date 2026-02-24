// This module MUST be imported before any module that uses window.$ or window.jQuery.
// ES modules evaluate in dependency order: since this is imported first in entry.js,
// it runs before muckrock.js and other modules that rely on the jQuery global.
import jQuery from "jquery";
window.$ = window.jQuery = jQuery;
