/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId])
/******/ 			return installedModules[moduleId].exports;
/******/
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			exports: {},
/******/ 			id: moduleId,
/******/ 			loaded: false
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.loaded = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(0);
/******/ })
/************************************************************************/
/******/ ([
/* 0 */
/***/ function(module, exports, __webpack_require__) {

	'use strict';

	__webpack_require__(1);

	__webpack_require__(20);

/***/ },
/* 1 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	__webpack_require__(3);
	
	__webpack_require__(4);
	
	__webpack_require__(5);
	
	__webpack_require__(6);
	
	__webpack_require__(7);
	
	__webpack_require__(8);
	
	__webpack_require__(9);
	
	__webpack_require__(10);
	
	__webpack_require__(11);
	
	__webpack_require__(12);
	
	__webpack_require__(13);
	
	__webpack_require__(14);
	
	__webpack_require__(15);
	
	__webpack_require__(16);
	
	__webpack_require__(17);
	
	__webpack_require__(18);
	
	__webpack_require__(19);
	
	function modal(nextSelector) {
	    var overlay = '#modal-overlay';
	    $(overlay).addClass('visible');
	    $(nextSelector).addClass('visible');
	    $(overlay).click(function () {
	        $(overlay).removeClass('visible');
	        $(nextSelector).removeClass('visible');
	    });
	    $('.close-modal').click(function () {
	        $(overlay).removeClass('visible');
	        $(nextSelector).removeClass('visible');
	    });
	}
	
	// MODALS
	$('.modal-button').click(function () {
	    modal($(this).next());
	});
	$('.embed.hidden-modal').each(function () {
	    var textarea = $(this).children('textarea');
	    var doc_id = textarea.data('docId');
	    var embed = '<div class="viewer" id="viewer-' + doc_id + '"></div> <script src="https://s3.amazonaws.com/s3.documentcloud.org/viewer/loader.js"><\/script> <script>DV.load("https://www.documentcloud.org/documents/' + doc_id + '.js", {width: 600, height: 600, sidebar: false, container: "#viewer-' + doc_id + '"});<\/script>';
	    textarea.val(embed);
	});
	
	// FLAG FORM
	$('#show-flag-form').click(function () {
	    var thisButton = $(this);
	    $(thisButton).hide();
	    var flagForm = $(this).next();
	    $(flagForm).addClass('visible').find('.cancel.button').click(function () {
	        $(thisButton).show();
	        $(flagForm).removeClass('visible');
	    });
	});
	
	// SELECT ALL
	$('#toggle-all').click(function () {
	    var toggleAll = this;
	    $(':checkbox').not('#toggle-all').each(function () {
	        $(this).click(function () {
	            toggleAll.checked = false;
	        });
	        if (!$(this).data('ignore-toggle-all')) {
	            this.checked = toggleAll.checked;
	        }
	    });
	});
	
	// Manager Component
	// A manager presents a state and a form that can modify that state.
	$('.edit').click(function () {
	    var editButton = this;
	    var manager = $(editButton).closest('.manager');
	    var form = $(manager).find('form');
	    var display = $(manager).find('.state');
	    $(form).addClass('visible');
	    $(display).hide();
	    $(editButton).hide();
	    $(manager).find('.cancel').click(function (e) {
	        e.preventDefault();
	        $(form).removeClass('visible');
	        $(display).show();
	        $(editButton).show();
	    });
	});
	
	// MESSAGES
	$('.message .visibility').click(function () {
	    var header = $(this).parent();
	    var message = header.siblings();
	    message.toggle();
	    if ($(this).hasClass('expanded')) {
	        $(this).removeClass('expanded').addClass('collapsed');
	        header.addClass('collapsed');
	        $(this).html('&#9654;');
	    } else {
	        $(this).removeClass('collapsed').addClass('expanded');
	        header.removeClass('collapsed');
	        $(this).html('&#9660;');
	    }
	});
	
	// DATEPICKER
	// Set defaults for datepicker plugin, and
	// bind it to elements with `.datepicker` class
	$('.datepicker').datepicker({
	    changeMonth: true,
	    changeYear: true,
	    minDate: new Date(1776, 6, 4),
	    maxDate: '+1y',
	    yearRange: '1776:+1'
	});
	
	// formsets
	$(function () {
	    $('.formset-container').formset();
	});
	
	function urlParam(sParam) {
	    var sPageURL = window.location.search.substring(1);
	    var sURLVariables = sPageURL.split('&');
	    for (var i = 0; i < sURLVariables.length; i++) {
	        var sParameterName = sURLVariables[i].split('=');
	        if (sParameterName[0] == sParam) {
	            return sParameterName[1];
	        }
	    }
	}
	
	$.expr[":"].icontains = $.expr.createPseudo(function (arg) {
	    return function (elem) {
	        return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
	    };
	});
	
	$('#sidebar-button').click(function (e) {
	    var overlay = '#modal-overlay';
	    var sidebar = '#website-sidebar';
	    $(sidebar).addClass('visible');
	    $(overlay).addClass('visible');
	    $(overlay).click(function (e) {
	        $(sidebar).removeClass('visible');
	        $(overlay).removeClass('visible');
	    });
	});
	
	function toggleNav(nav, button) {
	    $(nav).toggleClass('visible');
	    $(button).toggleClass('active');
	}
	
	function hideNav(nav, button) {
	    $(nav).removeClass('visible');
	    $(button).removeClass('active');
	}
	
	function selectAll(source, name) {
	    var checkboxes = $('input[type="checkbox"][name="' + name + '"]');
	    $(checkboxes).each(function () {
	        this.checked = source.checked;
	        $(this).change();
	    });
	}
	
	$('#show-sections').click(function () {
	    var button = this;
	    var sections = '#global-sections';
	    toggleNav(sections, button);
	});
	
	$('#show-search').click(function () {
	    var searchButton = this;
	    var search = '#global-search';
	    var closeSearch = '#hide-search';
	    var searchInput = $(search).children('input[type="search"]');
	    toggleNav(search, searchButton);
	    $(closeSearch).click(function () {
	        hideNav(search, searchButton);
	    });
	    if ($(search).hasClass('visible')) {
	        searchInput.focus();
	    } else {
	        searchInput.blur();
	    }
	});
	
	$('#quick-log-in').click(function (e) {
	    e.preventDefault();
	    var quickLogin = $('#quick-log-in-form');
	    quickLogin.addClass('visible');
	    quickLogin.find('input[type=text]')[0].focus();
	    quickLogin.find('.cancel').click(function () {
	        quickLogin.removeClass('visible');
	    });
	});
	
	// Stripe Checkout
	
	$('form.stripe-checkout').checkout();
	
	// Crowdfund form submission
	
	$('form.crowdfund-form').crowdfund();
	
	// Currency Field
	
	$('input.currency-field').currencyField();
	
	// Date Picker
	
	$(function () {
	    $('.datepicker').datepicker({
	        changeMonth: true,
	        changeYear: true,
	        minDate: new Date(1776, 6, 4),
	        maxDate: '+1y',
	        yearRange: '1776:+1'
	    });
	});
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 2 */
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/*!
	 * jQuery JavaScript Library v2.2.1
	 * http://jquery.com/
	 *
	 * Includes Sizzle.js
	 * http://sizzlejs.com/
	 *
	 * Copyright jQuery Foundation and other contributors
	 * Released under the MIT license
	 * http://jquery.org/license
	 *
	 * Date: 2016-02-22T19:11Z
	 */
	
	(function( global, factory ) {
	
		if ( typeof module === "object" && typeof module.exports === "object" ) {
			// For CommonJS and CommonJS-like environments where a proper `window`
			// is present, execute the factory and get jQuery.
			// For environments that do not have a `window` with a `document`
			// (such as Node.js), expose a factory as module.exports.
			// This accentuates the need for the creation of a real `window`.
			// e.g. var jQuery = require("jquery")(window);
			// See ticket #14549 for more info.
			module.exports = global.document ?
				factory( global, true ) :
				function( w ) {
					if ( !w.document ) {
						throw new Error( "jQuery requires a window with a document" );
					}
					return factory( w );
				};
		} else {
			factory( global );
		}
	
	// Pass this if window is not defined yet
	}(typeof window !== "undefined" ? window : this, function( window, noGlobal ) {
	
	// Support: Firefox 18+
	// Can't be in strict mode, several libs including ASP.NET trace
	// the stack via arguments.caller.callee and Firefox dies if
	// you try to trace through "use strict" call chains. (#13335)
	//"use strict";
	var arr = [];
	
	var document = window.document;
	
	var slice = arr.slice;
	
	var concat = arr.concat;
	
	var push = arr.push;
	
	var indexOf = arr.indexOf;
	
	var class2type = {};
	
	var toString = class2type.toString;
	
	var hasOwn = class2type.hasOwnProperty;
	
	var support = {};
	
	
	
	var
		version = "2.2.1",
	
		// Define a local copy of jQuery
		jQuery = function( selector, context ) {
	
			// The jQuery object is actually just the init constructor 'enhanced'
			// Need init if jQuery is called (just allow error to be thrown if not included)
			return new jQuery.fn.init( selector, context );
		},
	
		// Support: Android<4.1
		// Make sure we trim BOM and NBSP
		rtrim = /^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g,
	
		// Matches dashed string for camelizing
		rmsPrefix = /^-ms-/,
		rdashAlpha = /-([\da-z])/gi,
	
		// Used by jQuery.camelCase as callback to replace()
		fcamelCase = function( all, letter ) {
			return letter.toUpperCase();
		};
	
	jQuery.fn = jQuery.prototype = {
	
		// The current version of jQuery being used
		jquery: version,
	
		constructor: jQuery,
	
		// Start with an empty selector
		selector: "",
	
		// The default length of a jQuery object is 0
		length: 0,
	
		toArray: function() {
			return slice.call( this );
		},
	
		// Get the Nth element in the matched element set OR
		// Get the whole matched element set as a clean array
		get: function( num ) {
			return num != null ?
	
				// Return just the one element from the set
				( num < 0 ? this[ num + this.length ] : this[ num ] ) :
	
				// Return all the elements in a clean array
				slice.call( this );
		},
	
		// Take an array of elements and push it onto the stack
		// (returning the new matched element set)
		pushStack: function( elems ) {
	
			// Build a new jQuery matched element set
			var ret = jQuery.merge( this.constructor(), elems );
	
			// Add the old object onto the stack (as a reference)
			ret.prevObject = this;
			ret.context = this.context;
	
			// Return the newly-formed element set
			return ret;
		},
	
		// Execute a callback for every element in the matched set.
		each: function( callback ) {
			return jQuery.each( this, callback );
		},
	
		map: function( callback ) {
			return this.pushStack( jQuery.map( this, function( elem, i ) {
				return callback.call( elem, i, elem );
			} ) );
		},
	
		slice: function() {
			return this.pushStack( slice.apply( this, arguments ) );
		},
	
		first: function() {
			return this.eq( 0 );
		},
	
		last: function() {
			return this.eq( -1 );
		},
	
		eq: function( i ) {
			var len = this.length,
				j = +i + ( i < 0 ? len : 0 );
			return this.pushStack( j >= 0 && j < len ? [ this[ j ] ] : [] );
		},
	
		end: function() {
			return this.prevObject || this.constructor();
		},
	
		// For internal use only.
		// Behaves like an Array's method, not like a jQuery method.
		push: push,
		sort: arr.sort,
		splice: arr.splice
	};
	
	jQuery.extend = jQuery.fn.extend = function() {
		var options, name, src, copy, copyIsArray, clone,
			target = arguments[ 0 ] || {},
			i = 1,
			length = arguments.length,
			deep = false;
	
		// Handle a deep copy situation
		if ( typeof target === "boolean" ) {
			deep = target;
	
			// Skip the boolean and the target
			target = arguments[ i ] || {};
			i++;
		}
	
		// Handle case when target is a string or something (possible in deep copy)
		if ( typeof target !== "object" && !jQuery.isFunction( target ) ) {
			target = {};
		}
	
		// Extend jQuery itself if only one argument is passed
		if ( i === length ) {
			target = this;
			i--;
		}
	
		for ( ; i < length; i++ ) {
	
			// Only deal with non-null/undefined values
			if ( ( options = arguments[ i ] ) != null ) {
	
				// Extend the base object
				for ( name in options ) {
					src = target[ name ];
					copy = options[ name ];
	
					// Prevent never-ending loop
					if ( target === copy ) {
						continue;
					}
	
					// Recurse if we're merging plain objects or arrays
					if ( deep && copy && ( jQuery.isPlainObject( copy ) ||
						( copyIsArray = jQuery.isArray( copy ) ) ) ) {
	
						if ( copyIsArray ) {
							copyIsArray = false;
							clone = src && jQuery.isArray( src ) ? src : [];
	
						} else {
							clone = src && jQuery.isPlainObject( src ) ? src : {};
						}
	
						// Never move original objects, clone them
						target[ name ] = jQuery.extend( deep, clone, copy );
	
					// Don't bring in undefined values
					} else if ( copy !== undefined ) {
						target[ name ] = copy;
					}
				}
			}
		}
	
		// Return the modified object
		return target;
	};
	
	jQuery.extend( {
	
		// Unique for each copy of jQuery on the page
		expando: "jQuery" + ( version + Math.random() ).replace( /\D/g, "" ),
	
		// Assume jQuery is ready without the ready module
		isReady: true,
	
		error: function( msg ) {
			throw new Error( msg );
		},
	
		noop: function() {},
	
		isFunction: function( obj ) {
			return jQuery.type( obj ) === "function";
		},
	
		isArray: Array.isArray,
	
		isWindow: function( obj ) {
			return obj != null && obj === obj.window;
		},
	
		isNumeric: function( obj ) {
	
			// parseFloat NaNs numeric-cast false positives (null|true|false|"")
			// ...but misinterprets leading-number strings, particularly hex literals ("0x...")
			// subtraction forces infinities to NaN
			// adding 1 corrects loss of precision from parseFloat (#15100)
			var realStringObj = obj && obj.toString();
			return !jQuery.isArray( obj ) && ( realStringObj - parseFloat( realStringObj ) + 1 ) >= 0;
		},
	
		isPlainObject: function( obj ) {
	
			// Not plain objects:
			// - Any object or value whose internal [[Class]] property is not "[object Object]"
			// - DOM nodes
			// - window
			if ( jQuery.type( obj ) !== "object" || obj.nodeType || jQuery.isWindow( obj ) ) {
				return false;
			}
	
			if ( obj.constructor &&
					!hasOwn.call( obj.constructor.prototype, "isPrototypeOf" ) ) {
				return false;
			}
	
			// If the function hasn't returned already, we're confident that
			// |obj| is a plain object, created by {} or constructed with new Object
			return true;
		},
	
		isEmptyObject: function( obj ) {
			var name;
			for ( name in obj ) {
				return false;
			}
			return true;
		},
	
		type: function( obj ) {
			if ( obj == null ) {
				return obj + "";
			}
	
			// Support: Android<4.0, iOS<6 (functionish RegExp)
			return typeof obj === "object" || typeof obj === "function" ?
				class2type[ toString.call( obj ) ] || "object" :
				typeof obj;
		},
	
		// Evaluates a script in a global context
		globalEval: function( code ) {
			var script,
				indirect = eval;
	
			code = jQuery.trim( code );
	
			if ( code ) {
	
				// If the code includes a valid, prologue position
				// strict mode pragma, execute code by injecting a
				// script tag into the document.
				if ( code.indexOf( "use strict" ) === 1 ) {
					script = document.createElement( "script" );
					script.text = code;
					document.head.appendChild( script ).parentNode.removeChild( script );
				} else {
	
					// Otherwise, avoid the DOM node creation, insertion
					// and removal by using an indirect global eval
	
					indirect( code );
				}
			}
		},
	
		// Convert dashed to camelCase; used by the css and data modules
		// Support: IE9-11+
		// Microsoft forgot to hump their vendor prefix (#9572)
		camelCase: function( string ) {
			return string.replace( rmsPrefix, "ms-" ).replace( rdashAlpha, fcamelCase );
		},
	
		nodeName: function( elem, name ) {
			return elem.nodeName && elem.nodeName.toLowerCase() === name.toLowerCase();
		},
	
		each: function( obj, callback ) {
			var length, i = 0;
	
			if ( isArrayLike( obj ) ) {
				length = obj.length;
				for ( ; i < length; i++ ) {
					if ( callback.call( obj[ i ], i, obj[ i ] ) === false ) {
						break;
					}
				}
			} else {
				for ( i in obj ) {
					if ( callback.call( obj[ i ], i, obj[ i ] ) === false ) {
						break;
					}
				}
			}
	
			return obj;
		},
	
		// Support: Android<4.1
		trim: function( text ) {
			return text == null ?
				"" :
				( text + "" ).replace( rtrim, "" );
		},
	
		// results is for internal usage only
		makeArray: function( arr, results ) {
			var ret = results || [];
	
			if ( arr != null ) {
				if ( isArrayLike( Object( arr ) ) ) {
					jQuery.merge( ret,
						typeof arr === "string" ?
						[ arr ] : arr
					);
				} else {
					push.call( ret, arr );
				}
			}
	
			return ret;
		},
	
		inArray: function( elem, arr, i ) {
			return arr == null ? -1 : indexOf.call( arr, elem, i );
		},
	
		merge: function( first, second ) {
			var len = +second.length,
				j = 0,
				i = first.length;
	
			for ( ; j < len; j++ ) {
				first[ i++ ] = second[ j ];
			}
	
			first.length = i;
	
			return first;
		},
	
		grep: function( elems, callback, invert ) {
			var callbackInverse,
				matches = [],
				i = 0,
				length = elems.length,
				callbackExpect = !invert;
	
			// Go through the array, only saving the items
			// that pass the validator function
			for ( ; i < length; i++ ) {
				callbackInverse = !callback( elems[ i ], i );
				if ( callbackInverse !== callbackExpect ) {
					matches.push( elems[ i ] );
				}
			}
	
			return matches;
		},
	
		// arg is for internal usage only
		map: function( elems, callback, arg ) {
			var length, value,
				i = 0,
				ret = [];
	
			// Go through the array, translating each of the items to their new values
			if ( isArrayLike( elems ) ) {
				length = elems.length;
				for ( ; i < length; i++ ) {
					value = callback( elems[ i ], i, arg );
	
					if ( value != null ) {
						ret.push( value );
					}
				}
	
			// Go through every key on the object,
			} else {
				for ( i in elems ) {
					value = callback( elems[ i ], i, arg );
	
					if ( value != null ) {
						ret.push( value );
					}
				}
			}
	
			// Flatten any nested arrays
			return concat.apply( [], ret );
		},
	
		// A global GUID counter for objects
		guid: 1,
	
		// Bind a function to a context, optionally partially applying any
		// arguments.
		proxy: function( fn, context ) {
			var tmp, args, proxy;
	
			if ( typeof context === "string" ) {
				tmp = fn[ context ];
				context = fn;
				fn = tmp;
			}
	
			// Quick check to determine if target is callable, in the spec
			// this throws a TypeError, but we will just return undefined.
			if ( !jQuery.isFunction( fn ) ) {
				return undefined;
			}
	
			// Simulated bind
			args = slice.call( arguments, 2 );
			proxy = function() {
				return fn.apply( context || this, args.concat( slice.call( arguments ) ) );
			};
	
			// Set the guid of unique handler to the same of original handler, so it can be removed
			proxy.guid = fn.guid = fn.guid || jQuery.guid++;
	
			return proxy;
		},
	
		now: Date.now,
	
		// jQuery.support is not used in Core but other projects attach their
		// properties to it so it needs to exist.
		support: support
	} );
	
	// JSHint would error on this code due to the Symbol not being defined in ES5.
	// Defining this global in .jshintrc would create a danger of using the global
	// unguarded in another place, it seems safer to just disable JSHint for these
	// three lines.
	/* jshint ignore: start */
	if ( typeof Symbol === "function" ) {
		jQuery.fn[ Symbol.iterator ] = arr[ Symbol.iterator ];
	}
	/* jshint ignore: end */
	
	// Populate the class2type map
	jQuery.each( "Boolean Number String Function Array Date RegExp Object Error Symbol".split( " " ),
	function( i, name ) {
		class2type[ "[object " + name + "]" ] = name.toLowerCase();
	} );
	
	function isArrayLike( obj ) {
	
		// Support: iOS 8.2 (not reproducible in simulator)
		// `in` check used to prevent JIT error (gh-2145)
		// hasOwn isn't used here due to false negatives
		// regarding Nodelist length in IE
		var length = !!obj && "length" in obj && obj.length,
			type = jQuery.type( obj );
	
		if ( type === "function" || jQuery.isWindow( obj ) ) {
			return false;
		}
	
		return type === "array" || length === 0 ||
			typeof length === "number" && length > 0 && ( length - 1 ) in obj;
	}
	var Sizzle =
	/*!
	 * Sizzle CSS Selector Engine v2.2.1
	 * http://sizzlejs.com/
	 *
	 * Copyright jQuery Foundation and other contributors
	 * Released under the MIT license
	 * http://jquery.org/license
	 *
	 * Date: 2015-10-17
	 */
	(function( window ) {
	
	var i,
		support,
		Expr,
		getText,
		isXML,
		tokenize,
		compile,
		select,
		outermostContext,
		sortInput,
		hasDuplicate,
	
		// Local document vars
		setDocument,
		document,
		docElem,
		documentIsHTML,
		rbuggyQSA,
		rbuggyMatches,
		matches,
		contains,
	
		// Instance-specific data
		expando = "sizzle" + 1 * new Date(),
		preferredDoc = window.document,
		dirruns = 0,
		done = 0,
		classCache = createCache(),
		tokenCache = createCache(),
		compilerCache = createCache(),
		sortOrder = function( a, b ) {
			if ( a === b ) {
				hasDuplicate = true;
			}
			return 0;
		},
	
		// General-purpose constants
		MAX_NEGATIVE = 1 << 31,
	
		// Instance methods
		hasOwn = ({}).hasOwnProperty,
		arr = [],
		pop = arr.pop,
		push_native = arr.push,
		push = arr.push,
		slice = arr.slice,
		// Use a stripped-down indexOf as it's faster than native
		// http://jsperf.com/thor-indexof-vs-for/5
		indexOf = function( list, elem ) {
			var i = 0,
				len = list.length;
			for ( ; i < len; i++ ) {
				if ( list[i] === elem ) {
					return i;
				}
			}
			return -1;
		},
	
		booleans = "checked|selected|async|autofocus|autoplay|controls|defer|disabled|hidden|ismap|loop|multiple|open|readonly|required|scoped",
	
		// Regular expressions
	
		// http://www.w3.org/TR/css3-selectors/#whitespace
		whitespace = "[\\x20\\t\\r\\n\\f]",
	
		// http://www.w3.org/TR/CSS21/syndata.html#value-def-identifier
		identifier = "(?:\\\\.|[\\w-]|[^\\x00-\\xa0])+",
	
		// Attribute selectors: http://www.w3.org/TR/selectors/#attribute-selectors
		attributes = "\\[" + whitespace + "*(" + identifier + ")(?:" + whitespace +
			// Operator (capture 2)
			"*([*^$|!~]?=)" + whitespace +
			// "Attribute values must be CSS identifiers [capture 5] or strings [capture 3 or capture 4]"
			"*(?:'((?:\\\\.|[^\\\\'])*)'|\"((?:\\\\.|[^\\\\\"])*)\"|(" + identifier + "))|)" + whitespace +
			"*\\]",
	
		pseudos = ":(" + identifier + ")(?:\\((" +
			// To reduce the number of selectors needing tokenize in the preFilter, prefer arguments:
			// 1. quoted (capture 3; capture 4 or capture 5)
			"('((?:\\\\.|[^\\\\'])*)'|\"((?:\\\\.|[^\\\\\"])*)\")|" +
			// 2. simple (capture 6)
			"((?:\\\\.|[^\\\\()[\\]]|" + attributes + ")*)|" +
			// 3. anything else (capture 2)
			".*" +
			")\\)|)",
	
		// Leading and non-escaped trailing whitespace, capturing some non-whitespace characters preceding the latter
		rwhitespace = new RegExp( whitespace + "+", "g" ),
		rtrim = new RegExp( "^" + whitespace + "+|((?:^|[^\\\\])(?:\\\\.)*)" + whitespace + "+$", "g" ),
	
		rcomma = new RegExp( "^" + whitespace + "*," + whitespace + "*" ),
		rcombinators = new RegExp( "^" + whitespace + "*([>+~]|" + whitespace + ")" + whitespace + "*" ),
	
		rattributeQuotes = new RegExp( "=" + whitespace + "*([^\\]'\"]*?)" + whitespace + "*\\]", "g" ),
	
		rpseudo = new RegExp( pseudos ),
		ridentifier = new RegExp( "^" + identifier + "$" ),
	
		matchExpr = {
			"ID": new RegExp( "^#(" + identifier + ")" ),
			"CLASS": new RegExp( "^\\.(" + identifier + ")" ),
			"TAG": new RegExp( "^(" + identifier + "|[*])" ),
			"ATTR": new RegExp( "^" + attributes ),
			"PSEUDO": new RegExp( "^" + pseudos ),
			"CHILD": new RegExp( "^:(only|first|last|nth|nth-last)-(child|of-type)(?:\\(" + whitespace +
				"*(even|odd|(([+-]|)(\\d*)n|)" + whitespace + "*(?:([+-]|)" + whitespace +
				"*(\\d+)|))" + whitespace + "*\\)|)", "i" ),
			"bool": new RegExp( "^(?:" + booleans + ")$", "i" ),
			// For use in libraries implementing .is()
			// We use this for POS matching in `select`
			"needsContext": new RegExp( "^" + whitespace + "*[>+~]|:(even|odd|eq|gt|lt|nth|first|last)(?:\\(" +
				whitespace + "*((?:-\\d)?\\d*)" + whitespace + "*\\)|)(?=[^-]|$)", "i" )
		},
	
		rinputs = /^(?:input|select|textarea|button)$/i,
		rheader = /^h\d$/i,
	
		rnative = /^[^{]+\{\s*\[native \w/,
	
		// Easily-parseable/retrievable ID or TAG or CLASS selectors
		rquickExpr = /^(?:#([\w-]+)|(\w+)|\.([\w-]+))$/,
	
		rsibling = /[+~]/,
		rescape = /'|\\/g,
	
		// CSS escapes http://www.w3.org/TR/CSS21/syndata.html#escaped-characters
		runescape = new RegExp( "\\\\([\\da-f]{1,6}" + whitespace + "?|(" + whitespace + ")|.)", "ig" ),
		funescape = function( _, escaped, escapedWhitespace ) {
			var high = "0x" + escaped - 0x10000;
			// NaN means non-codepoint
			// Support: Firefox<24
			// Workaround erroneous numeric interpretation of +"0x"
			return high !== high || escapedWhitespace ?
				escaped :
				high < 0 ?
					// BMP codepoint
					String.fromCharCode( high + 0x10000 ) :
					// Supplemental Plane codepoint (surrogate pair)
					String.fromCharCode( high >> 10 | 0xD800, high & 0x3FF | 0xDC00 );
		},
	
		// Used for iframes
		// See setDocument()
		// Removing the function wrapper causes a "Permission Denied"
		// error in IE
		unloadHandler = function() {
			setDocument();
		};
	
	// Optimize for push.apply( _, NodeList )
	try {
		push.apply(
			(arr = slice.call( preferredDoc.childNodes )),
			preferredDoc.childNodes
		);
		// Support: Android<4.0
		// Detect silently failing push.apply
		arr[ preferredDoc.childNodes.length ].nodeType;
	} catch ( e ) {
		push = { apply: arr.length ?
	
			// Leverage slice if possible
			function( target, els ) {
				push_native.apply( target, slice.call(els) );
			} :
	
			// Support: IE<9
			// Otherwise append directly
			function( target, els ) {
				var j = target.length,
					i = 0;
				// Can't trust NodeList.length
				while ( (target[j++] = els[i++]) ) {}
				target.length = j - 1;
			}
		};
	}
	
	function Sizzle( selector, context, results, seed ) {
		var m, i, elem, nid, nidselect, match, groups, newSelector,
			newContext = context && context.ownerDocument,
	
			// nodeType defaults to 9, since context defaults to document
			nodeType = context ? context.nodeType : 9;
	
		results = results || [];
	
		// Return early from calls with invalid selector or context
		if ( typeof selector !== "string" || !selector ||
			nodeType !== 1 && nodeType !== 9 && nodeType !== 11 ) {
	
			return results;
		}
	
		// Try to shortcut find operations (as opposed to filters) in HTML documents
		if ( !seed ) {
	
			if ( ( context ? context.ownerDocument || context : preferredDoc ) !== document ) {
				setDocument( context );
			}
			context = context || document;
	
			if ( documentIsHTML ) {
	
				// If the selector is sufficiently simple, try using a "get*By*" DOM method
				// (excepting DocumentFragment context, where the methods don't exist)
				if ( nodeType !== 11 && (match = rquickExpr.exec( selector )) ) {
	
					// ID selector
					if ( (m = match[1]) ) {
	
						// Document context
						if ( nodeType === 9 ) {
							if ( (elem = context.getElementById( m )) ) {
	
								// Support: IE, Opera, Webkit
								// TODO: identify versions
								// getElementById can match elements by name instead of ID
								if ( elem.id === m ) {
									results.push( elem );
									return results;
								}
							} else {
								return results;
							}
	
						// Element context
						} else {
	
							// Support: IE, Opera, Webkit
							// TODO: identify versions
							// getElementById can match elements by name instead of ID
							if ( newContext && (elem = newContext.getElementById( m )) &&
								contains( context, elem ) &&
								elem.id === m ) {
	
								results.push( elem );
								return results;
							}
						}
	
					// Type selector
					} else if ( match[2] ) {
						push.apply( results, context.getElementsByTagName( selector ) );
						return results;
	
					// Class selector
					} else if ( (m = match[3]) && support.getElementsByClassName &&
						context.getElementsByClassName ) {
	
						push.apply( results, context.getElementsByClassName( m ) );
						return results;
					}
				}
	
				// Take advantage of querySelectorAll
				if ( support.qsa &&
					!compilerCache[ selector + " " ] &&
					(!rbuggyQSA || !rbuggyQSA.test( selector )) ) {
	
					if ( nodeType !== 1 ) {
						newContext = context;
						newSelector = selector;
	
					// qSA looks outside Element context, which is not what we want
					// Thanks to Andrew Dupont for this workaround technique
					// Support: IE <=8
					// Exclude object elements
					} else if ( context.nodeName.toLowerCase() !== "object" ) {
	
						// Capture the context ID, setting it first if necessary
						if ( (nid = context.getAttribute( "id" )) ) {
							nid = nid.replace( rescape, "\\$&" );
						} else {
							context.setAttribute( "id", (nid = expando) );
						}
	
						// Prefix every selector in the list
						groups = tokenize( selector );
						i = groups.length;
						nidselect = ridentifier.test( nid ) ? "#" + nid : "[id='" + nid + "']";
						while ( i-- ) {
							groups[i] = nidselect + " " + toSelector( groups[i] );
						}
						newSelector = groups.join( "," );
	
						// Expand context for sibling selectors
						newContext = rsibling.test( selector ) && testContext( context.parentNode ) ||
							context;
					}
	
					if ( newSelector ) {
						try {
							push.apply( results,
								newContext.querySelectorAll( newSelector )
							);
							return results;
						} catch ( qsaError ) {
						} finally {
							if ( nid === expando ) {
								context.removeAttribute( "id" );
							}
						}
					}
				}
			}
		}
	
		// All others
		return select( selector.replace( rtrim, "$1" ), context, results, seed );
	}
	
	/**
	 * Create key-value caches of limited size
	 * @returns {function(string, object)} Returns the Object data after storing it on itself with
	 *	property name the (space-suffixed) string and (if the cache is larger than Expr.cacheLength)
	 *	deleting the oldest entry
	 */
	function createCache() {
		var keys = [];
	
		function cache( key, value ) {
			// Use (key + " ") to avoid collision with native prototype properties (see Issue #157)
			if ( keys.push( key + " " ) > Expr.cacheLength ) {
				// Only keep the most recent entries
				delete cache[ keys.shift() ];
			}
			return (cache[ key + " " ] = value);
		}
		return cache;
	}
	
	/**
	 * Mark a function for special use by Sizzle
	 * @param {Function} fn The function to mark
	 */
	function markFunction( fn ) {
		fn[ expando ] = true;
		return fn;
	}
	
	/**
	 * Support testing using an element
	 * @param {Function} fn Passed the created div and expects a boolean result
	 */
	function assert( fn ) {
		var div = document.createElement("div");
	
		try {
			return !!fn( div );
		} catch (e) {
			return false;
		} finally {
			// Remove from its parent by default
			if ( div.parentNode ) {
				div.parentNode.removeChild( div );
			}
			// release memory in IE
			div = null;
		}
	}
	
	/**
	 * Adds the same handler for all of the specified attrs
	 * @param {String} attrs Pipe-separated list of attributes
	 * @param {Function} handler The method that will be applied
	 */
	function addHandle( attrs, handler ) {
		var arr = attrs.split("|"),
			i = arr.length;
	
		while ( i-- ) {
			Expr.attrHandle[ arr[i] ] = handler;
		}
	}
	
	/**
	 * Checks document order of two siblings
	 * @param {Element} a
	 * @param {Element} b
	 * @returns {Number} Returns less than 0 if a precedes b, greater than 0 if a follows b
	 */
	function siblingCheck( a, b ) {
		var cur = b && a,
			diff = cur && a.nodeType === 1 && b.nodeType === 1 &&
				( ~b.sourceIndex || MAX_NEGATIVE ) -
				( ~a.sourceIndex || MAX_NEGATIVE );
	
		// Use IE sourceIndex if available on both nodes
		if ( diff ) {
			return diff;
		}
	
		// Check if b follows a
		if ( cur ) {
			while ( (cur = cur.nextSibling) ) {
				if ( cur === b ) {
					return -1;
				}
			}
		}
	
		return a ? 1 : -1;
	}
	
	/**
	 * Returns a function to use in pseudos for input types
	 * @param {String} type
	 */
	function createInputPseudo( type ) {
		return function( elem ) {
			var name = elem.nodeName.toLowerCase();
			return name === "input" && elem.type === type;
		};
	}
	
	/**
	 * Returns a function to use in pseudos for buttons
	 * @param {String} type
	 */
	function createButtonPseudo( type ) {
		return function( elem ) {
			var name = elem.nodeName.toLowerCase();
			return (name === "input" || name === "button") && elem.type === type;
		};
	}
	
	/**
	 * Returns a function to use in pseudos for positionals
	 * @param {Function} fn
	 */
	function createPositionalPseudo( fn ) {
		return markFunction(function( argument ) {
			argument = +argument;
			return markFunction(function( seed, matches ) {
				var j,
					matchIndexes = fn( [], seed.length, argument ),
					i = matchIndexes.length;
	
				// Match elements found at the specified indexes
				while ( i-- ) {
					if ( seed[ (j = matchIndexes[i]) ] ) {
						seed[j] = !(matches[j] = seed[j]);
					}
				}
			});
		});
	}
	
	/**
	 * Checks a node for validity as a Sizzle context
	 * @param {Element|Object=} context
	 * @returns {Element|Object|Boolean} The input node if acceptable, otherwise a falsy value
	 */
	function testContext( context ) {
		return context && typeof context.getElementsByTagName !== "undefined" && context;
	}
	
	// Expose support vars for convenience
	support = Sizzle.support = {};
	
	/**
	 * Detects XML nodes
	 * @param {Element|Object} elem An element or a document
	 * @returns {Boolean} True iff elem is a non-HTML XML node
	 */
	isXML = Sizzle.isXML = function( elem ) {
		// documentElement is verified for cases where it doesn't yet exist
		// (such as loading iframes in IE - #4833)
		var documentElement = elem && (elem.ownerDocument || elem).documentElement;
		return documentElement ? documentElement.nodeName !== "HTML" : false;
	};
	
	/**
	 * Sets document-related variables once based on the current document
	 * @param {Element|Object} [doc] An element or document object to use to set the document
	 * @returns {Object} Returns the current document
	 */
	setDocument = Sizzle.setDocument = function( node ) {
		var hasCompare, parent,
			doc = node ? node.ownerDocument || node : preferredDoc;
	
		// Return early if doc is invalid or already selected
		if ( doc === document || doc.nodeType !== 9 || !doc.documentElement ) {
			return document;
		}
	
		// Update global variables
		document = doc;
		docElem = document.documentElement;
		documentIsHTML = !isXML( document );
	
		// Support: IE 9-11, Edge
		// Accessing iframe documents after unload throws "permission denied" errors (jQuery #13936)
		if ( (parent = document.defaultView) && parent.top !== parent ) {
			// Support: IE 11
			if ( parent.addEventListener ) {
				parent.addEventListener( "unload", unloadHandler, false );
	
			// Support: IE 9 - 10 only
			} else if ( parent.attachEvent ) {
				parent.attachEvent( "onunload", unloadHandler );
			}
		}
	
		/* Attributes
		---------------------------------------------------------------------- */
	
		// Support: IE<8
		// Verify that getAttribute really returns attributes and not properties
		// (excepting IE8 booleans)
		support.attributes = assert(function( div ) {
			div.className = "i";
			return !div.getAttribute("className");
		});
	
		/* getElement(s)By*
		---------------------------------------------------------------------- */
	
		// Check if getElementsByTagName("*") returns only elements
		support.getElementsByTagName = assert(function( div ) {
			div.appendChild( document.createComment("") );
			return !div.getElementsByTagName("*").length;
		});
	
		// Support: IE<9
		support.getElementsByClassName = rnative.test( document.getElementsByClassName );
	
		// Support: IE<10
		// Check if getElementById returns elements by name
		// The broken getElementById methods don't pick up programatically-set names,
		// so use a roundabout getElementsByName test
		support.getById = assert(function( div ) {
			docElem.appendChild( div ).id = expando;
			return !document.getElementsByName || !document.getElementsByName( expando ).length;
		});
	
		// ID find and filter
		if ( support.getById ) {
			Expr.find["ID"] = function( id, context ) {
				if ( typeof context.getElementById !== "undefined" && documentIsHTML ) {
					var m = context.getElementById( id );
					return m ? [ m ] : [];
				}
			};
			Expr.filter["ID"] = function( id ) {
				var attrId = id.replace( runescape, funescape );
				return function( elem ) {
					return elem.getAttribute("id") === attrId;
				};
			};
		} else {
			// Support: IE6/7
			// getElementById is not reliable as a find shortcut
			delete Expr.find["ID"];
	
			Expr.filter["ID"] =  function( id ) {
				var attrId = id.replace( runescape, funescape );
				return function( elem ) {
					var node = typeof elem.getAttributeNode !== "undefined" &&
						elem.getAttributeNode("id");
					return node && node.value === attrId;
				};
			};
		}
	
		// Tag
		Expr.find["TAG"] = support.getElementsByTagName ?
			function( tag, context ) {
				if ( typeof context.getElementsByTagName !== "undefined" ) {
					return context.getElementsByTagName( tag );
	
				// DocumentFragment nodes don't have gEBTN
				} else if ( support.qsa ) {
					return context.querySelectorAll( tag );
				}
			} :
	
			function( tag, context ) {
				var elem,
					tmp = [],
					i = 0,
					// By happy coincidence, a (broken) gEBTN appears on DocumentFragment nodes too
					results = context.getElementsByTagName( tag );
	
				// Filter out possible comments
				if ( tag === "*" ) {
					while ( (elem = results[i++]) ) {
						if ( elem.nodeType === 1 ) {
							tmp.push( elem );
						}
					}
	
					return tmp;
				}
				return results;
			};
	
		// Class
		Expr.find["CLASS"] = support.getElementsByClassName && function( className, context ) {
			if ( typeof context.getElementsByClassName !== "undefined" && documentIsHTML ) {
				return context.getElementsByClassName( className );
			}
		};
	
		/* QSA/matchesSelector
		---------------------------------------------------------------------- */
	
		// QSA and matchesSelector support
	
		// matchesSelector(:active) reports false when true (IE9/Opera 11.5)
		rbuggyMatches = [];
	
		// qSa(:focus) reports false when true (Chrome 21)
		// We allow this because of a bug in IE8/9 that throws an error
		// whenever `document.activeElement` is accessed on an iframe
		// So, we allow :focus to pass through QSA all the time to avoid the IE error
		// See http://bugs.jquery.com/ticket/13378
		rbuggyQSA = [];
	
		if ( (support.qsa = rnative.test( document.querySelectorAll )) ) {
			// Build QSA regex
			// Regex strategy adopted from Diego Perini
			assert(function( div ) {
				// Select is set to empty string on purpose
				// This is to test IE's treatment of not explicitly
				// setting a boolean content attribute,
				// since its presence should be enough
				// http://bugs.jquery.com/ticket/12359
				docElem.appendChild( div ).innerHTML = "<a id='" + expando + "'></a>" +
					"<select id='" + expando + "-\r\\' msallowcapture=''>" +
					"<option selected=''></option></select>";
	
				// Support: IE8, Opera 11-12.16
				// Nothing should be selected when empty strings follow ^= or $= or *=
				// The test attribute must be unknown in Opera but "safe" for WinRT
				// http://msdn.microsoft.com/en-us/library/ie/hh465388.aspx#attribute_section
				if ( div.querySelectorAll("[msallowcapture^='']").length ) {
					rbuggyQSA.push( "[*^$]=" + whitespace + "*(?:''|\"\")" );
				}
	
				// Support: IE8
				// Boolean attributes and "value" are not treated correctly
				if ( !div.querySelectorAll("[selected]").length ) {
					rbuggyQSA.push( "\\[" + whitespace + "*(?:value|" + booleans + ")" );
				}
	
				// Support: Chrome<29, Android<4.4, Safari<7.0+, iOS<7.0+, PhantomJS<1.9.8+
				if ( !div.querySelectorAll( "[id~=" + expando + "-]" ).length ) {
					rbuggyQSA.push("~=");
				}
	
				// Webkit/Opera - :checked should return selected option elements
				// http://www.w3.org/TR/2011/REC-css3-selectors-20110929/#checked
				// IE8 throws error here and will not see later tests
				if ( !div.querySelectorAll(":checked").length ) {
					rbuggyQSA.push(":checked");
				}
	
				// Support: Safari 8+, iOS 8+
				// https://bugs.webkit.org/show_bug.cgi?id=136851
				// In-page `selector#id sibing-combinator selector` fails
				if ( !div.querySelectorAll( "a#" + expando + "+*" ).length ) {
					rbuggyQSA.push(".#.+[+~]");
				}
			});
	
			assert(function( div ) {
				// Support: Windows 8 Native Apps
				// The type and name attributes are restricted during .innerHTML assignment
				var input = document.createElement("input");
				input.setAttribute( "type", "hidden" );
				div.appendChild( input ).setAttribute( "name", "D" );
	
				// Support: IE8
				// Enforce case-sensitivity of name attribute
				if ( div.querySelectorAll("[name=d]").length ) {
					rbuggyQSA.push( "name" + whitespace + "*[*^$|!~]?=" );
				}
	
				// FF 3.5 - :enabled/:disabled and hidden elements (hidden elements are still enabled)
				// IE8 throws error here and will not see later tests
				if ( !div.querySelectorAll(":enabled").length ) {
					rbuggyQSA.push( ":enabled", ":disabled" );
				}
	
				// Opera 10-11 does not throw on post-comma invalid pseudos
				div.querySelectorAll("*,:x");
				rbuggyQSA.push(",.*:");
			});
		}
	
		if ( (support.matchesSelector = rnative.test( (matches = docElem.matches ||
			docElem.webkitMatchesSelector ||
			docElem.mozMatchesSelector ||
			docElem.oMatchesSelector ||
			docElem.msMatchesSelector) )) ) {
	
			assert(function( div ) {
				// Check to see if it's possible to do matchesSelector
				// on a disconnected node (IE 9)
				support.disconnectedMatch = matches.call( div, "div" );
	
				// This should fail with an exception
				// Gecko does not error, returns false instead
				matches.call( div, "[s!='']:x" );
				rbuggyMatches.push( "!=", pseudos );
			});
		}
	
		rbuggyQSA = rbuggyQSA.length && new RegExp( rbuggyQSA.join("|") );
		rbuggyMatches = rbuggyMatches.length && new RegExp( rbuggyMatches.join("|") );
	
		/* Contains
		---------------------------------------------------------------------- */
		hasCompare = rnative.test( docElem.compareDocumentPosition );
	
		// Element contains another
		// Purposefully self-exclusive
		// As in, an element does not contain itself
		contains = hasCompare || rnative.test( docElem.contains ) ?
			function( a, b ) {
				var adown = a.nodeType === 9 ? a.documentElement : a,
					bup = b && b.parentNode;
				return a === bup || !!( bup && bup.nodeType === 1 && (
					adown.contains ?
						adown.contains( bup ) :
						a.compareDocumentPosition && a.compareDocumentPosition( bup ) & 16
				));
			} :
			function( a, b ) {
				if ( b ) {
					while ( (b = b.parentNode) ) {
						if ( b === a ) {
							return true;
						}
					}
				}
				return false;
			};
	
		/* Sorting
		---------------------------------------------------------------------- */
	
		// Document order sorting
		sortOrder = hasCompare ?
		function( a, b ) {
	
			// Flag for duplicate removal
			if ( a === b ) {
				hasDuplicate = true;
				return 0;
			}
	
			// Sort on method existence if only one input has compareDocumentPosition
			var compare = !a.compareDocumentPosition - !b.compareDocumentPosition;
			if ( compare ) {
				return compare;
			}
	
			// Calculate position if both inputs belong to the same document
			compare = ( a.ownerDocument || a ) === ( b.ownerDocument || b ) ?
				a.compareDocumentPosition( b ) :
	
				// Otherwise we know they are disconnected
				1;
	
			// Disconnected nodes
			if ( compare & 1 ||
				(!support.sortDetached && b.compareDocumentPosition( a ) === compare) ) {
	
				// Choose the first element that is related to our preferred document
				if ( a === document || a.ownerDocument === preferredDoc && contains(preferredDoc, a) ) {
					return -1;
				}
				if ( b === document || b.ownerDocument === preferredDoc && contains(preferredDoc, b) ) {
					return 1;
				}
	
				// Maintain original order
				return sortInput ?
					( indexOf( sortInput, a ) - indexOf( sortInput, b ) ) :
					0;
			}
	
			return compare & 4 ? -1 : 1;
		} :
		function( a, b ) {
			// Exit early if the nodes are identical
			if ( a === b ) {
				hasDuplicate = true;
				return 0;
			}
	
			var cur,
				i = 0,
				aup = a.parentNode,
				bup = b.parentNode,
				ap = [ a ],
				bp = [ b ];
	
			// Parentless nodes are either documents or disconnected
			if ( !aup || !bup ) {
				return a === document ? -1 :
					b === document ? 1 :
					aup ? -1 :
					bup ? 1 :
					sortInput ?
					( indexOf( sortInput, a ) - indexOf( sortInput, b ) ) :
					0;
	
			// If the nodes are siblings, we can do a quick check
			} else if ( aup === bup ) {
				return siblingCheck( a, b );
			}
	
			// Otherwise we need full lists of their ancestors for comparison
			cur = a;
			while ( (cur = cur.parentNode) ) {
				ap.unshift( cur );
			}
			cur = b;
			while ( (cur = cur.parentNode) ) {
				bp.unshift( cur );
			}
	
			// Walk down the tree looking for a discrepancy
			while ( ap[i] === bp[i] ) {
				i++;
			}
	
			return i ?
				// Do a sibling check if the nodes have a common ancestor
				siblingCheck( ap[i], bp[i] ) :
	
				// Otherwise nodes in our document sort first
				ap[i] === preferredDoc ? -1 :
				bp[i] === preferredDoc ? 1 :
				0;
		};
	
		return document;
	};
	
	Sizzle.matches = function( expr, elements ) {
		return Sizzle( expr, null, null, elements );
	};
	
	Sizzle.matchesSelector = function( elem, expr ) {
		// Set document vars if needed
		if ( ( elem.ownerDocument || elem ) !== document ) {
			setDocument( elem );
		}
	
		// Make sure that attribute selectors are quoted
		expr = expr.replace( rattributeQuotes, "='$1']" );
	
		if ( support.matchesSelector && documentIsHTML &&
			!compilerCache[ expr + " " ] &&
			( !rbuggyMatches || !rbuggyMatches.test( expr ) ) &&
			( !rbuggyQSA     || !rbuggyQSA.test( expr ) ) ) {
	
			try {
				var ret = matches.call( elem, expr );
	
				// IE 9's matchesSelector returns false on disconnected nodes
				if ( ret || support.disconnectedMatch ||
						// As well, disconnected nodes are said to be in a document
						// fragment in IE 9
						elem.document && elem.document.nodeType !== 11 ) {
					return ret;
				}
			} catch (e) {}
		}
	
		return Sizzle( expr, document, null, [ elem ] ).length > 0;
	};
	
	Sizzle.contains = function( context, elem ) {
		// Set document vars if needed
		if ( ( context.ownerDocument || context ) !== document ) {
			setDocument( context );
		}
		return contains( context, elem );
	};
	
	Sizzle.attr = function( elem, name ) {
		// Set document vars if needed
		if ( ( elem.ownerDocument || elem ) !== document ) {
			setDocument( elem );
		}
	
		var fn = Expr.attrHandle[ name.toLowerCase() ],
			// Don't get fooled by Object.prototype properties (jQuery #13807)
			val = fn && hasOwn.call( Expr.attrHandle, name.toLowerCase() ) ?
				fn( elem, name, !documentIsHTML ) :
				undefined;
	
		return val !== undefined ?
			val :
			support.attributes || !documentIsHTML ?
				elem.getAttribute( name ) :
				(val = elem.getAttributeNode(name)) && val.specified ?
					val.value :
					null;
	};
	
	Sizzle.error = function( msg ) {
		throw new Error( "Syntax error, unrecognized expression: " + msg );
	};
	
	/**
	 * Document sorting and removing duplicates
	 * @param {ArrayLike} results
	 */
	Sizzle.uniqueSort = function( results ) {
		var elem,
			duplicates = [],
			j = 0,
			i = 0;
	
		// Unless we *know* we can detect duplicates, assume their presence
		hasDuplicate = !support.detectDuplicates;
		sortInput = !support.sortStable && results.slice( 0 );
		results.sort( sortOrder );
	
		if ( hasDuplicate ) {
			while ( (elem = results[i++]) ) {
				if ( elem === results[ i ] ) {
					j = duplicates.push( i );
				}
			}
			while ( j-- ) {
				results.splice( duplicates[ j ], 1 );
			}
		}
	
		// Clear input after sorting to release objects
		// See https://github.com/jquery/sizzle/pull/225
		sortInput = null;
	
		return results;
	};
	
	/**
	 * Utility function for retrieving the text value of an array of DOM nodes
	 * @param {Array|Element} elem
	 */
	getText = Sizzle.getText = function( elem ) {
		var node,
			ret = "",
			i = 0,
			nodeType = elem.nodeType;
	
		if ( !nodeType ) {
			// If no nodeType, this is expected to be an array
			while ( (node = elem[i++]) ) {
				// Do not traverse comment nodes
				ret += getText( node );
			}
		} else if ( nodeType === 1 || nodeType === 9 || nodeType === 11 ) {
			// Use textContent for elements
			// innerText usage removed for consistency of new lines (jQuery #11153)
			if ( typeof elem.textContent === "string" ) {
				return elem.textContent;
			} else {
				// Traverse its children
				for ( elem = elem.firstChild; elem; elem = elem.nextSibling ) {
					ret += getText( elem );
				}
			}
		} else if ( nodeType === 3 || nodeType === 4 ) {
			return elem.nodeValue;
		}
		// Do not include comment or processing instruction nodes
	
		return ret;
	};
	
	Expr = Sizzle.selectors = {
	
		// Can be adjusted by the user
		cacheLength: 50,
	
		createPseudo: markFunction,
	
		match: matchExpr,
	
		attrHandle: {},
	
		find: {},
	
		relative: {
			">": { dir: "parentNode", first: true },
			" ": { dir: "parentNode" },
			"+": { dir: "previousSibling", first: true },
			"~": { dir: "previousSibling" }
		},
	
		preFilter: {
			"ATTR": function( match ) {
				match[1] = match[1].replace( runescape, funescape );
	
				// Move the given value to match[3] whether quoted or unquoted
				match[3] = ( match[3] || match[4] || match[5] || "" ).replace( runescape, funescape );
	
				if ( match[2] === "~=" ) {
					match[3] = " " + match[3] + " ";
				}
	
				return match.slice( 0, 4 );
			},
	
			"CHILD": function( match ) {
				/* matches from matchExpr["CHILD"]
					1 type (only|nth|...)
					2 what (child|of-type)
					3 argument (even|odd|\d*|\d*n([+-]\d+)?|...)
					4 xn-component of xn+y argument ([+-]?\d*n|)
					5 sign of xn-component
					6 x of xn-component
					7 sign of y-component
					8 y of y-component
				*/
				match[1] = match[1].toLowerCase();
	
				if ( match[1].slice( 0, 3 ) === "nth" ) {
					// nth-* requires argument
					if ( !match[3] ) {
						Sizzle.error( match[0] );
					}
	
					// numeric x and y parameters for Expr.filter.CHILD
					// remember that false/true cast respectively to 0/1
					match[4] = +( match[4] ? match[5] + (match[6] || 1) : 2 * ( match[3] === "even" || match[3] === "odd" ) );
					match[5] = +( ( match[7] + match[8] ) || match[3] === "odd" );
	
				// other types prohibit arguments
				} else if ( match[3] ) {
					Sizzle.error( match[0] );
				}
	
				return match;
			},
	
			"PSEUDO": function( match ) {
				var excess,
					unquoted = !match[6] && match[2];
	
				if ( matchExpr["CHILD"].test( match[0] ) ) {
					return null;
				}
	
				// Accept quoted arguments as-is
				if ( match[3] ) {
					match[2] = match[4] || match[5] || "";
	
				// Strip excess characters from unquoted arguments
				} else if ( unquoted && rpseudo.test( unquoted ) &&
					// Get excess from tokenize (recursively)
					(excess = tokenize( unquoted, true )) &&
					// advance to the next closing parenthesis
					(excess = unquoted.indexOf( ")", unquoted.length - excess ) - unquoted.length) ) {
	
					// excess is a negative index
					match[0] = match[0].slice( 0, excess );
					match[2] = unquoted.slice( 0, excess );
				}
	
				// Return only captures needed by the pseudo filter method (type and argument)
				return match.slice( 0, 3 );
			}
		},
	
		filter: {
	
			"TAG": function( nodeNameSelector ) {
				var nodeName = nodeNameSelector.replace( runescape, funescape ).toLowerCase();
				return nodeNameSelector === "*" ?
					function() { return true; } :
					function( elem ) {
						return elem.nodeName && elem.nodeName.toLowerCase() === nodeName;
					};
			},
	
			"CLASS": function( className ) {
				var pattern = classCache[ className + " " ];
	
				return pattern ||
					(pattern = new RegExp( "(^|" + whitespace + ")" + className + "(" + whitespace + "|$)" )) &&
					classCache( className, function( elem ) {
						return pattern.test( typeof elem.className === "string" && elem.className || typeof elem.getAttribute !== "undefined" && elem.getAttribute("class") || "" );
					});
			},
	
			"ATTR": function( name, operator, check ) {
				return function( elem ) {
					var result = Sizzle.attr( elem, name );
	
					if ( result == null ) {
						return operator === "!=";
					}
					if ( !operator ) {
						return true;
					}
	
					result += "";
	
					return operator === "=" ? result === check :
						operator === "!=" ? result !== check :
						operator === "^=" ? check && result.indexOf( check ) === 0 :
						operator === "*=" ? check && result.indexOf( check ) > -1 :
						operator === "$=" ? check && result.slice( -check.length ) === check :
						operator === "~=" ? ( " " + result.replace( rwhitespace, " " ) + " " ).indexOf( check ) > -1 :
						operator === "|=" ? result === check || result.slice( 0, check.length + 1 ) === check + "-" :
						false;
				};
			},
	
			"CHILD": function( type, what, argument, first, last ) {
				var simple = type.slice( 0, 3 ) !== "nth",
					forward = type.slice( -4 ) !== "last",
					ofType = what === "of-type";
	
				return first === 1 && last === 0 ?
	
					// Shortcut for :nth-*(n)
					function( elem ) {
						return !!elem.parentNode;
					} :
	
					function( elem, context, xml ) {
						var cache, uniqueCache, outerCache, node, nodeIndex, start,
							dir = simple !== forward ? "nextSibling" : "previousSibling",
							parent = elem.parentNode,
							name = ofType && elem.nodeName.toLowerCase(),
							useCache = !xml && !ofType,
							diff = false;
	
						if ( parent ) {
	
							// :(first|last|only)-(child|of-type)
							if ( simple ) {
								while ( dir ) {
									node = elem;
									while ( (node = node[ dir ]) ) {
										if ( ofType ?
											node.nodeName.toLowerCase() === name :
											node.nodeType === 1 ) {
	
											return false;
										}
									}
									// Reverse direction for :only-* (if we haven't yet done so)
									start = dir = type === "only" && !start && "nextSibling";
								}
								return true;
							}
	
							start = [ forward ? parent.firstChild : parent.lastChild ];
	
							// non-xml :nth-child(...) stores cache data on `parent`
							if ( forward && useCache ) {
	
								// Seek `elem` from a previously-cached index
	
								// ...in a gzip-friendly way
								node = parent;
								outerCache = node[ expando ] || (node[ expando ] = {});
	
								// Support: IE <9 only
								// Defend against cloned attroperties (jQuery gh-1709)
								uniqueCache = outerCache[ node.uniqueID ] ||
									(outerCache[ node.uniqueID ] = {});
	
								cache = uniqueCache[ type ] || [];
								nodeIndex = cache[ 0 ] === dirruns && cache[ 1 ];
								diff = nodeIndex && cache[ 2 ];
								node = nodeIndex && parent.childNodes[ nodeIndex ];
	
								while ( (node = ++nodeIndex && node && node[ dir ] ||
	
									// Fallback to seeking `elem` from the start
									(diff = nodeIndex = 0) || start.pop()) ) {
	
									// When found, cache indexes on `parent` and break
									if ( node.nodeType === 1 && ++diff && node === elem ) {
										uniqueCache[ type ] = [ dirruns, nodeIndex, diff ];
										break;
									}
								}
	
							} else {
								// Use previously-cached element index if available
								if ( useCache ) {
									// ...in a gzip-friendly way
									node = elem;
									outerCache = node[ expando ] || (node[ expando ] = {});
	
									// Support: IE <9 only
									// Defend against cloned attroperties (jQuery gh-1709)
									uniqueCache = outerCache[ node.uniqueID ] ||
										(outerCache[ node.uniqueID ] = {});
	
									cache = uniqueCache[ type ] || [];
									nodeIndex = cache[ 0 ] === dirruns && cache[ 1 ];
									diff = nodeIndex;
								}
	
								// xml :nth-child(...)
								// or :nth-last-child(...) or :nth(-last)?-of-type(...)
								if ( diff === false ) {
									// Use the same loop as above to seek `elem` from the start
									while ( (node = ++nodeIndex && node && node[ dir ] ||
										(diff = nodeIndex = 0) || start.pop()) ) {
	
										if ( ( ofType ?
											node.nodeName.toLowerCase() === name :
											node.nodeType === 1 ) &&
											++diff ) {
	
											// Cache the index of each encountered element
											if ( useCache ) {
												outerCache = node[ expando ] || (node[ expando ] = {});
	
												// Support: IE <9 only
												// Defend against cloned attroperties (jQuery gh-1709)
												uniqueCache = outerCache[ node.uniqueID ] ||
													(outerCache[ node.uniqueID ] = {});
	
												uniqueCache[ type ] = [ dirruns, diff ];
											}
	
											if ( node === elem ) {
												break;
											}
										}
									}
								}
							}
	
							// Incorporate the offset, then check against cycle size
							diff -= last;
							return diff === first || ( diff % first === 0 && diff / first >= 0 );
						}
					};
			},
	
			"PSEUDO": function( pseudo, argument ) {
				// pseudo-class names are case-insensitive
				// http://www.w3.org/TR/selectors/#pseudo-classes
				// Prioritize by case sensitivity in case custom pseudos are added with uppercase letters
				// Remember that setFilters inherits from pseudos
				var args,
					fn = Expr.pseudos[ pseudo ] || Expr.setFilters[ pseudo.toLowerCase() ] ||
						Sizzle.error( "unsupported pseudo: " + pseudo );
	
				// The user may use createPseudo to indicate that
				// arguments are needed to create the filter function
				// just as Sizzle does
				if ( fn[ expando ] ) {
					return fn( argument );
				}
	
				// But maintain support for old signatures
				if ( fn.length > 1 ) {
					args = [ pseudo, pseudo, "", argument ];
					return Expr.setFilters.hasOwnProperty( pseudo.toLowerCase() ) ?
						markFunction(function( seed, matches ) {
							var idx,
								matched = fn( seed, argument ),
								i = matched.length;
							while ( i-- ) {
								idx = indexOf( seed, matched[i] );
								seed[ idx ] = !( matches[ idx ] = matched[i] );
							}
						}) :
						function( elem ) {
							return fn( elem, 0, args );
						};
				}
	
				return fn;
			}
		},
	
		pseudos: {
			// Potentially complex pseudos
			"not": markFunction(function( selector ) {
				// Trim the selector passed to compile
				// to avoid treating leading and trailing
				// spaces as combinators
				var input = [],
					results = [],
					matcher = compile( selector.replace( rtrim, "$1" ) );
	
				return matcher[ expando ] ?
					markFunction(function( seed, matches, context, xml ) {
						var elem,
							unmatched = matcher( seed, null, xml, [] ),
							i = seed.length;
	
						// Match elements unmatched by `matcher`
						while ( i-- ) {
							if ( (elem = unmatched[i]) ) {
								seed[i] = !(matches[i] = elem);
							}
						}
					}) :
					function( elem, context, xml ) {
						input[0] = elem;
						matcher( input, null, xml, results );
						// Don't keep the element (issue #299)
						input[0] = null;
						return !results.pop();
					};
			}),
	
			"has": markFunction(function( selector ) {
				return function( elem ) {
					return Sizzle( selector, elem ).length > 0;
				};
			}),
	
			"contains": markFunction(function( text ) {
				text = text.replace( runescape, funescape );
				return function( elem ) {
					return ( elem.textContent || elem.innerText || getText( elem ) ).indexOf( text ) > -1;
				};
			}),
	
			// "Whether an element is represented by a :lang() selector
			// is based solely on the element's language value
			// being equal to the identifier C,
			// or beginning with the identifier C immediately followed by "-".
			// The matching of C against the element's language value is performed case-insensitively.
			// The identifier C does not have to be a valid language name."
			// http://www.w3.org/TR/selectors/#lang-pseudo
			"lang": markFunction( function( lang ) {
				// lang value must be a valid identifier
				if ( !ridentifier.test(lang || "") ) {
					Sizzle.error( "unsupported lang: " + lang );
				}
				lang = lang.replace( runescape, funescape ).toLowerCase();
				return function( elem ) {
					var elemLang;
					do {
						if ( (elemLang = documentIsHTML ?
							elem.lang :
							elem.getAttribute("xml:lang") || elem.getAttribute("lang")) ) {
	
							elemLang = elemLang.toLowerCase();
							return elemLang === lang || elemLang.indexOf( lang + "-" ) === 0;
						}
					} while ( (elem = elem.parentNode) && elem.nodeType === 1 );
					return false;
				};
			}),
	
			// Miscellaneous
			"target": function( elem ) {
				var hash = window.location && window.location.hash;
				return hash && hash.slice( 1 ) === elem.id;
			},
	
			"root": function( elem ) {
				return elem === docElem;
			},
	
			"focus": function( elem ) {
				return elem === document.activeElement && (!document.hasFocus || document.hasFocus()) && !!(elem.type || elem.href || ~elem.tabIndex);
			},
	
			// Boolean properties
			"enabled": function( elem ) {
				return elem.disabled === false;
			},
	
			"disabled": function( elem ) {
				return elem.disabled === true;
			},
	
			"checked": function( elem ) {
				// In CSS3, :checked should return both checked and selected elements
				// http://www.w3.org/TR/2011/REC-css3-selectors-20110929/#checked
				var nodeName = elem.nodeName.toLowerCase();
				return (nodeName === "input" && !!elem.checked) || (nodeName === "option" && !!elem.selected);
			},
	
			"selected": function( elem ) {
				// Accessing this property makes selected-by-default
				// options in Safari work properly
				if ( elem.parentNode ) {
					elem.parentNode.selectedIndex;
				}
	
				return elem.selected === true;
			},
	
			// Contents
			"empty": function( elem ) {
				// http://www.w3.org/TR/selectors/#empty-pseudo
				// :empty is negated by element (1) or content nodes (text: 3; cdata: 4; entity ref: 5),
				//   but not by others (comment: 8; processing instruction: 7; etc.)
				// nodeType < 6 works because attributes (2) do not appear as children
				for ( elem = elem.firstChild; elem; elem = elem.nextSibling ) {
					if ( elem.nodeType < 6 ) {
						return false;
					}
				}
				return true;
			},
	
			"parent": function( elem ) {
				return !Expr.pseudos["empty"]( elem );
			},
	
			// Element/input types
			"header": function( elem ) {
				return rheader.test( elem.nodeName );
			},
	
			"input": function( elem ) {
				return rinputs.test( elem.nodeName );
			},
	
			"button": function( elem ) {
				var name = elem.nodeName.toLowerCase();
				return name === "input" && elem.type === "button" || name === "button";
			},
	
			"text": function( elem ) {
				var attr;
				return elem.nodeName.toLowerCase() === "input" &&
					elem.type === "text" &&
	
					// Support: IE<8
					// New HTML5 attribute values (e.g., "search") appear with elem.type === "text"
					( (attr = elem.getAttribute("type")) == null || attr.toLowerCase() === "text" );
			},
	
			// Position-in-collection
			"first": createPositionalPseudo(function() {
				return [ 0 ];
			}),
	
			"last": createPositionalPseudo(function( matchIndexes, length ) {
				return [ length - 1 ];
			}),
	
			"eq": createPositionalPseudo(function( matchIndexes, length, argument ) {
				return [ argument < 0 ? argument + length : argument ];
			}),
	
			"even": createPositionalPseudo(function( matchIndexes, length ) {
				var i = 0;
				for ( ; i < length; i += 2 ) {
					matchIndexes.push( i );
				}
				return matchIndexes;
			}),
	
			"odd": createPositionalPseudo(function( matchIndexes, length ) {
				var i = 1;
				for ( ; i < length; i += 2 ) {
					matchIndexes.push( i );
				}
				return matchIndexes;
			}),
	
			"lt": createPositionalPseudo(function( matchIndexes, length, argument ) {
				var i = argument < 0 ? argument + length : argument;
				for ( ; --i >= 0; ) {
					matchIndexes.push( i );
				}
				return matchIndexes;
			}),
	
			"gt": createPositionalPseudo(function( matchIndexes, length, argument ) {
				var i = argument < 0 ? argument + length : argument;
				for ( ; ++i < length; ) {
					matchIndexes.push( i );
				}
				return matchIndexes;
			})
		}
	};
	
	Expr.pseudos["nth"] = Expr.pseudos["eq"];
	
	// Add button/input type pseudos
	for ( i in { radio: true, checkbox: true, file: true, password: true, image: true } ) {
		Expr.pseudos[ i ] = createInputPseudo( i );
	}
	for ( i in { submit: true, reset: true } ) {
		Expr.pseudos[ i ] = createButtonPseudo( i );
	}
	
	// Easy API for creating new setFilters
	function setFilters() {}
	setFilters.prototype = Expr.filters = Expr.pseudos;
	Expr.setFilters = new setFilters();
	
	tokenize = Sizzle.tokenize = function( selector, parseOnly ) {
		var matched, match, tokens, type,
			soFar, groups, preFilters,
			cached = tokenCache[ selector + " " ];
	
		if ( cached ) {
			return parseOnly ? 0 : cached.slice( 0 );
		}
	
		soFar = selector;
		groups = [];
		preFilters = Expr.preFilter;
	
		while ( soFar ) {
	
			// Comma and first run
			if ( !matched || (match = rcomma.exec( soFar )) ) {
				if ( match ) {
					// Don't consume trailing commas as valid
					soFar = soFar.slice( match[0].length ) || soFar;
				}
				groups.push( (tokens = []) );
			}
	
			matched = false;
	
			// Combinators
			if ( (match = rcombinators.exec( soFar )) ) {
				matched = match.shift();
				tokens.push({
					value: matched,
					// Cast descendant combinators to space
					type: match[0].replace( rtrim, " " )
				});
				soFar = soFar.slice( matched.length );
			}
	
			// Filters
			for ( type in Expr.filter ) {
				if ( (match = matchExpr[ type ].exec( soFar )) && (!preFilters[ type ] ||
					(match = preFilters[ type ]( match ))) ) {
					matched = match.shift();
					tokens.push({
						value: matched,
						type: type,
						matches: match
					});
					soFar = soFar.slice( matched.length );
				}
			}
	
			if ( !matched ) {
				break;
			}
		}
	
		// Return the length of the invalid excess
		// if we're just parsing
		// Otherwise, throw an error or return tokens
		return parseOnly ?
			soFar.length :
			soFar ?
				Sizzle.error( selector ) :
				// Cache the tokens
				tokenCache( selector, groups ).slice( 0 );
	};
	
	function toSelector( tokens ) {
		var i = 0,
			len = tokens.length,
			selector = "";
		for ( ; i < len; i++ ) {
			selector += tokens[i].value;
		}
		return selector;
	}
	
	function addCombinator( matcher, combinator, base ) {
		var dir = combinator.dir,
			checkNonElements = base && dir === "parentNode",
			doneName = done++;
	
		return combinator.first ?
			// Check against closest ancestor/preceding element
			function( elem, context, xml ) {
				while ( (elem = elem[ dir ]) ) {
					if ( elem.nodeType === 1 || checkNonElements ) {
						return matcher( elem, context, xml );
					}
				}
			} :
	
			// Check against all ancestor/preceding elements
			function( elem, context, xml ) {
				var oldCache, uniqueCache, outerCache,
					newCache = [ dirruns, doneName ];
	
				// We can't set arbitrary data on XML nodes, so they don't benefit from combinator caching
				if ( xml ) {
					while ( (elem = elem[ dir ]) ) {
						if ( elem.nodeType === 1 || checkNonElements ) {
							if ( matcher( elem, context, xml ) ) {
								return true;
							}
						}
					}
				} else {
					while ( (elem = elem[ dir ]) ) {
						if ( elem.nodeType === 1 || checkNonElements ) {
							outerCache = elem[ expando ] || (elem[ expando ] = {});
	
							// Support: IE <9 only
							// Defend against cloned attroperties (jQuery gh-1709)
							uniqueCache = outerCache[ elem.uniqueID ] || (outerCache[ elem.uniqueID ] = {});
	
							if ( (oldCache = uniqueCache[ dir ]) &&
								oldCache[ 0 ] === dirruns && oldCache[ 1 ] === doneName ) {
	
								// Assign to newCache so results back-propagate to previous elements
								return (newCache[ 2 ] = oldCache[ 2 ]);
							} else {
								// Reuse newcache so results back-propagate to previous elements
								uniqueCache[ dir ] = newCache;
	
								// A match means we're done; a fail means we have to keep checking
								if ( (newCache[ 2 ] = matcher( elem, context, xml )) ) {
									return true;
								}
							}
						}
					}
				}
			};
	}
	
	function elementMatcher( matchers ) {
		return matchers.length > 1 ?
			function( elem, context, xml ) {
				var i = matchers.length;
				while ( i-- ) {
					if ( !matchers[i]( elem, context, xml ) ) {
						return false;
					}
				}
				return true;
			} :
			matchers[0];
	}
	
	function multipleContexts( selector, contexts, results ) {
		var i = 0,
			len = contexts.length;
		for ( ; i < len; i++ ) {
			Sizzle( selector, contexts[i], results );
		}
		return results;
	}
	
	function condense( unmatched, map, filter, context, xml ) {
		var elem,
			newUnmatched = [],
			i = 0,
			len = unmatched.length,
			mapped = map != null;
	
		for ( ; i < len; i++ ) {
			if ( (elem = unmatched[i]) ) {
				if ( !filter || filter( elem, context, xml ) ) {
					newUnmatched.push( elem );
					if ( mapped ) {
						map.push( i );
					}
				}
			}
		}
	
		return newUnmatched;
	}
	
	function setMatcher( preFilter, selector, matcher, postFilter, postFinder, postSelector ) {
		if ( postFilter && !postFilter[ expando ] ) {
			postFilter = setMatcher( postFilter );
		}
		if ( postFinder && !postFinder[ expando ] ) {
			postFinder = setMatcher( postFinder, postSelector );
		}
		return markFunction(function( seed, results, context, xml ) {
			var temp, i, elem,
				preMap = [],
				postMap = [],
				preexisting = results.length,
	
				// Get initial elements from seed or context
				elems = seed || multipleContexts( selector || "*", context.nodeType ? [ context ] : context, [] ),
	
				// Prefilter to get matcher input, preserving a map for seed-results synchronization
				matcherIn = preFilter && ( seed || !selector ) ?
					condense( elems, preMap, preFilter, context, xml ) :
					elems,
	
				matcherOut = matcher ?
					// If we have a postFinder, or filtered seed, or non-seed postFilter or preexisting results,
					postFinder || ( seed ? preFilter : preexisting || postFilter ) ?
	
						// ...intermediate processing is necessary
						[] :
	
						// ...otherwise use results directly
						results :
					matcherIn;
	
			// Find primary matches
			if ( matcher ) {
				matcher( matcherIn, matcherOut, context, xml );
			}
	
			// Apply postFilter
			if ( postFilter ) {
				temp = condense( matcherOut, postMap );
				postFilter( temp, [], context, xml );
	
				// Un-match failing elements by moving them back to matcherIn
				i = temp.length;
				while ( i-- ) {
					if ( (elem = temp[i]) ) {
						matcherOut[ postMap[i] ] = !(matcherIn[ postMap[i] ] = elem);
					}
				}
			}
	
			if ( seed ) {
				if ( postFinder || preFilter ) {
					if ( postFinder ) {
						// Get the final matcherOut by condensing this intermediate into postFinder contexts
						temp = [];
						i = matcherOut.length;
						while ( i-- ) {
							if ( (elem = matcherOut[i]) ) {
								// Restore matcherIn since elem is not yet a final match
								temp.push( (matcherIn[i] = elem) );
							}
						}
						postFinder( null, (matcherOut = []), temp, xml );
					}
	
					// Move matched elements from seed to results to keep them synchronized
					i = matcherOut.length;
					while ( i-- ) {
						if ( (elem = matcherOut[i]) &&
							(temp = postFinder ? indexOf( seed, elem ) : preMap[i]) > -1 ) {
	
							seed[temp] = !(results[temp] = elem);
						}
					}
				}
	
			// Add elements to results, through postFinder if defined
			} else {
				matcherOut = condense(
					matcherOut === results ?
						matcherOut.splice( preexisting, matcherOut.length ) :
						matcherOut
				);
				if ( postFinder ) {
					postFinder( null, results, matcherOut, xml );
				} else {
					push.apply( results, matcherOut );
				}
			}
		});
	}
	
	function matcherFromTokens( tokens ) {
		var checkContext, matcher, j,
			len = tokens.length,
			leadingRelative = Expr.relative[ tokens[0].type ],
			implicitRelative = leadingRelative || Expr.relative[" "],
			i = leadingRelative ? 1 : 0,
	
			// The foundational matcher ensures that elements are reachable from top-level context(s)
			matchContext = addCombinator( function( elem ) {
				return elem === checkContext;
			}, implicitRelative, true ),
			matchAnyContext = addCombinator( function( elem ) {
				return indexOf( checkContext, elem ) > -1;
			}, implicitRelative, true ),
			matchers = [ function( elem, context, xml ) {
				var ret = ( !leadingRelative && ( xml || context !== outermostContext ) ) || (
					(checkContext = context).nodeType ?
						matchContext( elem, context, xml ) :
						matchAnyContext( elem, context, xml ) );
				// Avoid hanging onto element (issue #299)
				checkContext = null;
				return ret;
			} ];
	
		for ( ; i < len; i++ ) {
			if ( (matcher = Expr.relative[ tokens[i].type ]) ) {
				matchers = [ addCombinator(elementMatcher( matchers ), matcher) ];
			} else {
				matcher = Expr.filter[ tokens[i].type ].apply( null, tokens[i].matches );
	
				// Return special upon seeing a positional matcher
				if ( matcher[ expando ] ) {
					// Find the next relative operator (if any) for proper handling
					j = ++i;
					for ( ; j < len; j++ ) {
						if ( Expr.relative[ tokens[j].type ] ) {
							break;
						}
					}
					return setMatcher(
						i > 1 && elementMatcher( matchers ),
						i > 1 && toSelector(
							// If the preceding token was a descendant combinator, insert an implicit any-element `*`
							tokens.slice( 0, i - 1 ).concat({ value: tokens[ i - 2 ].type === " " ? "*" : "" })
						).replace( rtrim, "$1" ),
						matcher,
						i < j && matcherFromTokens( tokens.slice( i, j ) ),
						j < len && matcherFromTokens( (tokens = tokens.slice( j )) ),
						j < len && toSelector( tokens )
					);
				}
				matchers.push( matcher );
			}
		}
	
		return elementMatcher( matchers );
	}
	
	function matcherFromGroupMatchers( elementMatchers, setMatchers ) {
		var bySet = setMatchers.length > 0,
			byElement = elementMatchers.length > 0,
			superMatcher = function( seed, context, xml, results, outermost ) {
				var elem, j, matcher,
					matchedCount = 0,
					i = "0",
					unmatched = seed && [],
					setMatched = [],
					contextBackup = outermostContext,
					// We must always have either seed elements or outermost context
					elems = seed || byElement && Expr.find["TAG"]( "*", outermost ),
					// Use integer dirruns iff this is the outermost matcher
					dirrunsUnique = (dirruns += contextBackup == null ? 1 : Math.random() || 0.1),
					len = elems.length;
	
				if ( outermost ) {
					outermostContext = context === document || context || outermost;
				}
	
				// Add elements passing elementMatchers directly to results
				// Support: IE<9, Safari
				// Tolerate NodeList properties (IE: "length"; Safari: <number>) matching elements by id
				for ( ; i !== len && (elem = elems[i]) != null; i++ ) {
					if ( byElement && elem ) {
						j = 0;
						if ( !context && elem.ownerDocument !== document ) {
							setDocument( elem );
							xml = !documentIsHTML;
						}
						while ( (matcher = elementMatchers[j++]) ) {
							if ( matcher( elem, context || document, xml) ) {
								results.push( elem );
								break;
							}
						}
						if ( outermost ) {
							dirruns = dirrunsUnique;
						}
					}
	
					// Track unmatched elements for set filters
					if ( bySet ) {
						// They will have gone through all possible matchers
						if ( (elem = !matcher && elem) ) {
							matchedCount--;
						}
	
						// Lengthen the array for every element, matched or not
						if ( seed ) {
							unmatched.push( elem );
						}
					}
				}
	
				// `i` is now the count of elements visited above, and adding it to `matchedCount`
				// makes the latter nonnegative.
				matchedCount += i;
	
				// Apply set filters to unmatched elements
				// NOTE: This can be skipped if there are no unmatched elements (i.e., `matchedCount`
				// equals `i`), unless we didn't visit _any_ elements in the above loop because we have
				// no element matchers and no seed.
				// Incrementing an initially-string "0" `i` allows `i` to remain a string only in that
				// case, which will result in a "00" `matchedCount` that differs from `i` but is also
				// numerically zero.
				if ( bySet && i !== matchedCount ) {
					j = 0;
					while ( (matcher = setMatchers[j++]) ) {
						matcher( unmatched, setMatched, context, xml );
					}
	
					if ( seed ) {
						// Reintegrate element matches to eliminate the need for sorting
						if ( matchedCount > 0 ) {
							while ( i-- ) {
								if ( !(unmatched[i] || setMatched[i]) ) {
									setMatched[i] = pop.call( results );
								}
							}
						}
	
						// Discard index placeholder values to get only actual matches
						setMatched = condense( setMatched );
					}
	
					// Add matches to results
					push.apply( results, setMatched );
	
					// Seedless set matches succeeding multiple successful matchers stipulate sorting
					if ( outermost && !seed && setMatched.length > 0 &&
						( matchedCount + setMatchers.length ) > 1 ) {
	
						Sizzle.uniqueSort( results );
					}
				}
	
				// Override manipulation of globals by nested matchers
				if ( outermost ) {
					dirruns = dirrunsUnique;
					outermostContext = contextBackup;
				}
	
				return unmatched;
			};
	
		return bySet ?
			markFunction( superMatcher ) :
			superMatcher;
	}
	
	compile = Sizzle.compile = function( selector, match /* Internal Use Only */ ) {
		var i,
			setMatchers = [],
			elementMatchers = [],
			cached = compilerCache[ selector + " " ];
	
		if ( !cached ) {
			// Generate a function of recursive functions that can be used to check each element
			if ( !match ) {
				match = tokenize( selector );
			}
			i = match.length;
			while ( i-- ) {
				cached = matcherFromTokens( match[i] );
				if ( cached[ expando ] ) {
					setMatchers.push( cached );
				} else {
					elementMatchers.push( cached );
				}
			}
	
			// Cache the compiled function
			cached = compilerCache( selector, matcherFromGroupMatchers( elementMatchers, setMatchers ) );
	
			// Save selector and tokenization
			cached.selector = selector;
		}
		return cached;
	};
	
	/**
	 * A low-level selection function that works with Sizzle's compiled
	 *  selector functions
	 * @param {String|Function} selector A selector or a pre-compiled
	 *  selector function built with Sizzle.compile
	 * @param {Element} context
	 * @param {Array} [results]
	 * @param {Array} [seed] A set of elements to match against
	 */
	select = Sizzle.select = function( selector, context, results, seed ) {
		var i, tokens, token, type, find,
			compiled = typeof selector === "function" && selector,
			match = !seed && tokenize( (selector = compiled.selector || selector) );
	
		results = results || [];
	
		// Try to minimize operations if there is only one selector in the list and no seed
		// (the latter of which guarantees us context)
		if ( match.length === 1 ) {
	
			// Reduce context if the leading compound selector is an ID
			tokens = match[0] = match[0].slice( 0 );
			if ( tokens.length > 2 && (token = tokens[0]).type === "ID" &&
					support.getById && context.nodeType === 9 && documentIsHTML &&
					Expr.relative[ tokens[1].type ] ) {
	
				context = ( Expr.find["ID"]( token.matches[0].replace(runescape, funescape), context ) || [] )[0];
				if ( !context ) {
					return results;
	
				// Precompiled matchers will still verify ancestry, so step up a level
				} else if ( compiled ) {
					context = context.parentNode;
				}
	
				selector = selector.slice( tokens.shift().value.length );
			}
	
			// Fetch a seed set for right-to-left matching
			i = matchExpr["needsContext"].test( selector ) ? 0 : tokens.length;
			while ( i-- ) {
				token = tokens[i];
	
				// Abort if we hit a combinator
				if ( Expr.relative[ (type = token.type) ] ) {
					break;
				}
				if ( (find = Expr.find[ type ]) ) {
					// Search, expanding context for leading sibling combinators
					if ( (seed = find(
						token.matches[0].replace( runescape, funescape ),
						rsibling.test( tokens[0].type ) && testContext( context.parentNode ) || context
					)) ) {
	
						// If seed is empty or no tokens remain, we can return early
						tokens.splice( i, 1 );
						selector = seed.length && toSelector( tokens );
						if ( !selector ) {
							push.apply( results, seed );
							return results;
						}
	
						break;
					}
				}
			}
		}
	
		// Compile and execute a filtering function if one is not provided
		// Provide `match` to avoid retokenization if we modified the selector above
		( compiled || compile( selector, match ) )(
			seed,
			context,
			!documentIsHTML,
			results,
			!context || rsibling.test( selector ) && testContext( context.parentNode ) || context
		);
		return results;
	};
	
	// One-time assignments
	
	// Sort stability
	support.sortStable = expando.split("").sort( sortOrder ).join("") === expando;
	
	// Support: Chrome 14-35+
	// Always assume duplicates if they aren't passed to the comparison function
	support.detectDuplicates = !!hasDuplicate;
	
	// Initialize against the default document
	setDocument();
	
	// Support: Webkit<537.32 - Safari 6.0.3/Chrome 25 (fixed in Chrome 27)
	// Detached nodes confoundingly follow *each other*
	support.sortDetached = assert(function( div1 ) {
		// Should return 1, but returns 4 (following)
		return div1.compareDocumentPosition( document.createElement("div") ) & 1;
	});
	
	// Support: IE<8
	// Prevent attribute/property "interpolation"
	// http://msdn.microsoft.com/en-us/library/ms536429%28VS.85%29.aspx
	if ( !assert(function( div ) {
		div.innerHTML = "<a href='#'></a>";
		return div.firstChild.getAttribute("href") === "#" ;
	}) ) {
		addHandle( "type|href|height|width", function( elem, name, isXML ) {
			if ( !isXML ) {
				return elem.getAttribute( name, name.toLowerCase() === "type" ? 1 : 2 );
			}
		});
	}
	
	// Support: IE<9
	// Use defaultValue in place of getAttribute("value")
	if ( !support.attributes || !assert(function( div ) {
		div.innerHTML = "<input/>";
		div.firstChild.setAttribute( "value", "" );
		return div.firstChild.getAttribute( "value" ) === "";
	}) ) {
		addHandle( "value", function( elem, name, isXML ) {
			if ( !isXML && elem.nodeName.toLowerCase() === "input" ) {
				return elem.defaultValue;
			}
		});
	}
	
	// Support: IE<9
	// Use getAttributeNode to fetch booleans when getAttribute lies
	if ( !assert(function( div ) {
		return div.getAttribute("disabled") == null;
	}) ) {
		addHandle( booleans, function( elem, name, isXML ) {
			var val;
			if ( !isXML ) {
				return elem[ name ] === true ? name.toLowerCase() :
						(val = elem.getAttributeNode( name )) && val.specified ?
						val.value :
					null;
			}
		});
	}
	
	return Sizzle;
	
	})( window );
	
	
	
	jQuery.find = Sizzle;
	jQuery.expr = Sizzle.selectors;
	jQuery.expr[ ":" ] = jQuery.expr.pseudos;
	jQuery.uniqueSort = jQuery.unique = Sizzle.uniqueSort;
	jQuery.text = Sizzle.getText;
	jQuery.isXMLDoc = Sizzle.isXML;
	jQuery.contains = Sizzle.contains;
	
	
	
	var dir = function( elem, dir, until ) {
		var matched = [],
			truncate = until !== undefined;
	
		while ( ( elem = elem[ dir ] ) && elem.nodeType !== 9 ) {
			if ( elem.nodeType === 1 ) {
				if ( truncate && jQuery( elem ).is( until ) ) {
					break;
				}
				matched.push( elem );
			}
		}
		return matched;
	};
	
	
	var siblings = function( n, elem ) {
		var matched = [];
	
		for ( ; n; n = n.nextSibling ) {
			if ( n.nodeType === 1 && n !== elem ) {
				matched.push( n );
			}
		}
	
		return matched;
	};
	
	
	var rneedsContext = jQuery.expr.match.needsContext;
	
	var rsingleTag = ( /^<([\w-]+)\s*\/?>(?:<\/\1>|)$/ );
	
	
	
	var risSimple = /^.[^:#\[\.,]*$/;
	
	// Implement the identical functionality for filter and not
	function winnow( elements, qualifier, not ) {
		if ( jQuery.isFunction( qualifier ) ) {
			return jQuery.grep( elements, function( elem, i ) {
				/* jshint -W018 */
				return !!qualifier.call( elem, i, elem ) !== not;
			} );
	
		}
	
		if ( qualifier.nodeType ) {
			return jQuery.grep( elements, function( elem ) {
				return ( elem === qualifier ) !== not;
			} );
	
		}
	
		if ( typeof qualifier === "string" ) {
			if ( risSimple.test( qualifier ) ) {
				return jQuery.filter( qualifier, elements, not );
			}
	
			qualifier = jQuery.filter( qualifier, elements );
		}
	
		return jQuery.grep( elements, function( elem ) {
			return ( indexOf.call( qualifier, elem ) > -1 ) !== not;
		} );
	}
	
	jQuery.filter = function( expr, elems, not ) {
		var elem = elems[ 0 ];
	
		if ( not ) {
			expr = ":not(" + expr + ")";
		}
	
		return elems.length === 1 && elem.nodeType === 1 ?
			jQuery.find.matchesSelector( elem, expr ) ? [ elem ] : [] :
			jQuery.find.matches( expr, jQuery.grep( elems, function( elem ) {
				return elem.nodeType === 1;
			} ) );
	};
	
	jQuery.fn.extend( {
		find: function( selector ) {
			var i,
				len = this.length,
				ret = [],
				self = this;
	
			if ( typeof selector !== "string" ) {
				return this.pushStack( jQuery( selector ).filter( function() {
					for ( i = 0; i < len; i++ ) {
						if ( jQuery.contains( self[ i ], this ) ) {
							return true;
						}
					}
				} ) );
			}
	
			for ( i = 0; i < len; i++ ) {
				jQuery.find( selector, self[ i ], ret );
			}
	
			// Needed because $( selector, context ) becomes $( context ).find( selector )
			ret = this.pushStack( len > 1 ? jQuery.unique( ret ) : ret );
			ret.selector = this.selector ? this.selector + " " + selector : selector;
			return ret;
		},
		filter: function( selector ) {
			return this.pushStack( winnow( this, selector || [], false ) );
		},
		not: function( selector ) {
			return this.pushStack( winnow( this, selector || [], true ) );
		},
		is: function( selector ) {
			return !!winnow(
				this,
	
				// If this is a positional/relative selector, check membership in the returned set
				// so $("p:first").is("p:last") won't return true for a doc with two "p".
				typeof selector === "string" && rneedsContext.test( selector ) ?
					jQuery( selector ) :
					selector || [],
				false
			).length;
		}
	} );
	
	
	// Initialize a jQuery object
	
	
	// A central reference to the root jQuery(document)
	var rootjQuery,
	
		// A simple way to check for HTML strings
		// Prioritize #id over <tag> to avoid XSS via location.hash (#9521)
		// Strict HTML recognition (#11290: must start with <)
		rquickExpr = /^(?:\s*(<[\w\W]+>)[^>]*|#([\w-]*))$/,
	
		init = jQuery.fn.init = function( selector, context, root ) {
			var match, elem;
	
			// HANDLE: $(""), $(null), $(undefined), $(false)
			if ( !selector ) {
				return this;
			}
	
			// Method init() accepts an alternate rootjQuery
			// so migrate can support jQuery.sub (gh-2101)
			root = root || rootjQuery;
	
			// Handle HTML strings
			if ( typeof selector === "string" ) {
				if ( selector[ 0 ] === "<" &&
					selector[ selector.length - 1 ] === ">" &&
					selector.length >= 3 ) {
	
					// Assume that strings that start and end with <> are HTML and skip the regex check
					match = [ null, selector, null ];
	
				} else {
					match = rquickExpr.exec( selector );
				}
	
				// Match html or make sure no context is specified for #id
				if ( match && ( match[ 1 ] || !context ) ) {
	
					// HANDLE: $(html) -> $(array)
					if ( match[ 1 ] ) {
						context = context instanceof jQuery ? context[ 0 ] : context;
	
						// Option to run scripts is true for back-compat
						// Intentionally let the error be thrown if parseHTML is not present
						jQuery.merge( this, jQuery.parseHTML(
							match[ 1 ],
							context && context.nodeType ? context.ownerDocument || context : document,
							true
						) );
	
						// HANDLE: $(html, props)
						if ( rsingleTag.test( match[ 1 ] ) && jQuery.isPlainObject( context ) ) {
							for ( match in context ) {
	
								// Properties of context are called as methods if possible
								if ( jQuery.isFunction( this[ match ] ) ) {
									this[ match ]( context[ match ] );
	
								// ...and otherwise set as attributes
								} else {
									this.attr( match, context[ match ] );
								}
							}
						}
	
						return this;
	
					// HANDLE: $(#id)
					} else {
						elem = document.getElementById( match[ 2 ] );
	
						// Support: Blackberry 4.6
						// gEBID returns nodes no longer in the document (#6963)
						if ( elem && elem.parentNode ) {
	
							// Inject the element directly into the jQuery object
							this.length = 1;
							this[ 0 ] = elem;
						}
	
						this.context = document;
						this.selector = selector;
						return this;
					}
	
				// HANDLE: $(expr, $(...))
				} else if ( !context || context.jquery ) {
					return ( context || root ).find( selector );
	
				// HANDLE: $(expr, context)
				// (which is just equivalent to: $(context).find(expr)
				} else {
					return this.constructor( context ).find( selector );
				}
	
			// HANDLE: $(DOMElement)
			} else if ( selector.nodeType ) {
				this.context = this[ 0 ] = selector;
				this.length = 1;
				return this;
	
			// HANDLE: $(function)
			// Shortcut for document ready
			} else if ( jQuery.isFunction( selector ) ) {
				return root.ready !== undefined ?
					root.ready( selector ) :
	
					// Execute immediately if ready is not present
					selector( jQuery );
			}
	
			if ( selector.selector !== undefined ) {
				this.selector = selector.selector;
				this.context = selector.context;
			}
	
			return jQuery.makeArray( selector, this );
		};
	
	// Give the init function the jQuery prototype for later instantiation
	init.prototype = jQuery.fn;
	
	// Initialize central reference
	rootjQuery = jQuery( document );
	
	
	var rparentsprev = /^(?:parents|prev(?:Until|All))/,
	
		// Methods guaranteed to produce a unique set when starting from a unique set
		guaranteedUnique = {
			children: true,
			contents: true,
			next: true,
			prev: true
		};
	
	jQuery.fn.extend( {
		has: function( target ) {
			var targets = jQuery( target, this ),
				l = targets.length;
	
			return this.filter( function() {
				var i = 0;
				for ( ; i < l; i++ ) {
					if ( jQuery.contains( this, targets[ i ] ) ) {
						return true;
					}
				}
			} );
		},
	
		closest: function( selectors, context ) {
			var cur,
				i = 0,
				l = this.length,
				matched = [],
				pos = rneedsContext.test( selectors ) || typeof selectors !== "string" ?
					jQuery( selectors, context || this.context ) :
					0;
	
			for ( ; i < l; i++ ) {
				for ( cur = this[ i ]; cur && cur !== context; cur = cur.parentNode ) {
	
					// Always skip document fragments
					if ( cur.nodeType < 11 && ( pos ?
						pos.index( cur ) > -1 :
	
						// Don't pass non-elements to Sizzle
						cur.nodeType === 1 &&
							jQuery.find.matchesSelector( cur, selectors ) ) ) {
	
						matched.push( cur );
						break;
					}
				}
			}
	
			return this.pushStack( matched.length > 1 ? jQuery.uniqueSort( matched ) : matched );
		},
	
		// Determine the position of an element within the set
		index: function( elem ) {
	
			// No argument, return index in parent
			if ( !elem ) {
				return ( this[ 0 ] && this[ 0 ].parentNode ) ? this.first().prevAll().length : -1;
			}
	
			// Index in selector
			if ( typeof elem === "string" ) {
				return indexOf.call( jQuery( elem ), this[ 0 ] );
			}
	
			// Locate the position of the desired element
			return indexOf.call( this,
	
				// If it receives a jQuery object, the first element is used
				elem.jquery ? elem[ 0 ] : elem
			);
		},
	
		add: function( selector, context ) {
			return this.pushStack(
				jQuery.uniqueSort(
					jQuery.merge( this.get(), jQuery( selector, context ) )
				)
			);
		},
	
		addBack: function( selector ) {
			return this.add( selector == null ?
				this.prevObject : this.prevObject.filter( selector )
			);
		}
	} );
	
	function sibling( cur, dir ) {
		while ( ( cur = cur[ dir ] ) && cur.nodeType !== 1 ) {}
		return cur;
	}
	
	jQuery.each( {
		parent: function( elem ) {
			var parent = elem.parentNode;
			return parent && parent.nodeType !== 11 ? parent : null;
		},
		parents: function( elem ) {
			return dir( elem, "parentNode" );
		},
		parentsUntil: function( elem, i, until ) {
			return dir( elem, "parentNode", until );
		},
		next: function( elem ) {
			return sibling( elem, "nextSibling" );
		},
		prev: function( elem ) {
			return sibling( elem, "previousSibling" );
		},
		nextAll: function( elem ) {
			return dir( elem, "nextSibling" );
		},
		prevAll: function( elem ) {
			return dir( elem, "previousSibling" );
		},
		nextUntil: function( elem, i, until ) {
			return dir( elem, "nextSibling", until );
		},
		prevUntil: function( elem, i, until ) {
			return dir( elem, "previousSibling", until );
		},
		siblings: function( elem ) {
			return siblings( ( elem.parentNode || {} ).firstChild, elem );
		},
		children: function( elem ) {
			return siblings( elem.firstChild );
		},
		contents: function( elem ) {
			return elem.contentDocument || jQuery.merge( [], elem.childNodes );
		}
	}, function( name, fn ) {
		jQuery.fn[ name ] = function( until, selector ) {
			var matched = jQuery.map( this, fn, until );
	
			if ( name.slice( -5 ) !== "Until" ) {
				selector = until;
			}
	
			if ( selector && typeof selector === "string" ) {
				matched = jQuery.filter( selector, matched );
			}
	
			if ( this.length > 1 ) {
	
				// Remove duplicates
				if ( !guaranteedUnique[ name ] ) {
					jQuery.uniqueSort( matched );
				}
	
				// Reverse order for parents* and prev-derivatives
				if ( rparentsprev.test( name ) ) {
					matched.reverse();
				}
			}
	
			return this.pushStack( matched );
		};
	} );
	var rnotwhite = ( /\S+/g );
	
	
	
	// Convert String-formatted options into Object-formatted ones
	function createOptions( options ) {
		var object = {};
		jQuery.each( options.match( rnotwhite ) || [], function( _, flag ) {
			object[ flag ] = true;
		} );
		return object;
	}
	
	/*
	 * Create a callback list using the following parameters:
	 *
	 *	options: an optional list of space-separated options that will change how
	 *			the callback list behaves or a more traditional option object
	 *
	 * By default a callback list will act like an event callback list and can be
	 * "fired" multiple times.
	 *
	 * Possible options:
	 *
	 *	once:			will ensure the callback list can only be fired once (like a Deferred)
	 *
	 *	memory:			will keep track of previous values and will call any callback added
	 *					after the list has been fired right away with the latest "memorized"
	 *					values (like a Deferred)
	 *
	 *	unique:			will ensure a callback can only be added once (no duplicate in the list)
	 *
	 *	stopOnFalse:	interrupt callings when a callback returns false
	 *
	 */
	jQuery.Callbacks = function( options ) {
	
		// Convert options from String-formatted to Object-formatted if needed
		// (we check in cache first)
		options = typeof options === "string" ?
			createOptions( options ) :
			jQuery.extend( {}, options );
	
		var // Flag to know if list is currently firing
			firing,
	
			// Last fire value for non-forgettable lists
			memory,
	
			// Flag to know if list was already fired
			fired,
	
			// Flag to prevent firing
			locked,
	
			// Actual callback list
			list = [],
	
			// Queue of execution data for repeatable lists
			queue = [],
	
			// Index of currently firing callback (modified by add/remove as needed)
			firingIndex = -1,
	
			// Fire callbacks
			fire = function() {
	
				// Enforce single-firing
				locked = options.once;
	
				// Execute callbacks for all pending executions,
				// respecting firingIndex overrides and runtime changes
				fired = firing = true;
				for ( ; queue.length; firingIndex = -1 ) {
					memory = queue.shift();
					while ( ++firingIndex < list.length ) {
	
						// Run callback and check for early termination
						if ( list[ firingIndex ].apply( memory[ 0 ], memory[ 1 ] ) === false &&
							options.stopOnFalse ) {
	
							// Jump to end and forget the data so .add doesn't re-fire
							firingIndex = list.length;
							memory = false;
						}
					}
				}
	
				// Forget the data if we're done with it
				if ( !options.memory ) {
					memory = false;
				}
	
				firing = false;
	
				// Clean up if we're done firing for good
				if ( locked ) {
	
					// Keep an empty list if we have data for future add calls
					if ( memory ) {
						list = [];
	
					// Otherwise, this object is spent
					} else {
						list = "";
					}
				}
			},
	
			// Actual Callbacks object
			self = {
	
				// Add a callback or a collection of callbacks to the list
				add: function() {
					if ( list ) {
	
						// If we have memory from a past run, we should fire after adding
						if ( memory && !firing ) {
							firingIndex = list.length - 1;
							queue.push( memory );
						}
	
						( function add( args ) {
							jQuery.each( args, function( _, arg ) {
								if ( jQuery.isFunction( arg ) ) {
									if ( !options.unique || !self.has( arg ) ) {
										list.push( arg );
									}
								} else if ( arg && arg.length && jQuery.type( arg ) !== "string" ) {
	
									// Inspect recursively
									add( arg );
								}
							} );
						} )( arguments );
	
						if ( memory && !firing ) {
							fire();
						}
					}
					return this;
				},
	
				// Remove a callback from the list
				remove: function() {
					jQuery.each( arguments, function( _, arg ) {
						var index;
						while ( ( index = jQuery.inArray( arg, list, index ) ) > -1 ) {
							list.splice( index, 1 );
	
							// Handle firing indexes
							if ( index <= firingIndex ) {
								firingIndex--;
							}
						}
					} );
					return this;
				},
	
				// Check if a given callback is in the list.
				// If no argument is given, return whether or not list has callbacks attached.
				has: function( fn ) {
					return fn ?
						jQuery.inArray( fn, list ) > -1 :
						list.length > 0;
				},
	
				// Remove all callbacks from the list
				empty: function() {
					if ( list ) {
						list = [];
					}
					return this;
				},
	
				// Disable .fire and .add
				// Abort any current/pending executions
				// Clear all callbacks and values
				disable: function() {
					locked = queue = [];
					list = memory = "";
					return this;
				},
				disabled: function() {
					return !list;
				},
	
				// Disable .fire
				// Also disable .add unless we have memory (since it would have no effect)
				// Abort any pending executions
				lock: function() {
					locked = queue = [];
					if ( !memory ) {
						list = memory = "";
					}
					return this;
				},
				locked: function() {
					return !!locked;
				},
	
				// Call all callbacks with the given context and arguments
				fireWith: function( context, args ) {
					if ( !locked ) {
						args = args || [];
						args = [ context, args.slice ? args.slice() : args ];
						queue.push( args );
						if ( !firing ) {
							fire();
						}
					}
					return this;
				},
	
				// Call all the callbacks with the given arguments
				fire: function() {
					self.fireWith( this, arguments );
					return this;
				},
	
				// To know if the callbacks have already been called at least once
				fired: function() {
					return !!fired;
				}
			};
	
		return self;
	};
	
	
	jQuery.extend( {
	
		Deferred: function( func ) {
			var tuples = [
	
					// action, add listener, listener list, final state
					[ "resolve", "done", jQuery.Callbacks( "once memory" ), "resolved" ],
					[ "reject", "fail", jQuery.Callbacks( "once memory" ), "rejected" ],
					[ "notify", "progress", jQuery.Callbacks( "memory" ) ]
				],
				state = "pending",
				promise = {
					state: function() {
						return state;
					},
					always: function() {
						deferred.done( arguments ).fail( arguments );
						return this;
					},
					then: function( /* fnDone, fnFail, fnProgress */ ) {
						var fns = arguments;
						return jQuery.Deferred( function( newDefer ) {
							jQuery.each( tuples, function( i, tuple ) {
								var fn = jQuery.isFunction( fns[ i ] ) && fns[ i ];
	
								// deferred[ done | fail | progress ] for forwarding actions to newDefer
								deferred[ tuple[ 1 ] ]( function() {
									var returned = fn && fn.apply( this, arguments );
									if ( returned && jQuery.isFunction( returned.promise ) ) {
										returned.promise()
											.progress( newDefer.notify )
											.done( newDefer.resolve )
											.fail( newDefer.reject );
									} else {
										newDefer[ tuple[ 0 ] + "With" ](
											this === promise ? newDefer.promise() : this,
											fn ? [ returned ] : arguments
										);
									}
								} );
							} );
							fns = null;
						} ).promise();
					},
	
					// Get a promise for this deferred
					// If obj is provided, the promise aspect is added to the object
					promise: function( obj ) {
						return obj != null ? jQuery.extend( obj, promise ) : promise;
					}
				},
				deferred = {};
	
			// Keep pipe for back-compat
			promise.pipe = promise.then;
	
			// Add list-specific methods
			jQuery.each( tuples, function( i, tuple ) {
				var list = tuple[ 2 ],
					stateString = tuple[ 3 ];
	
				// promise[ done | fail | progress ] = list.add
				promise[ tuple[ 1 ] ] = list.add;
	
				// Handle state
				if ( stateString ) {
					list.add( function() {
	
						// state = [ resolved | rejected ]
						state = stateString;
	
					// [ reject_list | resolve_list ].disable; progress_list.lock
					}, tuples[ i ^ 1 ][ 2 ].disable, tuples[ 2 ][ 2 ].lock );
				}
	
				// deferred[ resolve | reject | notify ]
				deferred[ tuple[ 0 ] ] = function() {
					deferred[ tuple[ 0 ] + "With" ]( this === deferred ? promise : this, arguments );
					return this;
				};
				deferred[ tuple[ 0 ] + "With" ] = list.fireWith;
			} );
	
			// Make the deferred a promise
			promise.promise( deferred );
	
			// Call given func if any
			if ( func ) {
				func.call( deferred, deferred );
			}
	
			// All done!
			return deferred;
		},
	
		// Deferred helper
		when: function( subordinate /* , ..., subordinateN */ ) {
			var i = 0,
				resolveValues = slice.call( arguments ),
				length = resolveValues.length,
	
				// the count of uncompleted subordinates
				remaining = length !== 1 ||
					( subordinate && jQuery.isFunction( subordinate.promise ) ) ? length : 0,
	
				// the master Deferred.
				// If resolveValues consist of only a single Deferred, just use that.
				deferred = remaining === 1 ? subordinate : jQuery.Deferred(),
	
				// Update function for both resolve and progress values
				updateFunc = function( i, contexts, values ) {
					return function( value ) {
						contexts[ i ] = this;
						values[ i ] = arguments.length > 1 ? slice.call( arguments ) : value;
						if ( values === progressValues ) {
							deferred.notifyWith( contexts, values );
						} else if ( !( --remaining ) ) {
							deferred.resolveWith( contexts, values );
						}
					};
				},
	
				progressValues, progressContexts, resolveContexts;
	
			// Add listeners to Deferred subordinates; treat others as resolved
			if ( length > 1 ) {
				progressValues = new Array( length );
				progressContexts = new Array( length );
				resolveContexts = new Array( length );
				for ( ; i < length; i++ ) {
					if ( resolveValues[ i ] && jQuery.isFunction( resolveValues[ i ].promise ) ) {
						resolveValues[ i ].promise()
							.progress( updateFunc( i, progressContexts, progressValues ) )
							.done( updateFunc( i, resolveContexts, resolveValues ) )
							.fail( deferred.reject );
					} else {
						--remaining;
					}
				}
			}
	
			// If we're not waiting on anything, resolve the master
			if ( !remaining ) {
				deferred.resolveWith( resolveContexts, resolveValues );
			}
	
			return deferred.promise();
		}
	} );
	
	
	// The deferred used on DOM ready
	var readyList;
	
	jQuery.fn.ready = function( fn ) {
	
		// Add the callback
		jQuery.ready.promise().done( fn );
	
		return this;
	};
	
	jQuery.extend( {
	
		// Is the DOM ready to be used? Set to true once it occurs.
		isReady: false,
	
		// A counter to track how many items to wait for before
		// the ready event fires. See #6781
		readyWait: 1,
	
		// Hold (or release) the ready event
		holdReady: function( hold ) {
			if ( hold ) {
				jQuery.readyWait++;
			} else {
				jQuery.ready( true );
			}
		},
	
		// Handle when the DOM is ready
		ready: function( wait ) {
	
			// Abort if there are pending holds or we're already ready
			if ( wait === true ? --jQuery.readyWait : jQuery.isReady ) {
				return;
			}
	
			// Remember that the DOM is ready
			jQuery.isReady = true;
	
			// If a normal DOM Ready event fired, decrement, and wait if need be
			if ( wait !== true && --jQuery.readyWait > 0 ) {
				return;
			}
	
			// If there are functions bound, to execute
			readyList.resolveWith( document, [ jQuery ] );
	
			// Trigger any bound ready events
			if ( jQuery.fn.triggerHandler ) {
				jQuery( document ).triggerHandler( "ready" );
				jQuery( document ).off( "ready" );
			}
		}
	} );
	
	/**
	 * The ready event handler and self cleanup method
	 */
	function completed() {
		document.removeEventListener( "DOMContentLoaded", completed );
		window.removeEventListener( "load", completed );
		jQuery.ready();
	}
	
	jQuery.ready.promise = function( obj ) {
		if ( !readyList ) {
	
			readyList = jQuery.Deferred();
	
			// Catch cases where $(document).ready() is called
			// after the browser event has already occurred.
			// Support: IE9-10 only
			// Older IE sometimes signals "interactive" too soon
			if ( document.readyState === "complete" ||
				( document.readyState !== "loading" && !document.documentElement.doScroll ) ) {
	
				// Handle it asynchronously to allow scripts the opportunity to delay ready
				window.setTimeout( jQuery.ready );
	
			} else {
	
				// Use the handy event callback
				document.addEventListener( "DOMContentLoaded", completed );
	
				// A fallback to window.onload, that will always work
				window.addEventListener( "load", completed );
			}
		}
		return readyList.promise( obj );
	};
	
	// Kick off the DOM ready check even if the user does not
	jQuery.ready.promise();
	
	
	
	
	// Multifunctional method to get and set values of a collection
	// The value/s can optionally be executed if it's a function
	var access = function( elems, fn, key, value, chainable, emptyGet, raw ) {
		var i = 0,
			len = elems.length,
			bulk = key == null;
	
		// Sets many values
		if ( jQuery.type( key ) === "object" ) {
			chainable = true;
			for ( i in key ) {
				access( elems, fn, i, key[ i ], true, emptyGet, raw );
			}
	
		// Sets one value
		} else if ( value !== undefined ) {
			chainable = true;
	
			if ( !jQuery.isFunction( value ) ) {
				raw = true;
			}
	
			if ( bulk ) {
	
				// Bulk operations run against the entire set
				if ( raw ) {
					fn.call( elems, value );
					fn = null;
	
				// ...except when executing function values
				} else {
					bulk = fn;
					fn = function( elem, key, value ) {
						return bulk.call( jQuery( elem ), value );
					};
				}
			}
	
			if ( fn ) {
				for ( ; i < len; i++ ) {
					fn(
						elems[ i ], key, raw ?
						value :
						value.call( elems[ i ], i, fn( elems[ i ], key ) )
					);
				}
			}
		}
	
		return chainable ?
			elems :
	
			// Gets
			bulk ?
				fn.call( elems ) :
				len ? fn( elems[ 0 ], key ) : emptyGet;
	};
	var acceptData = function( owner ) {
	
		// Accepts only:
		//  - Node
		//    - Node.ELEMENT_NODE
		//    - Node.DOCUMENT_NODE
		//  - Object
		//    - Any
		/* jshint -W018 */
		return owner.nodeType === 1 || owner.nodeType === 9 || !( +owner.nodeType );
	};
	
	
	
	
	function Data() {
		this.expando = jQuery.expando + Data.uid++;
	}
	
	Data.uid = 1;
	
	Data.prototype = {
	
		register: function( owner, initial ) {
			var value = initial || {};
	
			// If it is a node unlikely to be stringify-ed or looped over
			// use plain assignment
			if ( owner.nodeType ) {
				owner[ this.expando ] = value;
	
			// Otherwise secure it in a non-enumerable, non-writable property
			// configurability must be true to allow the property to be
			// deleted with the delete operator
			} else {
				Object.defineProperty( owner, this.expando, {
					value: value,
					writable: true,
					configurable: true
				} );
			}
			return owner[ this.expando ];
		},
		cache: function( owner ) {
	
			// We can accept data for non-element nodes in modern browsers,
			// but we should not, see #8335.
			// Always return an empty object.
			if ( !acceptData( owner ) ) {
				return {};
			}
	
			// Check if the owner object already has a cache
			var value = owner[ this.expando ];
	
			// If not, create one
			if ( !value ) {
				value = {};
	
				// We can accept data for non-element nodes in modern browsers,
				// but we should not, see #8335.
				// Always return an empty object.
				if ( acceptData( owner ) ) {
	
					// If it is a node unlikely to be stringify-ed or looped over
					// use plain assignment
					if ( owner.nodeType ) {
						owner[ this.expando ] = value;
	
					// Otherwise secure it in a non-enumerable property
					// configurable must be true to allow the property to be
					// deleted when data is removed
					} else {
						Object.defineProperty( owner, this.expando, {
							value: value,
							configurable: true
						} );
					}
				}
			}
	
			return value;
		},
		set: function( owner, data, value ) {
			var prop,
				cache = this.cache( owner );
	
			// Handle: [ owner, key, value ] args
			if ( typeof data === "string" ) {
				cache[ data ] = value;
	
			// Handle: [ owner, { properties } ] args
			} else {
	
				// Copy the properties one-by-one to the cache object
				for ( prop in data ) {
					cache[ prop ] = data[ prop ];
				}
			}
			return cache;
		},
		get: function( owner, key ) {
			return key === undefined ?
				this.cache( owner ) :
				owner[ this.expando ] && owner[ this.expando ][ key ];
		},
		access: function( owner, key, value ) {
			var stored;
	
			// In cases where either:
			//
			//   1. No key was specified
			//   2. A string key was specified, but no value provided
			//
			// Take the "read" path and allow the get method to determine
			// which value to return, respectively either:
			//
			//   1. The entire cache object
			//   2. The data stored at the key
			//
			if ( key === undefined ||
					( ( key && typeof key === "string" ) && value === undefined ) ) {
	
				stored = this.get( owner, key );
	
				return stored !== undefined ?
					stored : this.get( owner, jQuery.camelCase( key ) );
			}
	
			// When the key is not a string, or both a key and value
			// are specified, set or extend (existing objects) with either:
			//
			//   1. An object of properties
			//   2. A key and value
			//
			this.set( owner, key, value );
	
			// Since the "set" path can have two possible entry points
			// return the expected data based on which path was taken[*]
			return value !== undefined ? value : key;
		},
		remove: function( owner, key ) {
			var i, name, camel,
				cache = owner[ this.expando ];
	
			if ( cache === undefined ) {
				return;
			}
	
			if ( key === undefined ) {
				this.register( owner );
	
			} else {
	
				// Support array or space separated string of keys
				if ( jQuery.isArray( key ) ) {
	
					// If "name" is an array of keys...
					// When data is initially created, via ("key", "val") signature,
					// keys will be converted to camelCase.
					// Since there is no way to tell _how_ a key was added, remove
					// both plain key and camelCase key. #12786
					// This will only penalize the array argument path.
					name = key.concat( key.map( jQuery.camelCase ) );
				} else {
					camel = jQuery.camelCase( key );
	
					// Try the string as a key before any manipulation
					if ( key in cache ) {
						name = [ key, camel ];
					} else {
	
						// If a key with the spaces exists, use it.
						// Otherwise, create an array by matching non-whitespace
						name = camel;
						name = name in cache ?
							[ name ] : ( name.match( rnotwhite ) || [] );
					}
				}
	
				i = name.length;
	
				while ( i-- ) {
					delete cache[ name[ i ] ];
				}
			}
	
			// Remove the expando if there's no more data
			if ( key === undefined || jQuery.isEmptyObject( cache ) ) {
	
				// Support: Chrome <= 35-45+
				// Webkit & Blink performance suffers when deleting properties
				// from DOM nodes, so set to undefined instead
				// https://code.google.com/p/chromium/issues/detail?id=378607
				if ( owner.nodeType ) {
					owner[ this.expando ] = undefined;
				} else {
					delete owner[ this.expando ];
				}
			}
		},
		hasData: function( owner ) {
			var cache = owner[ this.expando ];
			return cache !== undefined && !jQuery.isEmptyObject( cache );
		}
	};
	var dataPriv = new Data();
	
	var dataUser = new Data();
	
	
	
	//	Implementation Summary
	//
	//	1. Enforce API surface and semantic compatibility with 1.9.x branch
	//	2. Improve the module's maintainability by reducing the storage
	//		paths to a single mechanism.
	//	3. Use the same single mechanism to support "private" and "user" data.
	//	4. _Never_ expose "private" data to user code (TODO: Drop _data, _removeData)
	//	5. Avoid exposing implementation details on user objects (eg. expando properties)
	//	6. Provide a clear path for implementation upgrade to WeakMap in 2014
	
	var rbrace = /^(?:\{[\w\W]*\}|\[[\w\W]*\])$/,
		rmultiDash = /[A-Z]/g;
	
	function dataAttr( elem, key, data ) {
		var name;
	
		// If nothing was found internally, try to fetch any
		// data from the HTML5 data-* attribute
		if ( data === undefined && elem.nodeType === 1 ) {
			name = "data-" + key.replace( rmultiDash, "-$&" ).toLowerCase();
			data = elem.getAttribute( name );
	
			if ( typeof data === "string" ) {
				try {
					data = data === "true" ? true :
						data === "false" ? false :
						data === "null" ? null :
	
						// Only convert to a number if it doesn't change the string
						+data + "" === data ? +data :
						rbrace.test( data ) ? jQuery.parseJSON( data ) :
						data;
				} catch ( e ) {}
	
				// Make sure we set the data so it isn't changed later
				dataUser.set( elem, key, data );
			} else {
				data = undefined;
			}
		}
		return data;
	}
	
	jQuery.extend( {
		hasData: function( elem ) {
			return dataUser.hasData( elem ) || dataPriv.hasData( elem );
		},
	
		data: function( elem, name, data ) {
			return dataUser.access( elem, name, data );
		},
	
		removeData: function( elem, name ) {
			dataUser.remove( elem, name );
		},
	
		// TODO: Now that all calls to _data and _removeData have been replaced
		// with direct calls to dataPriv methods, these can be deprecated.
		_data: function( elem, name, data ) {
			return dataPriv.access( elem, name, data );
		},
	
		_removeData: function( elem, name ) {
			dataPriv.remove( elem, name );
		}
	} );
	
	jQuery.fn.extend( {
		data: function( key, value ) {
			var i, name, data,
				elem = this[ 0 ],
				attrs = elem && elem.attributes;
	
			// Gets all values
			if ( key === undefined ) {
				if ( this.length ) {
					data = dataUser.get( elem );
	
					if ( elem.nodeType === 1 && !dataPriv.get( elem, "hasDataAttrs" ) ) {
						i = attrs.length;
						while ( i-- ) {
	
							// Support: IE11+
							// The attrs elements can be null (#14894)
							if ( attrs[ i ] ) {
								name = attrs[ i ].name;
								if ( name.indexOf( "data-" ) === 0 ) {
									name = jQuery.camelCase( name.slice( 5 ) );
									dataAttr( elem, name, data[ name ] );
								}
							}
						}
						dataPriv.set( elem, "hasDataAttrs", true );
					}
				}
	
				return data;
			}
	
			// Sets multiple values
			if ( typeof key === "object" ) {
				return this.each( function() {
					dataUser.set( this, key );
				} );
			}
	
			return access( this, function( value ) {
				var data, camelKey;
	
				// The calling jQuery object (element matches) is not empty
				// (and therefore has an element appears at this[ 0 ]) and the
				// `value` parameter was not undefined. An empty jQuery object
				// will result in `undefined` for elem = this[ 0 ] which will
				// throw an exception if an attempt to read a data cache is made.
				if ( elem && value === undefined ) {
	
					// Attempt to get data from the cache
					// with the key as-is
					data = dataUser.get( elem, key ) ||
	
						// Try to find dashed key if it exists (gh-2779)
						// This is for 2.2.x only
						dataUser.get( elem, key.replace( rmultiDash, "-$&" ).toLowerCase() );
	
					if ( data !== undefined ) {
						return data;
					}
	
					camelKey = jQuery.camelCase( key );
	
					// Attempt to get data from the cache
					// with the key camelized
					data = dataUser.get( elem, camelKey );
					if ( data !== undefined ) {
						return data;
					}
	
					// Attempt to "discover" the data in
					// HTML5 custom data-* attrs
					data = dataAttr( elem, camelKey, undefined );
					if ( data !== undefined ) {
						return data;
					}
	
					// We tried really hard, but the data doesn't exist.
					return;
				}
	
				// Set the data...
				camelKey = jQuery.camelCase( key );
				this.each( function() {
	
					// First, attempt to store a copy or reference of any
					// data that might've been store with a camelCased key.
					var data = dataUser.get( this, camelKey );
	
					// For HTML5 data-* attribute interop, we have to
					// store property names with dashes in a camelCase form.
					// This might not apply to all properties...*
					dataUser.set( this, camelKey, value );
	
					// *... In the case of properties that might _actually_
					// have dashes, we need to also store a copy of that
					// unchanged property.
					if ( key.indexOf( "-" ) > -1 && data !== undefined ) {
						dataUser.set( this, key, value );
					}
				} );
			}, null, value, arguments.length > 1, null, true );
		},
	
		removeData: function( key ) {
			return this.each( function() {
				dataUser.remove( this, key );
			} );
		}
	} );
	
	
	jQuery.extend( {
		queue: function( elem, type, data ) {
			var queue;
	
			if ( elem ) {
				type = ( type || "fx" ) + "queue";
				queue = dataPriv.get( elem, type );
	
				// Speed up dequeue by getting out quickly if this is just a lookup
				if ( data ) {
					if ( !queue || jQuery.isArray( data ) ) {
						queue = dataPriv.access( elem, type, jQuery.makeArray( data ) );
					} else {
						queue.push( data );
					}
				}
				return queue || [];
			}
		},
	
		dequeue: function( elem, type ) {
			type = type || "fx";
	
			var queue = jQuery.queue( elem, type ),
				startLength = queue.length,
				fn = queue.shift(),
				hooks = jQuery._queueHooks( elem, type ),
				next = function() {
					jQuery.dequeue( elem, type );
				};
	
			// If the fx queue is dequeued, always remove the progress sentinel
			if ( fn === "inprogress" ) {
				fn = queue.shift();
				startLength--;
			}
	
			if ( fn ) {
	
				// Add a progress sentinel to prevent the fx queue from being
				// automatically dequeued
				if ( type === "fx" ) {
					queue.unshift( "inprogress" );
				}
	
				// Clear up the last queue stop function
				delete hooks.stop;
				fn.call( elem, next, hooks );
			}
	
			if ( !startLength && hooks ) {
				hooks.empty.fire();
			}
		},
	
		// Not public - generate a queueHooks object, or return the current one
		_queueHooks: function( elem, type ) {
			var key = type + "queueHooks";
			return dataPriv.get( elem, key ) || dataPriv.access( elem, key, {
				empty: jQuery.Callbacks( "once memory" ).add( function() {
					dataPriv.remove( elem, [ type + "queue", key ] );
				} )
			} );
		}
	} );
	
	jQuery.fn.extend( {
		queue: function( type, data ) {
			var setter = 2;
	
			if ( typeof type !== "string" ) {
				data = type;
				type = "fx";
				setter--;
			}
	
			if ( arguments.length < setter ) {
				return jQuery.queue( this[ 0 ], type );
			}
	
			return data === undefined ?
				this :
				this.each( function() {
					var queue = jQuery.queue( this, type, data );
	
					// Ensure a hooks for this queue
					jQuery._queueHooks( this, type );
	
					if ( type === "fx" && queue[ 0 ] !== "inprogress" ) {
						jQuery.dequeue( this, type );
					}
				} );
		},
		dequeue: function( type ) {
			return this.each( function() {
				jQuery.dequeue( this, type );
			} );
		},
		clearQueue: function( type ) {
			return this.queue( type || "fx", [] );
		},
	
		// Get a promise resolved when queues of a certain type
		// are emptied (fx is the type by default)
		promise: function( type, obj ) {
			var tmp,
				count = 1,
				defer = jQuery.Deferred(),
				elements = this,
				i = this.length,
				resolve = function() {
					if ( !( --count ) ) {
						defer.resolveWith( elements, [ elements ] );
					}
				};
	
			if ( typeof type !== "string" ) {
				obj = type;
				type = undefined;
			}
			type = type || "fx";
	
			while ( i-- ) {
				tmp = dataPriv.get( elements[ i ], type + "queueHooks" );
				if ( tmp && tmp.empty ) {
					count++;
					tmp.empty.add( resolve );
				}
			}
			resolve();
			return defer.promise( obj );
		}
	} );
	var pnum = ( /[+-]?(?:\d*\.|)\d+(?:[eE][+-]?\d+|)/ ).source;
	
	var rcssNum = new RegExp( "^(?:([+-])=|)(" + pnum + ")([a-z%]*)$", "i" );
	
	
	var cssExpand = [ "Top", "Right", "Bottom", "Left" ];
	
	var isHidden = function( elem, el ) {
	
			// isHidden might be called from jQuery#filter function;
			// in that case, element will be second argument
			elem = el || elem;
			return jQuery.css( elem, "display" ) === "none" ||
				!jQuery.contains( elem.ownerDocument, elem );
		};
	
	
	
	function adjustCSS( elem, prop, valueParts, tween ) {
		var adjusted,
			scale = 1,
			maxIterations = 20,
			currentValue = tween ?
				function() { return tween.cur(); } :
				function() { return jQuery.css( elem, prop, "" ); },
			initial = currentValue(),
			unit = valueParts && valueParts[ 3 ] || ( jQuery.cssNumber[ prop ] ? "" : "px" ),
	
			// Starting value computation is required for potential unit mismatches
			initialInUnit = ( jQuery.cssNumber[ prop ] || unit !== "px" && +initial ) &&
				rcssNum.exec( jQuery.css( elem, prop ) );
	
		if ( initialInUnit && initialInUnit[ 3 ] !== unit ) {
	
			// Trust units reported by jQuery.css
			unit = unit || initialInUnit[ 3 ];
	
			// Make sure we update the tween properties later on
			valueParts = valueParts || [];
	
			// Iteratively approximate from a nonzero starting point
			initialInUnit = +initial || 1;
	
			do {
	
				// If previous iteration zeroed out, double until we get *something*.
				// Use string for doubling so we don't accidentally see scale as unchanged below
				scale = scale || ".5";
	
				// Adjust and apply
				initialInUnit = initialInUnit / scale;
				jQuery.style( elem, prop, initialInUnit + unit );
	
			// Update scale, tolerating zero or NaN from tween.cur()
			// Break the loop if scale is unchanged or perfect, or if we've just had enough.
			} while (
				scale !== ( scale = currentValue() / initial ) && scale !== 1 && --maxIterations
			);
		}
	
		if ( valueParts ) {
			initialInUnit = +initialInUnit || +initial || 0;
	
			// Apply relative offset (+=/-=) if specified
			adjusted = valueParts[ 1 ] ?
				initialInUnit + ( valueParts[ 1 ] + 1 ) * valueParts[ 2 ] :
				+valueParts[ 2 ];
			if ( tween ) {
				tween.unit = unit;
				tween.start = initialInUnit;
				tween.end = adjusted;
			}
		}
		return adjusted;
	}
	var rcheckableType = ( /^(?:checkbox|radio)$/i );
	
	var rtagName = ( /<([\w:-]+)/ );
	
	var rscriptType = ( /^$|\/(?:java|ecma)script/i );
	
	
	
	// We have to close these tags to support XHTML (#13200)
	var wrapMap = {
	
		// Support: IE9
		option: [ 1, "<select multiple='multiple'>", "</select>" ],
	
		// XHTML parsers do not magically insert elements in the
		// same way that tag soup parsers do. So we cannot shorten
		// this by omitting <tbody> or other required elements.
		thead: [ 1, "<table>", "</table>" ],
		col: [ 2, "<table><colgroup>", "</colgroup></table>" ],
		tr: [ 2, "<table><tbody>", "</tbody></table>" ],
		td: [ 3, "<table><tbody><tr>", "</tr></tbody></table>" ],
	
		_default: [ 0, "", "" ]
	};
	
	// Support: IE9
	wrapMap.optgroup = wrapMap.option;
	
	wrapMap.tbody = wrapMap.tfoot = wrapMap.colgroup = wrapMap.caption = wrapMap.thead;
	wrapMap.th = wrapMap.td;
	
	
	function getAll( context, tag ) {
	
		// Support: IE9-11+
		// Use typeof to avoid zero-argument method invocation on host objects (#15151)
		var ret = typeof context.getElementsByTagName !== "undefined" ?
				context.getElementsByTagName( tag || "*" ) :
				typeof context.querySelectorAll !== "undefined" ?
					context.querySelectorAll( tag || "*" ) :
				[];
	
		return tag === undefined || tag && jQuery.nodeName( context, tag ) ?
			jQuery.merge( [ context ], ret ) :
			ret;
	}
	
	
	// Mark scripts as having already been evaluated
	function setGlobalEval( elems, refElements ) {
		var i = 0,
			l = elems.length;
	
		for ( ; i < l; i++ ) {
			dataPriv.set(
				elems[ i ],
				"globalEval",
				!refElements || dataPriv.get( refElements[ i ], "globalEval" )
			);
		}
	}
	
	
	var rhtml = /<|&#?\w+;/;
	
	function buildFragment( elems, context, scripts, selection, ignored ) {
		var elem, tmp, tag, wrap, contains, j,
			fragment = context.createDocumentFragment(),
			nodes = [],
			i = 0,
			l = elems.length;
	
		for ( ; i < l; i++ ) {
			elem = elems[ i ];
	
			if ( elem || elem === 0 ) {
	
				// Add nodes directly
				if ( jQuery.type( elem ) === "object" ) {
	
					// Support: Android<4.1, PhantomJS<2
					// push.apply(_, arraylike) throws on ancient WebKit
					jQuery.merge( nodes, elem.nodeType ? [ elem ] : elem );
	
				// Convert non-html into a text node
				} else if ( !rhtml.test( elem ) ) {
					nodes.push( context.createTextNode( elem ) );
	
				// Convert html into DOM nodes
				} else {
					tmp = tmp || fragment.appendChild( context.createElement( "div" ) );
	
					// Deserialize a standard representation
					tag = ( rtagName.exec( elem ) || [ "", "" ] )[ 1 ].toLowerCase();
					wrap = wrapMap[ tag ] || wrapMap._default;
					tmp.innerHTML = wrap[ 1 ] + jQuery.htmlPrefilter( elem ) + wrap[ 2 ];
	
					// Descend through wrappers to the right content
					j = wrap[ 0 ];
					while ( j-- ) {
						tmp = tmp.lastChild;
					}
	
					// Support: Android<4.1, PhantomJS<2
					// push.apply(_, arraylike) throws on ancient WebKit
					jQuery.merge( nodes, tmp.childNodes );
	
					// Remember the top-level container
					tmp = fragment.firstChild;
	
					// Ensure the created nodes are orphaned (#12392)
					tmp.textContent = "";
				}
			}
		}
	
		// Remove wrapper from fragment
		fragment.textContent = "";
	
		i = 0;
		while ( ( elem = nodes[ i++ ] ) ) {
	
			// Skip elements already in the context collection (trac-4087)
			if ( selection && jQuery.inArray( elem, selection ) > -1 ) {
				if ( ignored ) {
					ignored.push( elem );
				}
				continue;
			}
	
			contains = jQuery.contains( elem.ownerDocument, elem );
	
			// Append to fragment
			tmp = getAll( fragment.appendChild( elem ), "script" );
	
			// Preserve script evaluation history
			if ( contains ) {
				setGlobalEval( tmp );
			}
	
			// Capture executables
			if ( scripts ) {
				j = 0;
				while ( ( elem = tmp[ j++ ] ) ) {
					if ( rscriptType.test( elem.type || "" ) ) {
						scripts.push( elem );
					}
				}
			}
		}
	
		return fragment;
	}
	
	
	( function() {
		var fragment = document.createDocumentFragment(),
			div = fragment.appendChild( document.createElement( "div" ) ),
			input = document.createElement( "input" );
	
		// Support: Android 4.0-4.3, Safari<=5.1
		// Check state lost if the name is set (#11217)
		// Support: Windows Web Apps (WWA)
		// `name` and `type` must use .setAttribute for WWA (#14901)
		input.setAttribute( "type", "radio" );
		input.setAttribute( "checked", "checked" );
		input.setAttribute( "name", "t" );
	
		div.appendChild( input );
	
		// Support: Safari<=5.1, Android<4.2
		// Older WebKit doesn't clone checked state correctly in fragments
		support.checkClone = div.cloneNode( true ).cloneNode( true ).lastChild.checked;
	
		// Support: IE<=11+
		// Make sure textarea (and checkbox) defaultValue is properly cloned
		div.innerHTML = "<textarea>x</textarea>";
		support.noCloneChecked = !!div.cloneNode( true ).lastChild.defaultValue;
	} )();
	
	
	var
		rkeyEvent = /^key/,
		rmouseEvent = /^(?:mouse|pointer|contextmenu|drag|drop)|click/,
		rtypenamespace = /^([^.]*)(?:\.(.+)|)/;
	
	function returnTrue() {
		return true;
	}
	
	function returnFalse() {
		return false;
	}
	
	// Support: IE9
	// See #13393 for more info
	function safeActiveElement() {
		try {
			return document.activeElement;
		} catch ( err ) { }
	}
	
	function on( elem, types, selector, data, fn, one ) {
		var origFn, type;
	
		// Types can be a map of types/handlers
		if ( typeof types === "object" ) {
	
			// ( types-Object, selector, data )
			if ( typeof selector !== "string" ) {
	
				// ( types-Object, data )
				data = data || selector;
				selector = undefined;
			}
			for ( type in types ) {
				on( elem, type, selector, data, types[ type ], one );
			}
			return elem;
		}
	
		if ( data == null && fn == null ) {
	
			// ( types, fn )
			fn = selector;
			data = selector = undefined;
		} else if ( fn == null ) {
			if ( typeof selector === "string" ) {
	
				// ( types, selector, fn )
				fn = data;
				data = undefined;
			} else {
	
				// ( types, data, fn )
				fn = data;
				data = selector;
				selector = undefined;
			}
		}
		if ( fn === false ) {
			fn = returnFalse;
		} else if ( !fn ) {
			return elem;
		}
	
		if ( one === 1 ) {
			origFn = fn;
			fn = function( event ) {
	
				// Can use an empty set, since event contains the info
				jQuery().off( event );
				return origFn.apply( this, arguments );
			};
	
			// Use same guid so caller can remove using origFn
			fn.guid = origFn.guid || ( origFn.guid = jQuery.guid++ );
		}
		return elem.each( function() {
			jQuery.event.add( this, types, fn, data, selector );
		} );
	}
	
	/*
	 * Helper functions for managing events -- not part of the public interface.
	 * Props to Dean Edwards' addEvent library for many of the ideas.
	 */
	jQuery.event = {
	
		global: {},
	
		add: function( elem, types, handler, data, selector ) {
	
			var handleObjIn, eventHandle, tmp,
				events, t, handleObj,
				special, handlers, type, namespaces, origType,
				elemData = dataPriv.get( elem );
	
			// Don't attach events to noData or text/comment nodes (but allow plain objects)
			if ( !elemData ) {
				return;
			}
	
			// Caller can pass in an object of custom data in lieu of the handler
			if ( handler.handler ) {
				handleObjIn = handler;
				handler = handleObjIn.handler;
				selector = handleObjIn.selector;
			}
	
			// Make sure that the handler has a unique ID, used to find/remove it later
			if ( !handler.guid ) {
				handler.guid = jQuery.guid++;
			}
	
			// Init the element's event structure and main handler, if this is the first
			if ( !( events = elemData.events ) ) {
				events = elemData.events = {};
			}
			if ( !( eventHandle = elemData.handle ) ) {
				eventHandle = elemData.handle = function( e ) {
	
					// Discard the second event of a jQuery.event.trigger() and
					// when an event is called after a page has unloaded
					return typeof jQuery !== "undefined" && jQuery.event.triggered !== e.type ?
						jQuery.event.dispatch.apply( elem, arguments ) : undefined;
				};
			}
	
			// Handle multiple events separated by a space
			types = ( types || "" ).match( rnotwhite ) || [ "" ];
			t = types.length;
			while ( t-- ) {
				tmp = rtypenamespace.exec( types[ t ] ) || [];
				type = origType = tmp[ 1 ];
				namespaces = ( tmp[ 2 ] || "" ).split( "." ).sort();
	
				// There *must* be a type, no attaching namespace-only handlers
				if ( !type ) {
					continue;
				}
	
				// If event changes its type, use the special event handlers for the changed type
				special = jQuery.event.special[ type ] || {};
	
				// If selector defined, determine special event api type, otherwise given type
				type = ( selector ? special.delegateType : special.bindType ) || type;
	
				// Update special based on newly reset type
				special = jQuery.event.special[ type ] || {};
	
				// handleObj is passed to all event handlers
				handleObj = jQuery.extend( {
					type: type,
					origType: origType,
					data: data,
					handler: handler,
					guid: handler.guid,
					selector: selector,
					needsContext: selector && jQuery.expr.match.needsContext.test( selector ),
					namespace: namespaces.join( "." )
				}, handleObjIn );
	
				// Init the event handler queue if we're the first
				if ( !( handlers = events[ type ] ) ) {
					handlers = events[ type ] = [];
					handlers.delegateCount = 0;
	
					// Only use addEventListener if the special events handler returns false
					if ( !special.setup ||
						special.setup.call( elem, data, namespaces, eventHandle ) === false ) {
	
						if ( elem.addEventListener ) {
							elem.addEventListener( type, eventHandle );
						}
					}
				}
	
				if ( special.add ) {
					special.add.call( elem, handleObj );
	
					if ( !handleObj.handler.guid ) {
						handleObj.handler.guid = handler.guid;
					}
				}
	
				// Add to the element's handler list, delegates in front
				if ( selector ) {
					handlers.splice( handlers.delegateCount++, 0, handleObj );
				} else {
					handlers.push( handleObj );
				}
	
				// Keep track of which events have ever been used, for event optimization
				jQuery.event.global[ type ] = true;
			}
	
		},
	
		// Detach an event or set of events from an element
		remove: function( elem, types, handler, selector, mappedTypes ) {
	
			var j, origCount, tmp,
				events, t, handleObj,
				special, handlers, type, namespaces, origType,
				elemData = dataPriv.hasData( elem ) && dataPriv.get( elem );
	
			if ( !elemData || !( events = elemData.events ) ) {
				return;
			}
	
			// Once for each type.namespace in types; type may be omitted
			types = ( types || "" ).match( rnotwhite ) || [ "" ];
			t = types.length;
			while ( t-- ) {
				tmp = rtypenamespace.exec( types[ t ] ) || [];
				type = origType = tmp[ 1 ];
				namespaces = ( tmp[ 2 ] || "" ).split( "." ).sort();
	
				// Unbind all events (on this namespace, if provided) for the element
				if ( !type ) {
					for ( type in events ) {
						jQuery.event.remove( elem, type + types[ t ], handler, selector, true );
					}
					continue;
				}
	
				special = jQuery.event.special[ type ] || {};
				type = ( selector ? special.delegateType : special.bindType ) || type;
				handlers = events[ type ] || [];
				tmp = tmp[ 2 ] &&
					new RegExp( "(^|\\.)" + namespaces.join( "\\.(?:.*\\.|)" ) + "(\\.|$)" );
	
				// Remove matching events
				origCount = j = handlers.length;
				while ( j-- ) {
					handleObj = handlers[ j ];
	
					if ( ( mappedTypes || origType === handleObj.origType ) &&
						( !handler || handler.guid === handleObj.guid ) &&
						( !tmp || tmp.test( handleObj.namespace ) ) &&
						( !selector || selector === handleObj.selector ||
							selector === "**" && handleObj.selector ) ) {
						handlers.splice( j, 1 );
	
						if ( handleObj.selector ) {
							handlers.delegateCount--;
						}
						if ( special.remove ) {
							special.remove.call( elem, handleObj );
						}
					}
				}
	
				// Remove generic event handler if we removed something and no more handlers exist
				// (avoids potential for endless recursion during removal of special event handlers)
				if ( origCount && !handlers.length ) {
					if ( !special.teardown ||
						special.teardown.call( elem, namespaces, elemData.handle ) === false ) {
	
						jQuery.removeEvent( elem, type, elemData.handle );
					}
	
					delete events[ type ];
				}
			}
	
			// Remove data and the expando if it's no longer used
			if ( jQuery.isEmptyObject( events ) ) {
				dataPriv.remove( elem, "handle events" );
			}
		},
	
		dispatch: function( event ) {
	
			// Make a writable jQuery.Event from the native event object
			event = jQuery.event.fix( event );
	
			var i, j, ret, matched, handleObj,
				handlerQueue = [],
				args = slice.call( arguments ),
				handlers = ( dataPriv.get( this, "events" ) || {} )[ event.type ] || [],
				special = jQuery.event.special[ event.type ] || {};
	
			// Use the fix-ed jQuery.Event rather than the (read-only) native event
			args[ 0 ] = event;
			event.delegateTarget = this;
	
			// Call the preDispatch hook for the mapped type, and let it bail if desired
			if ( special.preDispatch && special.preDispatch.call( this, event ) === false ) {
				return;
			}
	
			// Determine handlers
			handlerQueue = jQuery.event.handlers.call( this, event, handlers );
	
			// Run delegates first; they may want to stop propagation beneath us
			i = 0;
			while ( ( matched = handlerQueue[ i++ ] ) && !event.isPropagationStopped() ) {
				event.currentTarget = matched.elem;
	
				j = 0;
				while ( ( handleObj = matched.handlers[ j++ ] ) &&
					!event.isImmediatePropagationStopped() ) {
	
					// Triggered event must either 1) have no namespace, or 2) have namespace(s)
					// a subset or equal to those in the bound event (both can have no namespace).
					if ( !event.rnamespace || event.rnamespace.test( handleObj.namespace ) ) {
	
						event.handleObj = handleObj;
						event.data = handleObj.data;
	
						ret = ( ( jQuery.event.special[ handleObj.origType ] || {} ).handle ||
							handleObj.handler ).apply( matched.elem, args );
	
						if ( ret !== undefined ) {
							if ( ( event.result = ret ) === false ) {
								event.preventDefault();
								event.stopPropagation();
							}
						}
					}
				}
			}
	
			// Call the postDispatch hook for the mapped type
			if ( special.postDispatch ) {
				special.postDispatch.call( this, event );
			}
	
			return event.result;
		},
	
		handlers: function( event, handlers ) {
			var i, matches, sel, handleObj,
				handlerQueue = [],
				delegateCount = handlers.delegateCount,
				cur = event.target;
	
			// Support (at least): Chrome, IE9
			// Find delegate handlers
			// Black-hole SVG <use> instance trees (#13180)
			//
			// Support: Firefox<=42+
			// Avoid non-left-click in FF but don't block IE radio events (#3861, gh-2343)
			if ( delegateCount && cur.nodeType &&
				( event.type !== "click" || isNaN( event.button ) || event.button < 1 ) ) {
	
				for ( ; cur !== this; cur = cur.parentNode || this ) {
	
					// Don't check non-elements (#13208)
					// Don't process clicks on disabled elements (#6911, #8165, #11382, #11764)
					if ( cur.nodeType === 1 && ( cur.disabled !== true || event.type !== "click" ) ) {
						matches = [];
						for ( i = 0; i < delegateCount; i++ ) {
							handleObj = handlers[ i ];
	
							// Don't conflict with Object.prototype properties (#13203)
							sel = handleObj.selector + " ";
	
							if ( matches[ sel ] === undefined ) {
								matches[ sel ] = handleObj.needsContext ?
									jQuery( sel, this ).index( cur ) > -1 :
									jQuery.find( sel, this, null, [ cur ] ).length;
							}
							if ( matches[ sel ] ) {
								matches.push( handleObj );
							}
						}
						if ( matches.length ) {
							handlerQueue.push( { elem: cur, handlers: matches } );
						}
					}
				}
			}
	
			// Add the remaining (directly-bound) handlers
			if ( delegateCount < handlers.length ) {
				handlerQueue.push( { elem: this, handlers: handlers.slice( delegateCount ) } );
			}
	
			return handlerQueue;
		},
	
		// Includes some event props shared by KeyEvent and MouseEvent
		props: ( "altKey bubbles cancelable ctrlKey currentTarget detail eventPhase " +
			"metaKey relatedTarget shiftKey target timeStamp view which" ).split( " " ),
	
		fixHooks: {},
	
		keyHooks: {
			props: "char charCode key keyCode".split( " " ),
			filter: function( event, original ) {
	
				// Add which for key events
				if ( event.which == null ) {
					event.which = original.charCode != null ? original.charCode : original.keyCode;
				}
	
				return event;
			}
		},
	
		mouseHooks: {
			props: ( "button buttons clientX clientY offsetX offsetY pageX pageY " +
				"screenX screenY toElement" ).split( " " ),
			filter: function( event, original ) {
				var eventDoc, doc, body,
					button = original.button;
	
				// Calculate pageX/Y if missing and clientX/Y available
				if ( event.pageX == null && original.clientX != null ) {
					eventDoc = event.target.ownerDocument || document;
					doc = eventDoc.documentElement;
					body = eventDoc.body;
	
					event.pageX = original.clientX +
						( doc && doc.scrollLeft || body && body.scrollLeft || 0 ) -
						( doc && doc.clientLeft || body && body.clientLeft || 0 );
					event.pageY = original.clientY +
						( doc && doc.scrollTop  || body && body.scrollTop  || 0 ) -
						( doc && doc.clientTop  || body && body.clientTop  || 0 );
				}
	
				// Add which for click: 1 === left; 2 === middle; 3 === right
				// Note: button is not normalized, so don't use it
				if ( !event.which && button !== undefined ) {
					event.which = ( button & 1 ? 1 : ( button & 2 ? 3 : ( button & 4 ? 2 : 0 ) ) );
				}
	
				return event;
			}
		},
	
		fix: function( event ) {
			if ( event[ jQuery.expando ] ) {
				return event;
			}
	
			// Create a writable copy of the event object and normalize some properties
			var i, prop, copy,
				type = event.type,
				originalEvent = event,
				fixHook = this.fixHooks[ type ];
	
			if ( !fixHook ) {
				this.fixHooks[ type ] = fixHook =
					rmouseEvent.test( type ) ? this.mouseHooks :
					rkeyEvent.test( type ) ? this.keyHooks :
					{};
			}
			copy = fixHook.props ? this.props.concat( fixHook.props ) : this.props;
	
			event = new jQuery.Event( originalEvent );
	
			i = copy.length;
			while ( i-- ) {
				prop = copy[ i ];
				event[ prop ] = originalEvent[ prop ];
			}
	
			// Support: Cordova 2.5 (WebKit) (#13255)
			// All events should have a target; Cordova deviceready doesn't
			if ( !event.target ) {
				event.target = document;
			}
	
			// Support: Safari 6.0+, Chrome<28
			// Target should not be a text node (#504, #13143)
			if ( event.target.nodeType === 3 ) {
				event.target = event.target.parentNode;
			}
	
			return fixHook.filter ? fixHook.filter( event, originalEvent ) : event;
		},
	
		special: {
			load: {
	
				// Prevent triggered image.load events from bubbling to window.load
				noBubble: true
			},
			focus: {
	
				// Fire native event if possible so blur/focus sequence is correct
				trigger: function() {
					if ( this !== safeActiveElement() && this.focus ) {
						this.focus();
						return false;
					}
				},
				delegateType: "focusin"
			},
			blur: {
				trigger: function() {
					if ( this === safeActiveElement() && this.blur ) {
						this.blur();
						return false;
					}
				},
				delegateType: "focusout"
			},
			click: {
	
				// For checkbox, fire native event so checked state will be right
				trigger: function() {
					if ( this.type === "checkbox" && this.click && jQuery.nodeName( this, "input" ) ) {
						this.click();
						return false;
					}
				},
	
				// For cross-browser consistency, don't fire native .click() on links
				_default: function( event ) {
					return jQuery.nodeName( event.target, "a" );
				}
			},
	
			beforeunload: {
				postDispatch: function( event ) {
	
					// Support: Firefox 20+
					// Firefox doesn't alert if the returnValue field is not set.
					if ( event.result !== undefined && event.originalEvent ) {
						event.originalEvent.returnValue = event.result;
					}
				}
			}
		}
	};
	
	jQuery.removeEvent = function( elem, type, handle ) {
	
		// This "if" is needed for plain objects
		if ( elem.removeEventListener ) {
			elem.removeEventListener( type, handle );
		}
	};
	
	jQuery.Event = function( src, props ) {
	
		// Allow instantiation without the 'new' keyword
		if ( !( this instanceof jQuery.Event ) ) {
			return new jQuery.Event( src, props );
		}
	
		// Event object
		if ( src && src.type ) {
			this.originalEvent = src;
			this.type = src.type;
	
			// Events bubbling up the document may have been marked as prevented
			// by a handler lower down the tree; reflect the correct value.
			this.isDefaultPrevented = src.defaultPrevented ||
					src.defaultPrevented === undefined &&
	
					// Support: Android<4.0
					src.returnValue === false ?
				returnTrue :
				returnFalse;
	
		// Event type
		} else {
			this.type = src;
		}
	
		// Put explicitly provided properties onto the event object
		if ( props ) {
			jQuery.extend( this, props );
		}
	
		// Create a timestamp if incoming event doesn't have one
		this.timeStamp = src && src.timeStamp || jQuery.now();
	
		// Mark it as fixed
		this[ jQuery.expando ] = true;
	};
	
	// jQuery.Event is based on DOM3 Events as specified by the ECMAScript Language Binding
	// http://www.w3.org/TR/2003/WD-DOM-Level-3-Events-20030331/ecma-script-binding.html
	jQuery.Event.prototype = {
		constructor: jQuery.Event,
		isDefaultPrevented: returnFalse,
		isPropagationStopped: returnFalse,
		isImmediatePropagationStopped: returnFalse,
	
		preventDefault: function() {
			var e = this.originalEvent;
	
			this.isDefaultPrevented = returnTrue;
	
			if ( e ) {
				e.preventDefault();
			}
		},
		stopPropagation: function() {
			var e = this.originalEvent;
	
			this.isPropagationStopped = returnTrue;
	
			if ( e ) {
				e.stopPropagation();
			}
		},
		stopImmediatePropagation: function() {
			var e = this.originalEvent;
	
			this.isImmediatePropagationStopped = returnTrue;
	
			if ( e ) {
				e.stopImmediatePropagation();
			}
	
			this.stopPropagation();
		}
	};
	
	// Create mouseenter/leave events using mouseover/out and event-time checks
	// so that event delegation works in jQuery.
	// Do the same for pointerenter/pointerleave and pointerover/pointerout
	//
	// Support: Safari 7 only
	// Safari sends mouseenter too often; see:
	// https://code.google.com/p/chromium/issues/detail?id=470258
	// for the description of the bug (it existed in older Chrome versions as well).
	jQuery.each( {
		mouseenter: "mouseover",
		mouseleave: "mouseout",
		pointerenter: "pointerover",
		pointerleave: "pointerout"
	}, function( orig, fix ) {
		jQuery.event.special[ orig ] = {
			delegateType: fix,
			bindType: fix,
	
			handle: function( event ) {
				var ret,
					target = this,
					related = event.relatedTarget,
					handleObj = event.handleObj;
	
				// For mouseenter/leave call the handler if related is outside the target.
				// NB: No relatedTarget if the mouse left/entered the browser window
				if ( !related || ( related !== target && !jQuery.contains( target, related ) ) ) {
					event.type = handleObj.origType;
					ret = handleObj.handler.apply( this, arguments );
					event.type = fix;
				}
				return ret;
			}
		};
	} );
	
	jQuery.fn.extend( {
		on: function( types, selector, data, fn ) {
			return on( this, types, selector, data, fn );
		},
		one: function( types, selector, data, fn ) {
			return on( this, types, selector, data, fn, 1 );
		},
		off: function( types, selector, fn ) {
			var handleObj, type;
			if ( types && types.preventDefault && types.handleObj ) {
	
				// ( event )  dispatched jQuery.Event
				handleObj = types.handleObj;
				jQuery( types.delegateTarget ).off(
					handleObj.namespace ?
						handleObj.origType + "." + handleObj.namespace :
						handleObj.origType,
					handleObj.selector,
					handleObj.handler
				);
				return this;
			}
			if ( typeof types === "object" ) {
	
				// ( types-object [, selector] )
				for ( type in types ) {
					this.off( type, selector, types[ type ] );
				}
				return this;
			}
			if ( selector === false || typeof selector === "function" ) {
	
				// ( types [, fn] )
				fn = selector;
				selector = undefined;
			}
			if ( fn === false ) {
				fn = returnFalse;
			}
			return this.each( function() {
				jQuery.event.remove( this, types, fn, selector );
			} );
		}
	} );
	
	
	var
		rxhtmlTag = /<(?!area|br|col|embed|hr|img|input|link|meta|param)(([\w:-]+)[^>]*)\/>/gi,
	
		// Support: IE 10-11, Edge 10240+
		// In IE/Edge using regex groups here causes severe slowdowns.
		// See https://connect.microsoft.com/IE/feedback/details/1736512/
		rnoInnerhtml = /<script|<style|<link/i,
	
		// checked="checked" or checked
		rchecked = /checked\s*(?:[^=]|=\s*.checked.)/i,
		rscriptTypeMasked = /^true\/(.*)/,
		rcleanScript = /^\s*<!(?:\[CDATA\[|--)|(?:\]\]|--)>\s*$/g;
	
	// Manipulating tables requires a tbody
	function manipulationTarget( elem, content ) {
		return jQuery.nodeName( elem, "table" ) &&
			jQuery.nodeName( content.nodeType !== 11 ? content : content.firstChild, "tr" ) ?
	
			elem.getElementsByTagName( "tbody" )[ 0 ] ||
				elem.appendChild( elem.ownerDocument.createElement( "tbody" ) ) :
			elem;
	}
	
	// Replace/restore the type attribute of script elements for safe DOM manipulation
	function disableScript( elem ) {
		elem.type = ( elem.getAttribute( "type" ) !== null ) + "/" + elem.type;
		return elem;
	}
	function restoreScript( elem ) {
		var match = rscriptTypeMasked.exec( elem.type );
	
		if ( match ) {
			elem.type = match[ 1 ];
		} else {
			elem.removeAttribute( "type" );
		}
	
		return elem;
	}
	
	function cloneCopyEvent( src, dest ) {
		var i, l, type, pdataOld, pdataCur, udataOld, udataCur, events;
	
		if ( dest.nodeType !== 1 ) {
			return;
		}
	
		// 1. Copy private data: events, handlers, etc.
		if ( dataPriv.hasData( src ) ) {
			pdataOld = dataPriv.access( src );
			pdataCur = dataPriv.set( dest, pdataOld );
			events = pdataOld.events;
	
			if ( events ) {
				delete pdataCur.handle;
				pdataCur.events = {};
	
				for ( type in events ) {
					for ( i = 0, l = events[ type ].length; i < l; i++ ) {
						jQuery.event.add( dest, type, events[ type ][ i ] );
					}
				}
			}
		}
	
		// 2. Copy user data
		if ( dataUser.hasData( src ) ) {
			udataOld = dataUser.access( src );
			udataCur = jQuery.extend( {}, udataOld );
	
			dataUser.set( dest, udataCur );
		}
	}
	
	// Fix IE bugs, see support tests
	function fixInput( src, dest ) {
		var nodeName = dest.nodeName.toLowerCase();
	
		// Fails to persist the checked state of a cloned checkbox or radio button.
		if ( nodeName === "input" && rcheckableType.test( src.type ) ) {
			dest.checked = src.checked;
	
		// Fails to return the selected option to the default selected state when cloning options
		} else if ( nodeName === "input" || nodeName === "textarea" ) {
			dest.defaultValue = src.defaultValue;
		}
	}
	
	function domManip( collection, args, callback, ignored ) {
	
		// Flatten any nested arrays
		args = concat.apply( [], args );
	
		var fragment, first, scripts, hasScripts, node, doc,
			i = 0,
			l = collection.length,
			iNoClone = l - 1,
			value = args[ 0 ],
			isFunction = jQuery.isFunction( value );
	
		// We can't cloneNode fragments that contain checked, in WebKit
		if ( isFunction ||
				( l > 1 && typeof value === "string" &&
					!support.checkClone && rchecked.test( value ) ) ) {
			return collection.each( function( index ) {
				var self = collection.eq( index );
				if ( isFunction ) {
					args[ 0 ] = value.call( this, index, self.html() );
				}
				domManip( self, args, callback, ignored );
			} );
		}
	
		if ( l ) {
			fragment = buildFragment( args, collection[ 0 ].ownerDocument, false, collection, ignored );
			first = fragment.firstChild;
	
			if ( fragment.childNodes.length === 1 ) {
				fragment = first;
			}
	
			// Require either new content or an interest in ignored elements to invoke the callback
			if ( first || ignored ) {
				scripts = jQuery.map( getAll( fragment, "script" ), disableScript );
				hasScripts = scripts.length;
	
				// Use the original fragment for the last item
				// instead of the first because it can end up
				// being emptied incorrectly in certain situations (#8070).
				for ( ; i < l; i++ ) {
					node = fragment;
	
					if ( i !== iNoClone ) {
						node = jQuery.clone( node, true, true );
	
						// Keep references to cloned scripts for later restoration
						if ( hasScripts ) {
	
							// Support: Android<4.1, PhantomJS<2
							// push.apply(_, arraylike) throws on ancient WebKit
							jQuery.merge( scripts, getAll( node, "script" ) );
						}
					}
	
					callback.call( collection[ i ], node, i );
				}
	
				if ( hasScripts ) {
					doc = scripts[ scripts.length - 1 ].ownerDocument;
	
					// Reenable scripts
					jQuery.map( scripts, restoreScript );
	
					// Evaluate executable scripts on first document insertion
					for ( i = 0; i < hasScripts; i++ ) {
						node = scripts[ i ];
						if ( rscriptType.test( node.type || "" ) &&
							!dataPriv.access( node, "globalEval" ) &&
							jQuery.contains( doc, node ) ) {
	
							if ( node.src ) {
	
								// Optional AJAX dependency, but won't run scripts if not present
								if ( jQuery._evalUrl ) {
									jQuery._evalUrl( node.src );
								}
							} else {
								jQuery.globalEval( node.textContent.replace( rcleanScript, "" ) );
							}
						}
					}
				}
			}
		}
	
		return collection;
	}
	
	function remove( elem, selector, keepData ) {
		var node,
			nodes = selector ? jQuery.filter( selector, elem ) : elem,
			i = 0;
	
		for ( ; ( node = nodes[ i ] ) != null; i++ ) {
			if ( !keepData && node.nodeType === 1 ) {
				jQuery.cleanData( getAll( node ) );
			}
	
			if ( node.parentNode ) {
				if ( keepData && jQuery.contains( node.ownerDocument, node ) ) {
					setGlobalEval( getAll( node, "script" ) );
				}
				node.parentNode.removeChild( node );
			}
		}
	
		return elem;
	}
	
	jQuery.extend( {
		htmlPrefilter: function( html ) {
			return html.replace( rxhtmlTag, "<$1></$2>" );
		},
	
		clone: function( elem, dataAndEvents, deepDataAndEvents ) {
			var i, l, srcElements, destElements,
				clone = elem.cloneNode( true ),
				inPage = jQuery.contains( elem.ownerDocument, elem );
	
			// Fix IE cloning issues
			if ( !support.noCloneChecked && ( elem.nodeType === 1 || elem.nodeType === 11 ) &&
					!jQuery.isXMLDoc( elem ) ) {
	
				// We eschew Sizzle here for performance reasons: http://jsperf.com/getall-vs-sizzle/2
				destElements = getAll( clone );
				srcElements = getAll( elem );
	
				for ( i = 0, l = srcElements.length; i < l; i++ ) {
					fixInput( srcElements[ i ], destElements[ i ] );
				}
			}
	
			// Copy the events from the original to the clone
			if ( dataAndEvents ) {
				if ( deepDataAndEvents ) {
					srcElements = srcElements || getAll( elem );
					destElements = destElements || getAll( clone );
	
					for ( i = 0, l = srcElements.length; i < l; i++ ) {
						cloneCopyEvent( srcElements[ i ], destElements[ i ] );
					}
				} else {
					cloneCopyEvent( elem, clone );
				}
			}
	
			// Preserve script evaluation history
			destElements = getAll( clone, "script" );
			if ( destElements.length > 0 ) {
				setGlobalEval( destElements, !inPage && getAll( elem, "script" ) );
			}
	
			// Return the cloned set
			return clone;
		},
	
		cleanData: function( elems ) {
			var data, elem, type,
				special = jQuery.event.special,
				i = 0;
	
			for ( ; ( elem = elems[ i ] ) !== undefined; i++ ) {
				if ( acceptData( elem ) ) {
					if ( ( data = elem[ dataPriv.expando ] ) ) {
						if ( data.events ) {
							for ( type in data.events ) {
								if ( special[ type ] ) {
									jQuery.event.remove( elem, type );
	
								// This is a shortcut to avoid jQuery.event.remove's overhead
								} else {
									jQuery.removeEvent( elem, type, data.handle );
								}
							}
						}
	
						// Support: Chrome <= 35-45+
						// Assign undefined instead of using delete, see Data#remove
						elem[ dataPriv.expando ] = undefined;
					}
					if ( elem[ dataUser.expando ] ) {
	
						// Support: Chrome <= 35-45+
						// Assign undefined instead of using delete, see Data#remove
						elem[ dataUser.expando ] = undefined;
					}
				}
			}
		}
	} );
	
	jQuery.fn.extend( {
	
		// Keep domManip exposed until 3.0 (gh-2225)
		domManip: domManip,
	
		detach: function( selector ) {
			return remove( this, selector, true );
		},
	
		remove: function( selector ) {
			return remove( this, selector );
		},
	
		text: function( value ) {
			return access( this, function( value ) {
				return value === undefined ?
					jQuery.text( this ) :
					this.empty().each( function() {
						if ( this.nodeType === 1 || this.nodeType === 11 || this.nodeType === 9 ) {
							this.textContent = value;
						}
					} );
			}, null, value, arguments.length );
		},
	
		append: function() {
			return domManip( this, arguments, function( elem ) {
				if ( this.nodeType === 1 || this.nodeType === 11 || this.nodeType === 9 ) {
					var target = manipulationTarget( this, elem );
					target.appendChild( elem );
				}
			} );
		},
	
		prepend: function() {
			return domManip( this, arguments, function( elem ) {
				if ( this.nodeType === 1 || this.nodeType === 11 || this.nodeType === 9 ) {
					var target = manipulationTarget( this, elem );
					target.insertBefore( elem, target.firstChild );
				}
			} );
		},
	
		before: function() {
			return domManip( this, arguments, function( elem ) {
				if ( this.parentNode ) {
					this.parentNode.insertBefore( elem, this );
				}
			} );
		},
	
		after: function() {
			return domManip( this, arguments, function( elem ) {
				if ( this.parentNode ) {
					this.parentNode.insertBefore( elem, this.nextSibling );
				}
			} );
		},
	
		empty: function() {
			var elem,
				i = 0;
	
			for ( ; ( elem = this[ i ] ) != null; i++ ) {
				if ( elem.nodeType === 1 ) {
	
					// Prevent memory leaks
					jQuery.cleanData( getAll( elem, false ) );
	
					// Remove any remaining nodes
					elem.textContent = "";
				}
			}
	
			return this;
		},
	
		clone: function( dataAndEvents, deepDataAndEvents ) {
			dataAndEvents = dataAndEvents == null ? false : dataAndEvents;
			deepDataAndEvents = deepDataAndEvents == null ? dataAndEvents : deepDataAndEvents;
	
			return this.map( function() {
				return jQuery.clone( this, dataAndEvents, deepDataAndEvents );
			} );
		},
	
		html: function( value ) {
			return access( this, function( value ) {
				var elem = this[ 0 ] || {},
					i = 0,
					l = this.length;
	
				if ( value === undefined && elem.nodeType === 1 ) {
					return elem.innerHTML;
				}
	
				// See if we can take a shortcut and just use innerHTML
				if ( typeof value === "string" && !rnoInnerhtml.test( value ) &&
					!wrapMap[ ( rtagName.exec( value ) || [ "", "" ] )[ 1 ].toLowerCase() ] ) {
	
					value = jQuery.htmlPrefilter( value );
	
					try {
						for ( ; i < l; i++ ) {
							elem = this[ i ] || {};
	
							// Remove element nodes and prevent memory leaks
							if ( elem.nodeType === 1 ) {
								jQuery.cleanData( getAll( elem, false ) );
								elem.innerHTML = value;
							}
						}
	
						elem = 0;
	
					// If using innerHTML throws an exception, use the fallback method
					} catch ( e ) {}
				}
	
				if ( elem ) {
					this.empty().append( value );
				}
			}, null, value, arguments.length );
		},
	
		replaceWith: function() {
			var ignored = [];
	
			// Make the changes, replacing each non-ignored context element with the new content
			return domManip( this, arguments, function( elem ) {
				var parent = this.parentNode;
	
				if ( jQuery.inArray( this, ignored ) < 0 ) {
					jQuery.cleanData( getAll( this ) );
					if ( parent ) {
						parent.replaceChild( elem, this );
					}
				}
	
			// Force callback invocation
			}, ignored );
		}
	} );
	
	jQuery.each( {
		appendTo: "append",
		prependTo: "prepend",
		insertBefore: "before",
		insertAfter: "after",
		replaceAll: "replaceWith"
	}, function( name, original ) {
		jQuery.fn[ name ] = function( selector ) {
			var elems,
				ret = [],
				insert = jQuery( selector ),
				last = insert.length - 1,
				i = 0;
	
			for ( ; i <= last; i++ ) {
				elems = i === last ? this : this.clone( true );
				jQuery( insert[ i ] )[ original ]( elems );
	
				// Support: QtWebKit
				// .get() because push.apply(_, arraylike) throws
				push.apply( ret, elems.get() );
			}
	
			return this.pushStack( ret );
		};
	} );
	
	
	var iframe,
		elemdisplay = {
	
			// Support: Firefox
			// We have to pre-define these values for FF (#10227)
			HTML: "block",
			BODY: "block"
		};
	
	/**
	 * Retrieve the actual display of a element
	 * @param {String} name nodeName of the element
	 * @param {Object} doc Document object
	 */
	
	// Called only from within defaultDisplay
	function actualDisplay( name, doc ) {
		var elem = jQuery( doc.createElement( name ) ).appendTo( doc.body ),
	
			display = jQuery.css( elem[ 0 ], "display" );
	
		// We don't have any data stored on the element,
		// so use "detach" method as fast way to get rid of the element
		elem.detach();
	
		return display;
	}
	
	/**
	 * Try to determine the default display value of an element
	 * @param {String} nodeName
	 */
	function defaultDisplay( nodeName ) {
		var doc = document,
			display = elemdisplay[ nodeName ];
	
		if ( !display ) {
			display = actualDisplay( nodeName, doc );
	
			// If the simple way fails, read from inside an iframe
			if ( display === "none" || !display ) {
	
				// Use the already-created iframe if possible
				iframe = ( iframe || jQuery( "<iframe frameborder='0' width='0' height='0'/>" ) )
					.appendTo( doc.documentElement );
	
				// Always write a new HTML skeleton so Webkit and Firefox don't choke on reuse
				doc = iframe[ 0 ].contentDocument;
	
				// Support: IE
				doc.write();
				doc.close();
	
				display = actualDisplay( nodeName, doc );
				iframe.detach();
			}
	
			// Store the correct default display
			elemdisplay[ nodeName ] = display;
		}
	
		return display;
	}
	var rmargin = ( /^margin/ );
	
	var rnumnonpx = new RegExp( "^(" + pnum + ")(?!px)[a-z%]+$", "i" );
	
	var getStyles = function( elem ) {
	
			// Support: IE<=11+, Firefox<=30+ (#15098, #14150)
			// IE throws on elements created in popups
			// FF meanwhile throws on frame elements through "defaultView.getComputedStyle"
			var view = elem.ownerDocument.defaultView;
	
			if ( !view || !view.opener ) {
				view = window;
			}
	
			return view.getComputedStyle( elem );
		};
	
	var swap = function( elem, options, callback, args ) {
		var ret, name,
			old = {};
	
		// Remember the old values, and insert the new ones
		for ( name in options ) {
			old[ name ] = elem.style[ name ];
			elem.style[ name ] = options[ name ];
		}
	
		ret = callback.apply( elem, args || [] );
	
		// Revert the old values
		for ( name in options ) {
			elem.style[ name ] = old[ name ];
		}
	
		return ret;
	};
	
	
	var documentElement = document.documentElement;
	
	
	
	( function() {
		var pixelPositionVal, boxSizingReliableVal, pixelMarginRightVal, reliableMarginLeftVal,
			container = document.createElement( "div" ),
			div = document.createElement( "div" );
	
		// Finish early in limited (non-browser) environments
		if ( !div.style ) {
			return;
		}
	
		// Support: IE9-11+
		// Style of cloned element affects source element cloned (#8908)
		div.style.backgroundClip = "content-box";
		div.cloneNode( true ).style.backgroundClip = "";
		support.clearCloneStyle = div.style.backgroundClip === "content-box";
	
		container.style.cssText = "border:0;width:8px;height:0;top:0;left:-9999px;" +
			"padding:0;margin-top:1px;position:absolute";
		container.appendChild( div );
	
		// Executing both pixelPosition & boxSizingReliable tests require only one layout
		// so they're executed at the same time to save the second computation.
		function computeStyleTests() {
			div.style.cssText =
	
				// Support: Firefox<29, Android 2.3
				// Vendor-prefix box-sizing
				"-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box;" +
				"position:relative;display:block;" +
				"margin:auto;border:1px;padding:1px;" +
				"top:1%;width:50%";
			div.innerHTML = "";
			documentElement.appendChild( container );
	
			var divStyle = window.getComputedStyle( div );
			pixelPositionVal = divStyle.top !== "1%";
			reliableMarginLeftVal = divStyle.marginLeft === "2px";
			boxSizingReliableVal = divStyle.width === "4px";
	
			// Support: Android 4.0 - 4.3 only
			// Some styles come back with percentage values, even though they shouldn't
			div.style.marginRight = "50%";
			pixelMarginRightVal = divStyle.marginRight === "4px";
	
			documentElement.removeChild( container );
		}
	
		jQuery.extend( support, {
			pixelPosition: function() {
	
				// This test is executed only once but we still do memoizing
				// since we can use the boxSizingReliable pre-computing.
				// No need to check if the test was already performed, though.
				computeStyleTests();
				return pixelPositionVal;
			},
			boxSizingReliable: function() {
				if ( boxSizingReliableVal == null ) {
					computeStyleTests();
				}
				return boxSizingReliableVal;
			},
			pixelMarginRight: function() {
	
				// Support: Android 4.0-4.3
				// We're checking for boxSizingReliableVal here instead of pixelMarginRightVal
				// since that compresses better and they're computed together anyway.
				if ( boxSizingReliableVal == null ) {
					computeStyleTests();
				}
				return pixelMarginRightVal;
			},
			reliableMarginLeft: function() {
	
				// Support: IE <=8 only, Android 4.0 - 4.3 only, Firefox <=3 - 37
				if ( boxSizingReliableVal == null ) {
					computeStyleTests();
				}
				return reliableMarginLeftVal;
			},
			reliableMarginRight: function() {
	
				// Support: Android 2.3
				// Check if div with explicit width and no margin-right incorrectly
				// gets computed margin-right based on width of container. (#3333)
				// WebKit Bug 13343 - getComputedStyle returns wrong value for margin-right
				// This support function is only executed once so no memoizing is needed.
				var ret,
					marginDiv = div.appendChild( document.createElement( "div" ) );
	
				// Reset CSS: box-sizing; display; margin; border; padding
				marginDiv.style.cssText = div.style.cssText =
	
					// Support: Android 2.3
					// Vendor-prefix box-sizing
					"-webkit-box-sizing:content-box;box-sizing:content-box;" +
					"display:block;margin:0;border:0;padding:0";
				marginDiv.style.marginRight = marginDiv.style.width = "0";
				div.style.width = "1px";
				documentElement.appendChild( container );
	
				ret = !parseFloat( window.getComputedStyle( marginDiv ).marginRight );
	
				documentElement.removeChild( container );
				div.removeChild( marginDiv );
	
				return ret;
			}
		} );
	} )();
	
	
	function curCSS( elem, name, computed ) {
		var width, minWidth, maxWidth, ret,
			style = elem.style;
	
		computed = computed || getStyles( elem );
		ret = computed ? computed.getPropertyValue( name ) || computed[ name ] : undefined;
	
		// Support: Opera 12.1x only
		// Fall back to style even without computed
		// computed is undefined for elems on document fragments
		if ( ( ret === "" || ret === undefined ) && !jQuery.contains( elem.ownerDocument, elem ) ) {
			ret = jQuery.style( elem, name );
		}
	
		// Support: IE9
		// getPropertyValue is only needed for .css('filter') (#12537)
		if ( computed ) {
	
			// A tribute to the "awesome hack by Dean Edwards"
			// Android Browser returns percentage for some values,
			// but width seems to be reliably pixels.
			// This is against the CSSOM draft spec:
			// http://dev.w3.org/csswg/cssom/#resolved-values
			if ( !support.pixelMarginRight() && rnumnonpx.test( ret ) && rmargin.test( name ) ) {
	
				// Remember the original values
				width = style.width;
				minWidth = style.minWidth;
				maxWidth = style.maxWidth;
	
				// Put in the new values to get a computed value out
				style.minWidth = style.maxWidth = style.width = ret;
				ret = computed.width;
	
				// Revert the changed values
				style.width = width;
				style.minWidth = minWidth;
				style.maxWidth = maxWidth;
			}
		}
	
		return ret !== undefined ?
	
			// Support: IE9-11+
			// IE returns zIndex value as an integer.
			ret + "" :
			ret;
	}
	
	
	function addGetHookIf( conditionFn, hookFn ) {
	
		// Define the hook, we'll check on the first run if it's really needed.
		return {
			get: function() {
				if ( conditionFn() ) {
	
					// Hook not needed (or it's not possible to use it due
					// to missing dependency), remove it.
					delete this.get;
					return;
				}
	
				// Hook needed; redefine it so that the support test is not executed again.
				return ( this.get = hookFn ).apply( this, arguments );
			}
		};
	}
	
	
	var
	
		// Swappable if display is none or starts with table
		// except "table", "table-cell", or "table-caption"
		// See here for display values: https://developer.mozilla.org/en-US/docs/CSS/display
		rdisplayswap = /^(none|table(?!-c[ea]).+)/,
	
		cssShow = { position: "absolute", visibility: "hidden", display: "block" },
		cssNormalTransform = {
			letterSpacing: "0",
			fontWeight: "400"
		},
	
		cssPrefixes = [ "Webkit", "O", "Moz", "ms" ],
		emptyStyle = document.createElement( "div" ).style;
	
	// Return a css property mapped to a potentially vendor prefixed property
	function vendorPropName( name ) {
	
		// Shortcut for names that are not vendor prefixed
		if ( name in emptyStyle ) {
			return name;
		}
	
		// Check for vendor prefixed names
		var capName = name[ 0 ].toUpperCase() + name.slice( 1 ),
			i = cssPrefixes.length;
	
		while ( i-- ) {
			name = cssPrefixes[ i ] + capName;
			if ( name in emptyStyle ) {
				return name;
			}
		}
	}
	
	function setPositiveNumber( elem, value, subtract ) {
	
		// Any relative (+/-) values have already been
		// normalized at this point
		var matches = rcssNum.exec( value );
		return matches ?
	
			// Guard against undefined "subtract", e.g., when used as in cssHooks
			Math.max( 0, matches[ 2 ] - ( subtract || 0 ) ) + ( matches[ 3 ] || "px" ) :
			value;
	}
	
	function augmentWidthOrHeight( elem, name, extra, isBorderBox, styles ) {
		var i = extra === ( isBorderBox ? "border" : "content" ) ?
	
			// If we already have the right measurement, avoid augmentation
			4 :
	
			// Otherwise initialize for horizontal or vertical properties
			name === "width" ? 1 : 0,
	
			val = 0;
	
		for ( ; i < 4; i += 2 ) {
	
			// Both box models exclude margin, so add it if we want it
			if ( extra === "margin" ) {
				val += jQuery.css( elem, extra + cssExpand[ i ], true, styles );
			}
	
			if ( isBorderBox ) {
	
				// border-box includes padding, so remove it if we want content
				if ( extra === "content" ) {
					val -= jQuery.css( elem, "padding" + cssExpand[ i ], true, styles );
				}
	
				// At this point, extra isn't border nor margin, so remove border
				if ( extra !== "margin" ) {
					val -= jQuery.css( elem, "border" + cssExpand[ i ] + "Width", true, styles );
				}
			} else {
	
				// At this point, extra isn't content, so add padding
				val += jQuery.css( elem, "padding" + cssExpand[ i ], true, styles );
	
				// At this point, extra isn't content nor padding, so add border
				if ( extra !== "padding" ) {
					val += jQuery.css( elem, "border" + cssExpand[ i ] + "Width", true, styles );
				}
			}
		}
	
		return val;
	}
	
	function getWidthOrHeight( elem, name, extra ) {
	
		// Start with offset property, which is equivalent to the border-box value
		var valueIsBorderBox = true,
			val = name === "width" ? elem.offsetWidth : elem.offsetHeight,
			styles = getStyles( elem ),
			isBorderBox = jQuery.css( elem, "boxSizing", false, styles ) === "border-box";
	
		// Support: IE11 only
		// In IE 11 fullscreen elements inside of an iframe have
		// 100x too small dimensions (gh-1764).
		if ( document.msFullscreenElement && window.top !== window ) {
	
			// Support: IE11 only
			// Running getBoundingClientRect on a disconnected node
			// in IE throws an error.
			if ( elem.getClientRects().length ) {
				val = Math.round( elem.getBoundingClientRect()[ name ] * 100 );
			}
		}
	
		// Some non-html elements return undefined for offsetWidth, so check for null/undefined
		// svg - https://bugzilla.mozilla.org/show_bug.cgi?id=649285
		// MathML - https://bugzilla.mozilla.org/show_bug.cgi?id=491668
		if ( val <= 0 || val == null ) {
	
			// Fall back to computed then uncomputed css if necessary
			val = curCSS( elem, name, styles );
			if ( val < 0 || val == null ) {
				val = elem.style[ name ];
			}
	
			// Computed unit is not pixels. Stop here and return.
			if ( rnumnonpx.test( val ) ) {
				return val;
			}
	
			// Check for style in case a browser which returns unreliable values
			// for getComputedStyle silently falls back to the reliable elem.style
			valueIsBorderBox = isBorderBox &&
				( support.boxSizingReliable() || val === elem.style[ name ] );
	
			// Normalize "", auto, and prepare for extra
			val = parseFloat( val ) || 0;
		}
	
		// Use the active box-sizing model to add/subtract irrelevant styles
		return ( val +
			augmentWidthOrHeight(
				elem,
				name,
				extra || ( isBorderBox ? "border" : "content" ),
				valueIsBorderBox,
				styles
			)
		) + "px";
	}
	
	function showHide( elements, show ) {
		var display, elem, hidden,
			values = [],
			index = 0,
			length = elements.length;
	
		for ( ; index < length; index++ ) {
			elem = elements[ index ];
			if ( !elem.style ) {
				continue;
			}
	
			values[ index ] = dataPriv.get( elem, "olddisplay" );
			display = elem.style.display;
			if ( show ) {
	
				// Reset the inline display of this element to learn if it is
				// being hidden by cascaded rules or not
				if ( !values[ index ] && display === "none" ) {
					elem.style.display = "";
				}
	
				// Set elements which have been overridden with display: none
				// in a stylesheet to whatever the default browser style is
				// for such an element
				if ( elem.style.display === "" && isHidden( elem ) ) {
					values[ index ] = dataPriv.access(
						elem,
						"olddisplay",
						defaultDisplay( elem.nodeName )
					);
				}
			} else {
				hidden = isHidden( elem );
	
				if ( display !== "none" || !hidden ) {
					dataPriv.set(
						elem,
						"olddisplay",
						hidden ? display : jQuery.css( elem, "display" )
					);
				}
			}
		}
	
		// Set the display of most of the elements in a second loop
		// to avoid the constant reflow
		for ( index = 0; index < length; index++ ) {
			elem = elements[ index ];
			if ( !elem.style ) {
				continue;
			}
			if ( !show || elem.style.display === "none" || elem.style.display === "" ) {
				elem.style.display = show ? values[ index ] || "" : "none";
			}
		}
	
		return elements;
	}
	
	jQuery.extend( {
	
		// Add in style property hooks for overriding the default
		// behavior of getting and setting a style property
		cssHooks: {
			opacity: {
				get: function( elem, computed ) {
					if ( computed ) {
	
						// We should always get a number back from opacity
						var ret = curCSS( elem, "opacity" );
						return ret === "" ? "1" : ret;
					}
				}
			}
		},
	
		// Don't automatically add "px" to these possibly-unitless properties
		cssNumber: {
			"animationIterationCount": true,
			"columnCount": true,
			"fillOpacity": true,
			"flexGrow": true,
			"flexShrink": true,
			"fontWeight": true,
			"lineHeight": true,
			"opacity": true,
			"order": true,
			"orphans": true,
			"widows": true,
			"zIndex": true,
			"zoom": true
		},
	
		// Add in properties whose names you wish to fix before
		// setting or getting the value
		cssProps: {
			"float": "cssFloat"
		},
	
		// Get and set the style property on a DOM Node
		style: function( elem, name, value, extra ) {
	
			// Don't set styles on text and comment nodes
			if ( !elem || elem.nodeType === 3 || elem.nodeType === 8 || !elem.style ) {
				return;
			}
	
			// Make sure that we're working with the right name
			var ret, type, hooks,
				origName = jQuery.camelCase( name ),
				style = elem.style;
	
			name = jQuery.cssProps[ origName ] ||
				( jQuery.cssProps[ origName ] = vendorPropName( origName ) || origName );
	
			// Gets hook for the prefixed version, then unprefixed version
			hooks = jQuery.cssHooks[ name ] || jQuery.cssHooks[ origName ];
	
			// Check if we're setting a value
			if ( value !== undefined ) {
				type = typeof value;
	
				// Convert "+=" or "-=" to relative numbers (#7345)
				if ( type === "string" && ( ret = rcssNum.exec( value ) ) && ret[ 1 ] ) {
					value = adjustCSS( elem, name, ret );
	
					// Fixes bug #9237
					type = "number";
				}
	
				// Make sure that null and NaN values aren't set (#7116)
				if ( value == null || value !== value ) {
					return;
				}
	
				// If a number was passed in, add the unit (except for certain CSS properties)
				if ( type === "number" ) {
					value += ret && ret[ 3 ] || ( jQuery.cssNumber[ origName ] ? "" : "px" );
				}
	
				// Support: IE9-11+
				// background-* props affect original clone's values
				if ( !support.clearCloneStyle && value === "" && name.indexOf( "background" ) === 0 ) {
					style[ name ] = "inherit";
				}
	
				// If a hook was provided, use that value, otherwise just set the specified value
				if ( !hooks || !( "set" in hooks ) ||
					( value = hooks.set( elem, value, extra ) ) !== undefined ) {
	
					style[ name ] = value;
				}
	
			} else {
	
				// If a hook was provided get the non-computed value from there
				if ( hooks && "get" in hooks &&
					( ret = hooks.get( elem, false, extra ) ) !== undefined ) {
	
					return ret;
				}
	
				// Otherwise just get the value from the style object
				return style[ name ];
			}
		},
	
		css: function( elem, name, extra, styles ) {
			var val, num, hooks,
				origName = jQuery.camelCase( name );
	
			// Make sure that we're working with the right name
			name = jQuery.cssProps[ origName ] ||
				( jQuery.cssProps[ origName ] = vendorPropName( origName ) || origName );
	
			// Try prefixed name followed by the unprefixed name
			hooks = jQuery.cssHooks[ name ] || jQuery.cssHooks[ origName ];
	
			// If a hook was provided get the computed value from there
			if ( hooks && "get" in hooks ) {
				val = hooks.get( elem, true, extra );
			}
	
			// Otherwise, if a way to get the computed value exists, use that
			if ( val === undefined ) {
				val = curCSS( elem, name, styles );
			}
	
			// Convert "normal" to computed value
			if ( val === "normal" && name in cssNormalTransform ) {
				val = cssNormalTransform[ name ];
			}
	
			// Make numeric if forced or a qualifier was provided and val looks numeric
			if ( extra === "" || extra ) {
				num = parseFloat( val );
				return extra === true || isFinite( num ) ? num || 0 : val;
			}
			return val;
		}
	} );
	
	jQuery.each( [ "height", "width" ], function( i, name ) {
		jQuery.cssHooks[ name ] = {
			get: function( elem, computed, extra ) {
				if ( computed ) {
	
					// Certain elements can have dimension info if we invisibly show them
					// but it must have a current display style that would benefit
					return rdisplayswap.test( jQuery.css( elem, "display" ) ) &&
						elem.offsetWidth === 0 ?
							swap( elem, cssShow, function() {
								return getWidthOrHeight( elem, name, extra );
							} ) :
							getWidthOrHeight( elem, name, extra );
				}
			},
	
			set: function( elem, value, extra ) {
				var matches,
					styles = extra && getStyles( elem ),
					subtract = extra && augmentWidthOrHeight(
						elem,
						name,
						extra,
						jQuery.css( elem, "boxSizing", false, styles ) === "border-box",
						styles
					);
	
				// Convert to pixels if value adjustment is needed
				if ( subtract && ( matches = rcssNum.exec( value ) ) &&
					( matches[ 3 ] || "px" ) !== "px" ) {
	
					elem.style[ name ] = value;
					value = jQuery.css( elem, name );
				}
	
				return setPositiveNumber( elem, value, subtract );
			}
		};
	} );
	
	jQuery.cssHooks.marginLeft = addGetHookIf( support.reliableMarginLeft,
		function( elem, computed ) {
			if ( computed ) {
				return ( parseFloat( curCSS( elem, "marginLeft" ) ) ||
					elem.getBoundingClientRect().left -
						swap( elem, { marginLeft: 0 }, function() {
							return elem.getBoundingClientRect().left;
						} )
					) + "px";
			}
		}
	);
	
	// Support: Android 2.3
	jQuery.cssHooks.marginRight = addGetHookIf( support.reliableMarginRight,
		function( elem, computed ) {
			if ( computed ) {
				return swap( elem, { "display": "inline-block" },
					curCSS, [ elem, "marginRight" ] );
			}
		}
	);
	
	// These hooks are used by animate to expand properties
	jQuery.each( {
		margin: "",
		padding: "",
		border: "Width"
	}, function( prefix, suffix ) {
		jQuery.cssHooks[ prefix + suffix ] = {
			expand: function( value ) {
				var i = 0,
					expanded = {},
	
					// Assumes a single number if not a string
					parts = typeof value === "string" ? value.split( " " ) : [ value ];
	
				for ( ; i < 4; i++ ) {
					expanded[ prefix + cssExpand[ i ] + suffix ] =
						parts[ i ] || parts[ i - 2 ] || parts[ 0 ];
				}
	
				return expanded;
			}
		};
	
		if ( !rmargin.test( prefix ) ) {
			jQuery.cssHooks[ prefix + suffix ].set = setPositiveNumber;
		}
	} );
	
	jQuery.fn.extend( {
		css: function( name, value ) {
			return access( this, function( elem, name, value ) {
				var styles, len,
					map = {},
					i = 0;
	
				if ( jQuery.isArray( name ) ) {
					styles = getStyles( elem );
					len = name.length;
	
					for ( ; i < len; i++ ) {
						map[ name[ i ] ] = jQuery.css( elem, name[ i ], false, styles );
					}
	
					return map;
				}
	
				return value !== undefined ?
					jQuery.style( elem, name, value ) :
					jQuery.css( elem, name );
			}, name, value, arguments.length > 1 );
		},
		show: function() {
			return showHide( this, true );
		},
		hide: function() {
			return showHide( this );
		},
		toggle: function( state ) {
			if ( typeof state === "boolean" ) {
				return state ? this.show() : this.hide();
			}
	
			return this.each( function() {
				if ( isHidden( this ) ) {
					jQuery( this ).show();
				} else {
					jQuery( this ).hide();
				}
			} );
		}
	} );
	
	
	function Tween( elem, options, prop, end, easing ) {
		return new Tween.prototype.init( elem, options, prop, end, easing );
	}
	jQuery.Tween = Tween;
	
	Tween.prototype = {
		constructor: Tween,
		init: function( elem, options, prop, end, easing, unit ) {
			this.elem = elem;
			this.prop = prop;
			this.easing = easing || jQuery.easing._default;
			this.options = options;
			this.start = this.now = this.cur();
			this.end = end;
			this.unit = unit || ( jQuery.cssNumber[ prop ] ? "" : "px" );
		},
		cur: function() {
			var hooks = Tween.propHooks[ this.prop ];
	
			return hooks && hooks.get ?
				hooks.get( this ) :
				Tween.propHooks._default.get( this );
		},
		run: function( percent ) {
			var eased,
				hooks = Tween.propHooks[ this.prop ];
	
			if ( this.options.duration ) {
				this.pos = eased = jQuery.easing[ this.easing ](
					percent, this.options.duration * percent, 0, 1, this.options.duration
				);
			} else {
				this.pos = eased = percent;
			}
			this.now = ( this.end - this.start ) * eased + this.start;
	
			if ( this.options.step ) {
				this.options.step.call( this.elem, this.now, this );
			}
	
			if ( hooks && hooks.set ) {
				hooks.set( this );
			} else {
				Tween.propHooks._default.set( this );
			}
			return this;
		}
	};
	
	Tween.prototype.init.prototype = Tween.prototype;
	
	Tween.propHooks = {
		_default: {
			get: function( tween ) {
				var result;
	
				// Use a property on the element directly when it is not a DOM element,
				// or when there is no matching style property that exists.
				if ( tween.elem.nodeType !== 1 ||
					tween.elem[ tween.prop ] != null && tween.elem.style[ tween.prop ] == null ) {
					return tween.elem[ tween.prop ];
				}
	
				// Passing an empty string as a 3rd parameter to .css will automatically
				// attempt a parseFloat and fallback to a string if the parse fails.
				// Simple values such as "10px" are parsed to Float;
				// complex values such as "rotate(1rad)" are returned as-is.
				result = jQuery.css( tween.elem, tween.prop, "" );
	
				// Empty strings, null, undefined and "auto" are converted to 0.
				return !result || result === "auto" ? 0 : result;
			},
			set: function( tween ) {
	
				// Use step hook for back compat.
				// Use cssHook if its there.
				// Use .style if available and use plain properties where available.
				if ( jQuery.fx.step[ tween.prop ] ) {
					jQuery.fx.step[ tween.prop ]( tween );
				} else if ( tween.elem.nodeType === 1 &&
					( tween.elem.style[ jQuery.cssProps[ tween.prop ] ] != null ||
						jQuery.cssHooks[ tween.prop ] ) ) {
					jQuery.style( tween.elem, tween.prop, tween.now + tween.unit );
				} else {
					tween.elem[ tween.prop ] = tween.now;
				}
			}
		}
	};
	
	// Support: IE9
	// Panic based approach to setting things on disconnected nodes
	Tween.propHooks.scrollTop = Tween.propHooks.scrollLeft = {
		set: function( tween ) {
			if ( tween.elem.nodeType && tween.elem.parentNode ) {
				tween.elem[ tween.prop ] = tween.now;
			}
		}
	};
	
	jQuery.easing = {
		linear: function( p ) {
			return p;
		},
		swing: function( p ) {
			return 0.5 - Math.cos( p * Math.PI ) / 2;
		},
		_default: "swing"
	};
	
	jQuery.fx = Tween.prototype.init;
	
	// Back Compat <1.8 extension point
	jQuery.fx.step = {};
	
	
	
	
	var
		fxNow, timerId,
		rfxtypes = /^(?:toggle|show|hide)$/,
		rrun = /queueHooks$/;
	
	// Animations created synchronously will run synchronously
	function createFxNow() {
		window.setTimeout( function() {
			fxNow = undefined;
		} );
		return ( fxNow = jQuery.now() );
	}
	
	// Generate parameters to create a standard animation
	function genFx( type, includeWidth ) {
		var which,
			i = 0,
			attrs = { height: type };
	
		// If we include width, step value is 1 to do all cssExpand values,
		// otherwise step value is 2 to skip over Left and Right
		includeWidth = includeWidth ? 1 : 0;
		for ( ; i < 4 ; i += 2 - includeWidth ) {
			which = cssExpand[ i ];
			attrs[ "margin" + which ] = attrs[ "padding" + which ] = type;
		}
	
		if ( includeWidth ) {
			attrs.opacity = attrs.width = type;
		}
	
		return attrs;
	}
	
	function createTween( value, prop, animation ) {
		var tween,
			collection = ( Animation.tweeners[ prop ] || [] ).concat( Animation.tweeners[ "*" ] ),
			index = 0,
			length = collection.length;
		for ( ; index < length; index++ ) {
			if ( ( tween = collection[ index ].call( animation, prop, value ) ) ) {
	
				// We're done with this property
				return tween;
			}
		}
	}
	
	function defaultPrefilter( elem, props, opts ) {
		/* jshint validthis: true */
		var prop, value, toggle, tween, hooks, oldfire, display, checkDisplay,
			anim = this,
			orig = {},
			style = elem.style,
			hidden = elem.nodeType && isHidden( elem ),
			dataShow = dataPriv.get( elem, "fxshow" );
	
		// Handle queue: false promises
		if ( !opts.queue ) {
			hooks = jQuery._queueHooks( elem, "fx" );
			if ( hooks.unqueued == null ) {
				hooks.unqueued = 0;
				oldfire = hooks.empty.fire;
				hooks.empty.fire = function() {
					if ( !hooks.unqueued ) {
						oldfire();
					}
				};
			}
			hooks.unqueued++;
	
			anim.always( function() {
	
				// Ensure the complete handler is called before this completes
				anim.always( function() {
					hooks.unqueued--;
					if ( !jQuery.queue( elem, "fx" ).length ) {
						hooks.empty.fire();
					}
				} );
			} );
		}
	
		// Height/width overflow pass
		if ( elem.nodeType === 1 && ( "height" in props || "width" in props ) ) {
	
			// Make sure that nothing sneaks out
			// Record all 3 overflow attributes because IE9-10 do not
			// change the overflow attribute when overflowX and
			// overflowY are set to the same value
			opts.overflow = [ style.overflow, style.overflowX, style.overflowY ];
	
			// Set display property to inline-block for height/width
			// animations on inline elements that are having width/height animated
			display = jQuery.css( elem, "display" );
	
			// Test default display if display is currently "none"
			checkDisplay = display === "none" ?
				dataPriv.get( elem, "olddisplay" ) || defaultDisplay( elem.nodeName ) : display;
	
			if ( checkDisplay === "inline" && jQuery.css( elem, "float" ) === "none" ) {
				style.display = "inline-block";
			}
		}
	
		if ( opts.overflow ) {
			style.overflow = "hidden";
			anim.always( function() {
				style.overflow = opts.overflow[ 0 ];
				style.overflowX = opts.overflow[ 1 ];
				style.overflowY = opts.overflow[ 2 ];
			} );
		}
	
		// show/hide pass
		for ( prop in props ) {
			value = props[ prop ];
			if ( rfxtypes.exec( value ) ) {
				delete props[ prop ];
				toggle = toggle || value === "toggle";
				if ( value === ( hidden ? "hide" : "show" ) ) {
	
					// If there is dataShow left over from a stopped hide or show
					// and we are going to proceed with show, we should pretend to be hidden
					if ( value === "show" && dataShow && dataShow[ prop ] !== undefined ) {
						hidden = true;
					} else {
						continue;
					}
				}
				orig[ prop ] = dataShow && dataShow[ prop ] || jQuery.style( elem, prop );
	
			// Any non-fx value stops us from restoring the original display value
			} else {
				display = undefined;
			}
		}
	
		if ( !jQuery.isEmptyObject( orig ) ) {
			if ( dataShow ) {
				if ( "hidden" in dataShow ) {
					hidden = dataShow.hidden;
				}
			} else {
				dataShow = dataPriv.access( elem, "fxshow", {} );
			}
	
			// Store state if its toggle - enables .stop().toggle() to "reverse"
			if ( toggle ) {
				dataShow.hidden = !hidden;
			}
			if ( hidden ) {
				jQuery( elem ).show();
			} else {
				anim.done( function() {
					jQuery( elem ).hide();
				} );
			}
			anim.done( function() {
				var prop;
	
				dataPriv.remove( elem, "fxshow" );
				for ( prop in orig ) {
					jQuery.style( elem, prop, orig[ prop ] );
				}
			} );
			for ( prop in orig ) {
				tween = createTween( hidden ? dataShow[ prop ] : 0, prop, anim );
	
				if ( !( prop in dataShow ) ) {
					dataShow[ prop ] = tween.start;
					if ( hidden ) {
						tween.end = tween.start;
						tween.start = prop === "width" || prop === "height" ? 1 : 0;
					}
				}
			}
	
		// If this is a noop like .hide().hide(), restore an overwritten display value
		} else if ( ( display === "none" ? defaultDisplay( elem.nodeName ) : display ) === "inline" ) {
			style.display = display;
		}
	}
	
	function propFilter( props, specialEasing ) {
		var index, name, easing, value, hooks;
	
		// camelCase, specialEasing and expand cssHook pass
		for ( index in props ) {
			name = jQuery.camelCase( index );
			easing = specialEasing[ name ];
			value = props[ index ];
			if ( jQuery.isArray( value ) ) {
				easing = value[ 1 ];
				value = props[ index ] = value[ 0 ];
			}
	
			if ( index !== name ) {
				props[ name ] = value;
				delete props[ index ];
			}
	
			hooks = jQuery.cssHooks[ name ];
			if ( hooks && "expand" in hooks ) {
				value = hooks.expand( value );
				delete props[ name ];
	
				// Not quite $.extend, this won't overwrite existing keys.
				// Reusing 'index' because we have the correct "name"
				for ( index in value ) {
					if ( !( index in props ) ) {
						props[ index ] = value[ index ];
						specialEasing[ index ] = easing;
					}
				}
			} else {
				specialEasing[ name ] = easing;
			}
		}
	}
	
	function Animation( elem, properties, options ) {
		var result,
			stopped,
			index = 0,
			length = Animation.prefilters.length,
			deferred = jQuery.Deferred().always( function() {
	
				// Don't match elem in the :animated selector
				delete tick.elem;
			} ),
			tick = function() {
				if ( stopped ) {
					return false;
				}
				var currentTime = fxNow || createFxNow(),
					remaining = Math.max( 0, animation.startTime + animation.duration - currentTime ),
	
					// Support: Android 2.3
					// Archaic crash bug won't allow us to use `1 - ( 0.5 || 0 )` (#12497)
					temp = remaining / animation.duration || 0,
					percent = 1 - temp,
					index = 0,
					length = animation.tweens.length;
	
				for ( ; index < length ; index++ ) {
					animation.tweens[ index ].run( percent );
				}
	
				deferred.notifyWith( elem, [ animation, percent, remaining ] );
	
				if ( percent < 1 && length ) {
					return remaining;
				} else {
					deferred.resolveWith( elem, [ animation ] );
					return false;
				}
			},
			animation = deferred.promise( {
				elem: elem,
				props: jQuery.extend( {}, properties ),
				opts: jQuery.extend( true, {
					specialEasing: {},
					easing: jQuery.easing._default
				}, options ),
				originalProperties: properties,
				originalOptions: options,
				startTime: fxNow || createFxNow(),
				duration: options.duration,
				tweens: [],
				createTween: function( prop, end ) {
					var tween = jQuery.Tween( elem, animation.opts, prop, end,
							animation.opts.specialEasing[ prop ] || animation.opts.easing );
					animation.tweens.push( tween );
					return tween;
				},
				stop: function( gotoEnd ) {
					var index = 0,
	
						// If we are going to the end, we want to run all the tweens
						// otherwise we skip this part
						length = gotoEnd ? animation.tweens.length : 0;
					if ( stopped ) {
						return this;
					}
					stopped = true;
					for ( ; index < length ; index++ ) {
						animation.tweens[ index ].run( 1 );
					}
	
					// Resolve when we played the last frame; otherwise, reject
					if ( gotoEnd ) {
						deferred.notifyWith( elem, [ animation, 1, 0 ] );
						deferred.resolveWith( elem, [ animation, gotoEnd ] );
					} else {
						deferred.rejectWith( elem, [ animation, gotoEnd ] );
					}
					return this;
				}
			} ),
			props = animation.props;
	
		propFilter( props, animation.opts.specialEasing );
	
		for ( ; index < length ; index++ ) {
			result = Animation.prefilters[ index ].call( animation, elem, props, animation.opts );
			if ( result ) {
				if ( jQuery.isFunction( result.stop ) ) {
					jQuery._queueHooks( animation.elem, animation.opts.queue ).stop =
						jQuery.proxy( result.stop, result );
				}
				return result;
			}
		}
	
		jQuery.map( props, createTween, animation );
	
		if ( jQuery.isFunction( animation.opts.start ) ) {
			animation.opts.start.call( elem, animation );
		}
	
		jQuery.fx.timer(
			jQuery.extend( tick, {
				elem: elem,
				anim: animation,
				queue: animation.opts.queue
			} )
		);
	
		// attach callbacks from options
		return animation.progress( animation.opts.progress )
			.done( animation.opts.done, animation.opts.complete )
			.fail( animation.opts.fail )
			.always( animation.opts.always );
	}
	
	jQuery.Animation = jQuery.extend( Animation, {
		tweeners: {
			"*": [ function( prop, value ) {
				var tween = this.createTween( prop, value );
				adjustCSS( tween.elem, prop, rcssNum.exec( value ), tween );
				return tween;
			} ]
		},
	
		tweener: function( props, callback ) {
			if ( jQuery.isFunction( props ) ) {
				callback = props;
				props = [ "*" ];
			} else {
				props = props.match( rnotwhite );
			}
	
			var prop,
				index = 0,
				length = props.length;
	
			for ( ; index < length ; index++ ) {
				prop = props[ index ];
				Animation.tweeners[ prop ] = Animation.tweeners[ prop ] || [];
				Animation.tweeners[ prop ].unshift( callback );
			}
		},
	
		prefilters: [ defaultPrefilter ],
	
		prefilter: function( callback, prepend ) {
			if ( prepend ) {
				Animation.prefilters.unshift( callback );
			} else {
				Animation.prefilters.push( callback );
			}
		}
	} );
	
	jQuery.speed = function( speed, easing, fn ) {
		var opt = speed && typeof speed === "object" ? jQuery.extend( {}, speed ) : {
			complete: fn || !fn && easing ||
				jQuery.isFunction( speed ) && speed,
			duration: speed,
			easing: fn && easing || easing && !jQuery.isFunction( easing ) && easing
		};
	
		opt.duration = jQuery.fx.off ? 0 : typeof opt.duration === "number" ?
			opt.duration : opt.duration in jQuery.fx.speeds ?
				jQuery.fx.speeds[ opt.duration ] : jQuery.fx.speeds._default;
	
		// Normalize opt.queue - true/undefined/null -> "fx"
		if ( opt.queue == null || opt.queue === true ) {
			opt.queue = "fx";
		}
	
		// Queueing
		opt.old = opt.complete;
	
		opt.complete = function() {
			if ( jQuery.isFunction( opt.old ) ) {
				opt.old.call( this );
			}
	
			if ( opt.queue ) {
				jQuery.dequeue( this, opt.queue );
			}
		};
	
		return opt;
	};
	
	jQuery.fn.extend( {
		fadeTo: function( speed, to, easing, callback ) {
	
			// Show any hidden elements after setting opacity to 0
			return this.filter( isHidden ).css( "opacity", 0 ).show()
	
				// Animate to the value specified
				.end().animate( { opacity: to }, speed, easing, callback );
		},
		animate: function( prop, speed, easing, callback ) {
			var empty = jQuery.isEmptyObject( prop ),
				optall = jQuery.speed( speed, easing, callback ),
				doAnimation = function() {
	
					// Operate on a copy of prop so per-property easing won't be lost
					var anim = Animation( this, jQuery.extend( {}, prop ), optall );
	
					// Empty animations, or finishing resolves immediately
					if ( empty || dataPriv.get( this, "finish" ) ) {
						anim.stop( true );
					}
				};
				doAnimation.finish = doAnimation;
	
			return empty || optall.queue === false ?
				this.each( doAnimation ) :
				this.queue( optall.queue, doAnimation );
		},
		stop: function( type, clearQueue, gotoEnd ) {
			var stopQueue = function( hooks ) {
				var stop = hooks.stop;
				delete hooks.stop;
				stop( gotoEnd );
			};
	
			if ( typeof type !== "string" ) {
				gotoEnd = clearQueue;
				clearQueue = type;
				type = undefined;
			}
			if ( clearQueue && type !== false ) {
				this.queue( type || "fx", [] );
			}
	
			return this.each( function() {
				var dequeue = true,
					index = type != null && type + "queueHooks",
					timers = jQuery.timers,
					data = dataPriv.get( this );
	
				if ( index ) {
					if ( data[ index ] && data[ index ].stop ) {
						stopQueue( data[ index ] );
					}
				} else {
					for ( index in data ) {
						if ( data[ index ] && data[ index ].stop && rrun.test( index ) ) {
							stopQueue( data[ index ] );
						}
					}
				}
	
				for ( index = timers.length; index--; ) {
					if ( timers[ index ].elem === this &&
						( type == null || timers[ index ].queue === type ) ) {
	
						timers[ index ].anim.stop( gotoEnd );
						dequeue = false;
						timers.splice( index, 1 );
					}
				}
	
				// Start the next in the queue if the last step wasn't forced.
				// Timers currently will call their complete callbacks, which
				// will dequeue but only if they were gotoEnd.
				if ( dequeue || !gotoEnd ) {
					jQuery.dequeue( this, type );
				}
			} );
		},
		finish: function( type ) {
			if ( type !== false ) {
				type = type || "fx";
			}
			return this.each( function() {
				var index,
					data = dataPriv.get( this ),
					queue = data[ type + "queue" ],
					hooks = data[ type + "queueHooks" ],
					timers = jQuery.timers,
					length = queue ? queue.length : 0;
	
				// Enable finishing flag on private data
				data.finish = true;
	
				// Empty the queue first
				jQuery.queue( this, type, [] );
	
				if ( hooks && hooks.stop ) {
					hooks.stop.call( this, true );
				}
	
				// Look for any active animations, and finish them
				for ( index = timers.length; index--; ) {
					if ( timers[ index ].elem === this && timers[ index ].queue === type ) {
						timers[ index ].anim.stop( true );
						timers.splice( index, 1 );
					}
				}
	
				// Look for any animations in the old queue and finish them
				for ( index = 0; index < length; index++ ) {
					if ( queue[ index ] && queue[ index ].finish ) {
						queue[ index ].finish.call( this );
					}
				}
	
				// Turn off finishing flag
				delete data.finish;
			} );
		}
	} );
	
	jQuery.each( [ "toggle", "show", "hide" ], function( i, name ) {
		var cssFn = jQuery.fn[ name ];
		jQuery.fn[ name ] = function( speed, easing, callback ) {
			return speed == null || typeof speed === "boolean" ?
				cssFn.apply( this, arguments ) :
				this.animate( genFx( name, true ), speed, easing, callback );
		};
	} );
	
	// Generate shortcuts for custom animations
	jQuery.each( {
		slideDown: genFx( "show" ),
		slideUp: genFx( "hide" ),
		slideToggle: genFx( "toggle" ),
		fadeIn: { opacity: "show" },
		fadeOut: { opacity: "hide" },
		fadeToggle: { opacity: "toggle" }
	}, function( name, props ) {
		jQuery.fn[ name ] = function( speed, easing, callback ) {
			return this.animate( props, speed, easing, callback );
		};
	} );
	
	jQuery.timers = [];
	jQuery.fx.tick = function() {
		var timer,
			i = 0,
			timers = jQuery.timers;
	
		fxNow = jQuery.now();
	
		for ( ; i < timers.length; i++ ) {
			timer = timers[ i ];
	
			// Checks the timer has not already been removed
			if ( !timer() && timers[ i ] === timer ) {
				timers.splice( i--, 1 );
			}
		}
	
		if ( !timers.length ) {
			jQuery.fx.stop();
		}
		fxNow = undefined;
	};
	
	jQuery.fx.timer = function( timer ) {
		jQuery.timers.push( timer );
		if ( timer() ) {
			jQuery.fx.start();
		} else {
			jQuery.timers.pop();
		}
	};
	
	jQuery.fx.interval = 13;
	jQuery.fx.start = function() {
		if ( !timerId ) {
			timerId = window.setInterval( jQuery.fx.tick, jQuery.fx.interval );
		}
	};
	
	jQuery.fx.stop = function() {
		window.clearInterval( timerId );
	
		timerId = null;
	};
	
	jQuery.fx.speeds = {
		slow: 600,
		fast: 200,
	
		// Default speed
		_default: 400
	};
	
	
	// Based off of the plugin by Clint Helfers, with permission.
	// http://web.archive.org/web/20100324014747/http://blindsignals.com/index.php/2009/07/jquery-delay/
	jQuery.fn.delay = function( time, type ) {
		time = jQuery.fx ? jQuery.fx.speeds[ time ] || time : time;
		type = type || "fx";
	
		return this.queue( type, function( next, hooks ) {
			var timeout = window.setTimeout( next, time );
			hooks.stop = function() {
				window.clearTimeout( timeout );
			};
		} );
	};
	
	
	( function() {
		var input = document.createElement( "input" ),
			select = document.createElement( "select" ),
			opt = select.appendChild( document.createElement( "option" ) );
	
		input.type = "checkbox";
	
		// Support: iOS<=5.1, Android<=4.2+
		// Default value for a checkbox should be "on"
		support.checkOn = input.value !== "";
	
		// Support: IE<=11+
		// Must access selectedIndex to make default options select
		support.optSelected = opt.selected;
	
		// Support: Android<=2.3
		// Options inside disabled selects are incorrectly marked as disabled
		select.disabled = true;
		support.optDisabled = !opt.disabled;
	
		// Support: IE<=11+
		// An input loses its value after becoming a radio
		input = document.createElement( "input" );
		input.value = "t";
		input.type = "radio";
		support.radioValue = input.value === "t";
	} )();
	
	
	var boolHook,
		attrHandle = jQuery.expr.attrHandle;
	
	jQuery.fn.extend( {
		attr: function( name, value ) {
			return access( this, jQuery.attr, name, value, arguments.length > 1 );
		},
	
		removeAttr: function( name ) {
			return this.each( function() {
				jQuery.removeAttr( this, name );
			} );
		}
	} );
	
	jQuery.extend( {
		attr: function( elem, name, value ) {
			var ret, hooks,
				nType = elem.nodeType;
	
			// Don't get/set attributes on text, comment and attribute nodes
			if ( nType === 3 || nType === 8 || nType === 2 ) {
				return;
			}
	
			// Fallback to prop when attributes are not supported
			if ( typeof elem.getAttribute === "undefined" ) {
				return jQuery.prop( elem, name, value );
			}
	
			// All attributes are lowercase
			// Grab necessary hook if one is defined
			if ( nType !== 1 || !jQuery.isXMLDoc( elem ) ) {
				name = name.toLowerCase();
				hooks = jQuery.attrHooks[ name ] ||
					( jQuery.expr.match.bool.test( name ) ? boolHook : undefined );
			}
	
			if ( value !== undefined ) {
				if ( value === null ) {
					jQuery.removeAttr( elem, name );
					return;
				}
	
				if ( hooks && "set" in hooks &&
					( ret = hooks.set( elem, value, name ) ) !== undefined ) {
					return ret;
				}
	
				elem.setAttribute( name, value + "" );
				return value;
			}
	
			if ( hooks && "get" in hooks && ( ret = hooks.get( elem, name ) ) !== null ) {
				return ret;
			}
	
			ret = jQuery.find.attr( elem, name );
	
			// Non-existent attributes return null, we normalize to undefined
			return ret == null ? undefined : ret;
		},
	
		attrHooks: {
			type: {
				set: function( elem, value ) {
					if ( !support.radioValue && value === "radio" &&
						jQuery.nodeName( elem, "input" ) ) {
						var val = elem.value;
						elem.setAttribute( "type", value );
						if ( val ) {
							elem.value = val;
						}
						return value;
					}
				}
			}
		},
	
		removeAttr: function( elem, value ) {
			var name, propName,
				i = 0,
				attrNames = value && value.match( rnotwhite );
	
			if ( attrNames && elem.nodeType === 1 ) {
				while ( ( name = attrNames[ i++ ] ) ) {
					propName = jQuery.propFix[ name ] || name;
	
					// Boolean attributes get special treatment (#10870)
					if ( jQuery.expr.match.bool.test( name ) ) {
	
						// Set corresponding property to false
						elem[ propName ] = false;
					}
	
					elem.removeAttribute( name );
				}
			}
		}
	} );
	
	// Hooks for boolean attributes
	boolHook = {
		set: function( elem, value, name ) {
			if ( value === false ) {
	
				// Remove boolean attributes when set to false
				jQuery.removeAttr( elem, name );
			} else {
				elem.setAttribute( name, name );
			}
			return name;
		}
	};
	jQuery.each( jQuery.expr.match.bool.source.match( /\w+/g ), function( i, name ) {
		var getter = attrHandle[ name ] || jQuery.find.attr;
	
		attrHandle[ name ] = function( elem, name, isXML ) {
			var ret, handle;
			if ( !isXML ) {
	
				// Avoid an infinite loop by temporarily removing this function from the getter
				handle = attrHandle[ name ];
				attrHandle[ name ] = ret;
				ret = getter( elem, name, isXML ) != null ?
					name.toLowerCase() :
					null;
				attrHandle[ name ] = handle;
			}
			return ret;
		};
	} );
	
	
	
	
	var rfocusable = /^(?:input|select|textarea|button)$/i,
		rclickable = /^(?:a|area)$/i;
	
	jQuery.fn.extend( {
		prop: function( name, value ) {
			return access( this, jQuery.prop, name, value, arguments.length > 1 );
		},
	
		removeProp: function( name ) {
			return this.each( function() {
				delete this[ jQuery.propFix[ name ] || name ];
			} );
		}
	} );
	
	jQuery.extend( {
		prop: function( elem, name, value ) {
			var ret, hooks,
				nType = elem.nodeType;
	
			// Don't get/set properties on text, comment and attribute nodes
			if ( nType === 3 || nType === 8 || nType === 2 ) {
				return;
			}
	
			if ( nType !== 1 || !jQuery.isXMLDoc( elem ) ) {
	
				// Fix name and attach hooks
				name = jQuery.propFix[ name ] || name;
				hooks = jQuery.propHooks[ name ];
			}
	
			if ( value !== undefined ) {
				if ( hooks && "set" in hooks &&
					( ret = hooks.set( elem, value, name ) ) !== undefined ) {
					return ret;
				}
	
				return ( elem[ name ] = value );
			}
	
			if ( hooks && "get" in hooks && ( ret = hooks.get( elem, name ) ) !== null ) {
				return ret;
			}
	
			return elem[ name ];
		},
	
		propHooks: {
			tabIndex: {
				get: function( elem ) {
	
					// elem.tabIndex doesn't always return the
					// correct value when it hasn't been explicitly set
					// http://fluidproject.org/blog/2008/01/09/getting-setting-and-removing-tabindex-values-with-javascript/
					// Use proper attribute retrieval(#12072)
					var tabindex = jQuery.find.attr( elem, "tabindex" );
	
					return tabindex ?
						parseInt( tabindex, 10 ) :
						rfocusable.test( elem.nodeName ) ||
							rclickable.test( elem.nodeName ) && elem.href ?
								0 :
								-1;
				}
			}
		},
	
		propFix: {
			"for": "htmlFor",
			"class": "className"
		}
	} );
	
	if ( !support.optSelected ) {
		jQuery.propHooks.selected = {
			get: function( elem ) {
				var parent = elem.parentNode;
				if ( parent && parent.parentNode ) {
					parent.parentNode.selectedIndex;
				}
				return null;
			}
		};
	}
	
	jQuery.each( [
		"tabIndex",
		"readOnly",
		"maxLength",
		"cellSpacing",
		"cellPadding",
		"rowSpan",
		"colSpan",
		"useMap",
		"frameBorder",
		"contentEditable"
	], function() {
		jQuery.propFix[ this.toLowerCase() ] = this;
	} );
	
	
	
	
	var rclass = /[\t\r\n\f]/g;
	
	function getClass( elem ) {
		return elem.getAttribute && elem.getAttribute( "class" ) || "";
	}
	
	jQuery.fn.extend( {
		addClass: function( value ) {
			var classes, elem, cur, curValue, clazz, j, finalValue,
				i = 0;
	
			if ( jQuery.isFunction( value ) ) {
				return this.each( function( j ) {
					jQuery( this ).addClass( value.call( this, j, getClass( this ) ) );
				} );
			}
	
			if ( typeof value === "string" && value ) {
				classes = value.match( rnotwhite ) || [];
	
				while ( ( elem = this[ i++ ] ) ) {
					curValue = getClass( elem );
					cur = elem.nodeType === 1 &&
						( " " + curValue + " " ).replace( rclass, " " );
	
					if ( cur ) {
						j = 0;
						while ( ( clazz = classes[ j++ ] ) ) {
							if ( cur.indexOf( " " + clazz + " " ) < 0 ) {
								cur += clazz + " ";
							}
						}
	
						// Only assign if different to avoid unneeded rendering.
						finalValue = jQuery.trim( cur );
						if ( curValue !== finalValue ) {
							elem.setAttribute( "class", finalValue );
						}
					}
				}
			}
	
			return this;
		},
	
		removeClass: function( value ) {
			var classes, elem, cur, curValue, clazz, j, finalValue,
				i = 0;
	
			if ( jQuery.isFunction( value ) ) {
				return this.each( function( j ) {
					jQuery( this ).removeClass( value.call( this, j, getClass( this ) ) );
				} );
			}
	
			if ( !arguments.length ) {
				return this.attr( "class", "" );
			}
	
			if ( typeof value === "string" && value ) {
				classes = value.match( rnotwhite ) || [];
	
				while ( ( elem = this[ i++ ] ) ) {
					curValue = getClass( elem );
	
					// This expression is here for better compressibility (see addClass)
					cur = elem.nodeType === 1 &&
						( " " + curValue + " " ).replace( rclass, " " );
	
					if ( cur ) {
						j = 0;
						while ( ( clazz = classes[ j++ ] ) ) {
	
							// Remove *all* instances
							while ( cur.indexOf( " " + clazz + " " ) > -1 ) {
								cur = cur.replace( " " + clazz + " ", " " );
							}
						}
	
						// Only assign if different to avoid unneeded rendering.
						finalValue = jQuery.trim( cur );
						if ( curValue !== finalValue ) {
							elem.setAttribute( "class", finalValue );
						}
					}
				}
			}
	
			return this;
		},
	
		toggleClass: function( value, stateVal ) {
			var type = typeof value;
	
			if ( typeof stateVal === "boolean" && type === "string" ) {
				return stateVal ? this.addClass( value ) : this.removeClass( value );
			}
	
			if ( jQuery.isFunction( value ) ) {
				return this.each( function( i ) {
					jQuery( this ).toggleClass(
						value.call( this, i, getClass( this ), stateVal ),
						stateVal
					);
				} );
			}
	
			return this.each( function() {
				var className, i, self, classNames;
	
				if ( type === "string" ) {
	
					// Toggle individual class names
					i = 0;
					self = jQuery( this );
					classNames = value.match( rnotwhite ) || [];
	
					while ( ( className = classNames[ i++ ] ) ) {
	
						// Check each className given, space separated list
						if ( self.hasClass( className ) ) {
							self.removeClass( className );
						} else {
							self.addClass( className );
						}
					}
	
				// Toggle whole class name
				} else if ( value === undefined || type === "boolean" ) {
					className = getClass( this );
					if ( className ) {
	
						// Store className if set
						dataPriv.set( this, "__className__", className );
					}
	
					// If the element has a class name or if we're passed `false`,
					// then remove the whole classname (if there was one, the above saved it).
					// Otherwise bring back whatever was previously saved (if anything),
					// falling back to the empty string if nothing was stored.
					if ( this.setAttribute ) {
						this.setAttribute( "class",
							className || value === false ?
							"" :
							dataPriv.get( this, "__className__" ) || ""
						);
					}
				}
			} );
		},
	
		hasClass: function( selector ) {
			var className, elem,
				i = 0;
	
			className = " " + selector + " ";
			while ( ( elem = this[ i++ ] ) ) {
				if ( elem.nodeType === 1 &&
					( " " + getClass( elem ) + " " ).replace( rclass, " " )
						.indexOf( className ) > -1
				) {
					return true;
				}
			}
	
			return false;
		}
	} );
	
	
	
	
	var rreturn = /\r/g;
	
	jQuery.fn.extend( {
		val: function( value ) {
			var hooks, ret, isFunction,
				elem = this[ 0 ];
	
			if ( !arguments.length ) {
				if ( elem ) {
					hooks = jQuery.valHooks[ elem.type ] ||
						jQuery.valHooks[ elem.nodeName.toLowerCase() ];
	
					if ( hooks &&
						"get" in hooks &&
						( ret = hooks.get( elem, "value" ) ) !== undefined
					) {
						return ret;
					}
	
					ret = elem.value;
	
					return typeof ret === "string" ?
	
						// Handle most common string cases
						ret.replace( rreturn, "" ) :
	
						// Handle cases where value is null/undef or number
						ret == null ? "" : ret;
				}
	
				return;
			}
	
			isFunction = jQuery.isFunction( value );
	
			return this.each( function( i ) {
				var val;
	
				if ( this.nodeType !== 1 ) {
					return;
				}
	
				if ( isFunction ) {
					val = value.call( this, i, jQuery( this ).val() );
				} else {
					val = value;
				}
	
				// Treat null/undefined as ""; convert numbers to string
				if ( val == null ) {
					val = "";
	
				} else if ( typeof val === "number" ) {
					val += "";
	
				} else if ( jQuery.isArray( val ) ) {
					val = jQuery.map( val, function( value ) {
						return value == null ? "" : value + "";
					} );
				}
	
				hooks = jQuery.valHooks[ this.type ] || jQuery.valHooks[ this.nodeName.toLowerCase() ];
	
				// If set returns undefined, fall back to normal setting
				if ( !hooks || !( "set" in hooks ) || hooks.set( this, val, "value" ) === undefined ) {
					this.value = val;
				}
			} );
		}
	} );
	
	jQuery.extend( {
		valHooks: {
			option: {
				get: function( elem ) {
	
					// Support: IE<11
					// option.value not trimmed (#14858)
					return jQuery.trim( elem.value );
				}
			},
			select: {
				get: function( elem ) {
					var value, option,
						options = elem.options,
						index = elem.selectedIndex,
						one = elem.type === "select-one" || index < 0,
						values = one ? null : [],
						max = one ? index + 1 : options.length,
						i = index < 0 ?
							max :
							one ? index : 0;
	
					// Loop through all the selected options
					for ( ; i < max; i++ ) {
						option = options[ i ];
	
						// IE8-9 doesn't update selected after form reset (#2551)
						if ( ( option.selected || i === index ) &&
	
								// Don't return options that are disabled or in a disabled optgroup
								( support.optDisabled ?
									!option.disabled : option.getAttribute( "disabled" ) === null ) &&
								( !option.parentNode.disabled ||
									!jQuery.nodeName( option.parentNode, "optgroup" ) ) ) {
	
							// Get the specific value for the option
							value = jQuery( option ).val();
	
							// We don't need an array for one selects
							if ( one ) {
								return value;
							}
	
							// Multi-Selects return an array
							values.push( value );
						}
					}
	
					return values;
				},
	
				set: function( elem, value ) {
					var optionSet, option,
						options = elem.options,
						values = jQuery.makeArray( value ),
						i = options.length;
	
					while ( i-- ) {
						option = options[ i ];
						if ( option.selected =
								jQuery.inArray( jQuery.valHooks.option.get( option ), values ) > -1
						) {
							optionSet = true;
						}
					}
	
					// Force browsers to behave consistently when non-matching value is set
					if ( !optionSet ) {
						elem.selectedIndex = -1;
					}
					return values;
				}
			}
		}
	} );
	
	// Radios and checkboxes getter/setter
	jQuery.each( [ "radio", "checkbox" ], function() {
		jQuery.valHooks[ this ] = {
			set: function( elem, value ) {
				if ( jQuery.isArray( value ) ) {
					return ( elem.checked = jQuery.inArray( jQuery( elem ).val(), value ) > -1 );
				}
			}
		};
		if ( !support.checkOn ) {
			jQuery.valHooks[ this ].get = function( elem ) {
				return elem.getAttribute( "value" ) === null ? "on" : elem.value;
			};
		}
	} );
	
	
	
	
	// Return jQuery for attributes-only inclusion
	
	
	var rfocusMorph = /^(?:focusinfocus|focusoutblur)$/;
	
	jQuery.extend( jQuery.event, {
	
		trigger: function( event, data, elem, onlyHandlers ) {
	
			var i, cur, tmp, bubbleType, ontype, handle, special,
				eventPath = [ elem || document ],
				type = hasOwn.call( event, "type" ) ? event.type : event,
				namespaces = hasOwn.call( event, "namespace" ) ? event.namespace.split( "." ) : [];
	
			cur = tmp = elem = elem || document;
	
			// Don't do events on text and comment nodes
			if ( elem.nodeType === 3 || elem.nodeType === 8 ) {
				return;
			}
	
			// focus/blur morphs to focusin/out; ensure we're not firing them right now
			if ( rfocusMorph.test( type + jQuery.event.triggered ) ) {
				return;
			}
	
			if ( type.indexOf( "." ) > -1 ) {
	
				// Namespaced trigger; create a regexp to match event type in handle()
				namespaces = type.split( "." );
				type = namespaces.shift();
				namespaces.sort();
			}
			ontype = type.indexOf( ":" ) < 0 && "on" + type;
	
			// Caller can pass in a jQuery.Event object, Object, or just an event type string
			event = event[ jQuery.expando ] ?
				event :
				new jQuery.Event( type, typeof event === "object" && event );
	
			// Trigger bitmask: & 1 for native handlers; & 2 for jQuery (always true)
			event.isTrigger = onlyHandlers ? 2 : 3;
			event.namespace = namespaces.join( "." );
			event.rnamespace = event.namespace ?
				new RegExp( "(^|\\.)" + namespaces.join( "\\.(?:.*\\.|)" ) + "(\\.|$)" ) :
				null;
	
			// Clean up the event in case it is being reused
			event.result = undefined;
			if ( !event.target ) {
				event.target = elem;
			}
	
			// Clone any incoming data and prepend the event, creating the handler arg list
			data = data == null ?
				[ event ] :
				jQuery.makeArray( data, [ event ] );
	
			// Allow special events to draw outside the lines
			special = jQuery.event.special[ type ] || {};
			if ( !onlyHandlers && special.trigger && special.trigger.apply( elem, data ) === false ) {
				return;
			}
	
			// Determine event propagation path in advance, per W3C events spec (#9951)
			// Bubble up to document, then to window; watch for a global ownerDocument var (#9724)
			if ( !onlyHandlers && !special.noBubble && !jQuery.isWindow( elem ) ) {
	
				bubbleType = special.delegateType || type;
				if ( !rfocusMorph.test( bubbleType + type ) ) {
					cur = cur.parentNode;
				}
				for ( ; cur; cur = cur.parentNode ) {
					eventPath.push( cur );
					tmp = cur;
				}
	
				// Only add window if we got to document (e.g., not plain obj or detached DOM)
				if ( tmp === ( elem.ownerDocument || document ) ) {
					eventPath.push( tmp.defaultView || tmp.parentWindow || window );
				}
			}
	
			// Fire handlers on the event path
			i = 0;
			while ( ( cur = eventPath[ i++ ] ) && !event.isPropagationStopped() ) {
	
				event.type = i > 1 ?
					bubbleType :
					special.bindType || type;
	
				// jQuery handler
				handle = ( dataPriv.get( cur, "events" ) || {} )[ event.type ] &&
					dataPriv.get( cur, "handle" );
				if ( handle ) {
					handle.apply( cur, data );
				}
	
				// Native handler
				handle = ontype && cur[ ontype ];
				if ( handle && handle.apply && acceptData( cur ) ) {
					event.result = handle.apply( cur, data );
					if ( event.result === false ) {
						event.preventDefault();
					}
				}
			}
			event.type = type;
	
			// If nobody prevented the default action, do it now
			if ( !onlyHandlers && !event.isDefaultPrevented() ) {
	
				if ( ( !special._default ||
					special._default.apply( eventPath.pop(), data ) === false ) &&
					acceptData( elem ) ) {
	
					// Call a native DOM method on the target with the same name name as the event.
					// Don't do default actions on window, that's where global variables be (#6170)
					if ( ontype && jQuery.isFunction( elem[ type ] ) && !jQuery.isWindow( elem ) ) {
	
						// Don't re-trigger an onFOO event when we call its FOO() method
						tmp = elem[ ontype ];
	
						if ( tmp ) {
							elem[ ontype ] = null;
						}
	
						// Prevent re-triggering of the same event, since we already bubbled it above
						jQuery.event.triggered = type;
						elem[ type ]();
						jQuery.event.triggered = undefined;
	
						if ( tmp ) {
							elem[ ontype ] = tmp;
						}
					}
				}
			}
	
			return event.result;
		},
	
		// Piggyback on a donor event to simulate a different one
		simulate: function( type, elem, event ) {
			var e = jQuery.extend(
				new jQuery.Event(),
				event,
				{
					type: type,
					isSimulated: true
	
					// Previously, `originalEvent: {}` was set here, so stopPropagation call
					// would not be triggered on donor event, since in our own
					// jQuery.event.stopPropagation function we had a check for existence of
					// originalEvent.stopPropagation method, so, consequently it would be a noop.
					//
					// But now, this "simulate" function is used only for events
					// for which stopPropagation() is noop, so there is no need for that anymore.
					//
					// For the 1.x branch though, guard for "click" and "submit"
					// events is still used, but was moved to jQuery.event.stopPropagation function
					// because `originalEvent` should point to the original event for the constancy
					// with other events and for more focused logic
				}
			);
	
			jQuery.event.trigger( e, null, elem );
	
			if ( e.isDefaultPrevented() ) {
				event.preventDefault();
			}
		}
	
	} );
	
	jQuery.fn.extend( {
	
		trigger: function( type, data ) {
			return this.each( function() {
				jQuery.event.trigger( type, data, this );
			} );
		},
		triggerHandler: function( type, data ) {
			var elem = this[ 0 ];
			if ( elem ) {
				return jQuery.event.trigger( type, data, elem, true );
			}
		}
	} );
	
	
	jQuery.each( ( "blur focus focusin focusout load resize scroll unload click dblclick " +
		"mousedown mouseup mousemove mouseover mouseout mouseenter mouseleave " +
		"change select submit keydown keypress keyup error contextmenu" ).split( " " ),
		function( i, name ) {
	
		// Handle event binding
		jQuery.fn[ name ] = function( data, fn ) {
			return arguments.length > 0 ?
				this.on( name, null, data, fn ) :
				this.trigger( name );
		};
	} );
	
	jQuery.fn.extend( {
		hover: function( fnOver, fnOut ) {
			return this.mouseenter( fnOver ).mouseleave( fnOut || fnOver );
		}
	} );
	
	
	
	
	support.focusin = "onfocusin" in window;
	
	
	// Support: Firefox
	// Firefox doesn't have focus(in | out) events
	// Related ticket - https://bugzilla.mozilla.org/show_bug.cgi?id=687787
	//
	// Support: Chrome, Safari
	// focus(in | out) events fire after focus & blur events,
	// which is spec violation - http://www.w3.org/TR/DOM-Level-3-Events/#events-focusevent-event-order
	// Related ticket - https://code.google.com/p/chromium/issues/detail?id=449857
	if ( !support.focusin ) {
		jQuery.each( { focus: "focusin", blur: "focusout" }, function( orig, fix ) {
	
			// Attach a single capturing handler on the document while someone wants focusin/focusout
			var handler = function( event ) {
				jQuery.event.simulate( fix, event.target, jQuery.event.fix( event ) );
			};
	
			jQuery.event.special[ fix ] = {
				setup: function() {
					var doc = this.ownerDocument || this,
						attaches = dataPriv.access( doc, fix );
	
					if ( !attaches ) {
						doc.addEventListener( orig, handler, true );
					}
					dataPriv.access( doc, fix, ( attaches || 0 ) + 1 );
				},
				teardown: function() {
					var doc = this.ownerDocument || this,
						attaches = dataPriv.access( doc, fix ) - 1;
	
					if ( !attaches ) {
						doc.removeEventListener( orig, handler, true );
						dataPriv.remove( doc, fix );
	
					} else {
						dataPriv.access( doc, fix, attaches );
					}
				}
			};
		} );
	}
	var location = window.location;
	
	var nonce = jQuery.now();
	
	var rquery = ( /\?/ );
	
	
	
	// Support: Android 2.3
	// Workaround failure to string-cast null input
	jQuery.parseJSON = function( data ) {
		return JSON.parse( data + "" );
	};
	
	
	// Cross-browser xml parsing
	jQuery.parseXML = function( data ) {
		var xml;
		if ( !data || typeof data !== "string" ) {
			return null;
		}
	
		// Support: IE9
		try {
			xml = ( new window.DOMParser() ).parseFromString( data, "text/xml" );
		} catch ( e ) {
			xml = undefined;
		}
	
		if ( !xml || xml.getElementsByTagName( "parsererror" ).length ) {
			jQuery.error( "Invalid XML: " + data );
		}
		return xml;
	};
	
	
	var
		rhash = /#.*$/,
		rts = /([?&])_=[^&]*/,
		rheaders = /^(.*?):[ \t]*([^\r\n]*)$/mg,
	
		// #7653, #8125, #8152: local protocol detection
		rlocalProtocol = /^(?:about|app|app-storage|.+-extension|file|res|widget):$/,
		rnoContent = /^(?:GET|HEAD)$/,
		rprotocol = /^\/\//,
	
		/* Prefilters
		 * 1) They are useful to introduce custom dataTypes (see ajax/jsonp.js for an example)
		 * 2) These are called:
		 *    - BEFORE asking for a transport
		 *    - AFTER param serialization (s.data is a string if s.processData is true)
		 * 3) key is the dataType
		 * 4) the catchall symbol "*" can be used
		 * 5) execution will start with transport dataType and THEN continue down to "*" if needed
		 */
		prefilters = {},
	
		/* Transports bindings
		 * 1) key is the dataType
		 * 2) the catchall symbol "*" can be used
		 * 3) selection will start with transport dataType and THEN go to "*" if needed
		 */
		transports = {},
	
		// Avoid comment-prolog char sequence (#10098); must appease lint and evade compression
		allTypes = "*/".concat( "*" ),
	
		// Anchor tag for parsing the document origin
		originAnchor = document.createElement( "a" );
		originAnchor.href = location.href;
	
	// Base "constructor" for jQuery.ajaxPrefilter and jQuery.ajaxTransport
	function addToPrefiltersOrTransports( structure ) {
	
		// dataTypeExpression is optional and defaults to "*"
		return function( dataTypeExpression, func ) {
	
			if ( typeof dataTypeExpression !== "string" ) {
				func = dataTypeExpression;
				dataTypeExpression = "*";
			}
	
			var dataType,
				i = 0,
				dataTypes = dataTypeExpression.toLowerCase().match( rnotwhite ) || [];
	
			if ( jQuery.isFunction( func ) ) {
	
				// For each dataType in the dataTypeExpression
				while ( ( dataType = dataTypes[ i++ ] ) ) {
	
					// Prepend if requested
					if ( dataType[ 0 ] === "+" ) {
						dataType = dataType.slice( 1 ) || "*";
						( structure[ dataType ] = structure[ dataType ] || [] ).unshift( func );
	
					// Otherwise append
					} else {
						( structure[ dataType ] = structure[ dataType ] || [] ).push( func );
					}
				}
			}
		};
	}
	
	// Base inspection function for prefilters and transports
	function inspectPrefiltersOrTransports( structure, options, originalOptions, jqXHR ) {
	
		var inspected = {},
			seekingTransport = ( structure === transports );
	
		function inspect( dataType ) {
			var selected;
			inspected[ dataType ] = true;
			jQuery.each( structure[ dataType ] || [], function( _, prefilterOrFactory ) {
				var dataTypeOrTransport = prefilterOrFactory( options, originalOptions, jqXHR );
				if ( typeof dataTypeOrTransport === "string" &&
					!seekingTransport && !inspected[ dataTypeOrTransport ] ) {
	
					options.dataTypes.unshift( dataTypeOrTransport );
					inspect( dataTypeOrTransport );
					return false;
				} else if ( seekingTransport ) {
					return !( selected = dataTypeOrTransport );
				}
			} );
			return selected;
		}
	
		return inspect( options.dataTypes[ 0 ] ) || !inspected[ "*" ] && inspect( "*" );
	}
	
	// A special extend for ajax options
	// that takes "flat" options (not to be deep extended)
	// Fixes #9887
	function ajaxExtend( target, src ) {
		var key, deep,
			flatOptions = jQuery.ajaxSettings.flatOptions || {};
	
		for ( key in src ) {
			if ( src[ key ] !== undefined ) {
				( flatOptions[ key ] ? target : ( deep || ( deep = {} ) ) )[ key ] = src[ key ];
			}
		}
		if ( deep ) {
			jQuery.extend( true, target, deep );
		}
	
		return target;
	}
	
	/* Handles responses to an ajax request:
	 * - finds the right dataType (mediates between content-type and expected dataType)
	 * - returns the corresponding response
	 */
	function ajaxHandleResponses( s, jqXHR, responses ) {
	
		var ct, type, finalDataType, firstDataType,
			contents = s.contents,
			dataTypes = s.dataTypes;
	
		// Remove auto dataType and get content-type in the process
		while ( dataTypes[ 0 ] === "*" ) {
			dataTypes.shift();
			if ( ct === undefined ) {
				ct = s.mimeType || jqXHR.getResponseHeader( "Content-Type" );
			}
		}
	
		// Check if we're dealing with a known content-type
		if ( ct ) {
			for ( type in contents ) {
				if ( contents[ type ] && contents[ type ].test( ct ) ) {
					dataTypes.unshift( type );
					break;
				}
			}
		}
	
		// Check to see if we have a response for the expected dataType
		if ( dataTypes[ 0 ] in responses ) {
			finalDataType = dataTypes[ 0 ];
		} else {
	
			// Try convertible dataTypes
			for ( type in responses ) {
				if ( !dataTypes[ 0 ] || s.converters[ type + " " + dataTypes[ 0 ] ] ) {
					finalDataType = type;
					break;
				}
				if ( !firstDataType ) {
					firstDataType = type;
				}
			}
	
			// Or just use first one
			finalDataType = finalDataType || firstDataType;
		}
	
		// If we found a dataType
		// We add the dataType to the list if needed
		// and return the corresponding response
		if ( finalDataType ) {
			if ( finalDataType !== dataTypes[ 0 ] ) {
				dataTypes.unshift( finalDataType );
			}
			return responses[ finalDataType ];
		}
	}
	
	/* Chain conversions given the request and the original response
	 * Also sets the responseXXX fields on the jqXHR instance
	 */
	function ajaxConvert( s, response, jqXHR, isSuccess ) {
		var conv2, current, conv, tmp, prev,
			converters = {},
	
			// Work with a copy of dataTypes in case we need to modify it for conversion
			dataTypes = s.dataTypes.slice();
	
		// Create converters map with lowercased keys
		if ( dataTypes[ 1 ] ) {
			for ( conv in s.converters ) {
				converters[ conv.toLowerCase() ] = s.converters[ conv ];
			}
		}
	
		current = dataTypes.shift();
	
		// Convert to each sequential dataType
		while ( current ) {
	
			if ( s.responseFields[ current ] ) {
				jqXHR[ s.responseFields[ current ] ] = response;
			}
	
			// Apply the dataFilter if provided
			if ( !prev && isSuccess && s.dataFilter ) {
				response = s.dataFilter( response, s.dataType );
			}
	
			prev = current;
			current = dataTypes.shift();
	
			if ( current ) {
	
			// There's only work to do if current dataType is non-auto
				if ( current === "*" ) {
	
					current = prev;
	
				// Convert response if prev dataType is non-auto and differs from current
				} else if ( prev !== "*" && prev !== current ) {
	
					// Seek a direct converter
					conv = converters[ prev + " " + current ] || converters[ "* " + current ];
	
					// If none found, seek a pair
					if ( !conv ) {
						for ( conv2 in converters ) {
	
							// If conv2 outputs current
							tmp = conv2.split( " " );
							if ( tmp[ 1 ] === current ) {
	
								// If prev can be converted to accepted input
								conv = converters[ prev + " " + tmp[ 0 ] ] ||
									converters[ "* " + tmp[ 0 ] ];
								if ( conv ) {
	
									// Condense equivalence converters
									if ( conv === true ) {
										conv = converters[ conv2 ];
	
									// Otherwise, insert the intermediate dataType
									} else if ( converters[ conv2 ] !== true ) {
										current = tmp[ 0 ];
										dataTypes.unshift( tmp[ 1 ] );
									}
									break;
								}
							}
						}
					}
	
					// Apply converter (if not an equivalence)
					if ( conv !== true ) {
	
						// Unless errors are allowed to bubble, catch and return them
						if ( conv && s.throws ) {
							response = conv( response );
						} else {
							try {
								response = conv( response );
							} catch ( e ) {
								return {
									state: "parsererror",
									error: conv ? e : "No conversion from " + prev + " to " + current
								};
							}
						}
					}
				}
			}
		}
	
		return { state: "success", data: response };
	}
	
	jQuery.extend( {
	
		// Counter for holding the number of active queries
		active: 0,
	
		// Last-Modified header cache for next request
		lastModified: {},
		etag: {},
	
		ajaxSettings: {
			url: location.href,
			type: "GET",
			isLocal: rlocalProtocol.test( location.protocol ),
			global: true,
			processData: true,
			async: true,
			contentType: "application/x-www-form-urlencoded; charset=UTF-8",
			/*
			timeout: 0,
			data: null,
			dataType: null,
			username: null,
			password: null,
			cache: null,
			throws: false,
			traditional: false,
			headers: {},
			*/
	
			accepts: {
				"*": allTypes,
				text: "text/plain",
				html: "text/html",
				xml: "application/xml, text/xml",
				json: "application/json, text/javascript"
			},
	
			contents: {
				xml: /\bxml\b/,
				html: /\bhtml/,
				json: /\bjson\b/
			},
	
			responseFields: {
				xml: "responseXML",
				text: "responseText",
				json: "responseJSON"
			},
	
			// Data converters
			// Keys separate source (or catchall "*") and destination types with a single space
			converters: {
	
				// Convert anything to text
				"* text": String,
	
				// Text to html (true = no transformation)
				"text html": true,
	
				// Evaluate text as a json expression
				"text json": jQuery.parseJSON,
	
				// Parse text as xml
				"text xml": jQuery.parseXML
			},
	
			// For options that shouldn't be deep extended:
			// you can add your own custom options here if
			// and when you create one that shouldn't be
			// deep extended (see ajaxExtend)
			flatOptions: {
				url: true,
				context: true
			}
		},
	
		// Creates a full fledged settings object into target
		// with both ajaxSettings and settings fields.
		// If target is omitted, writes into ajaxSettings.
		ajaxSetup: function( target, settings ) {
			return settings ?
	
				// Building a settings object
				ajaxExtend( ajaxExtend( target, jQuery.ajaxSettings ), settings ) :
	
				// Extending ajaxSettings
				ajaxExtend( jQuery.ajaxSettings, target );
		},
	
		ajaxPrefilter: addToPrefiltersOrTransports( prefilters ),
		ajaxTransport: addToPrefiltersOrTransports( transports ),
	
		// Main method
		ajax: function( url, options ) {
	
			// If url is an object, simulate pre-1.5 signature
			if ( typeof url === "object" ) {
				options = url;
				url = undefined;
			}
	
			// Force options to be an object
			options = options || {};
	
			var transport,
	
				// URL without anti-cache param
				cacheURL,
	
				// Response headers
				responseHeadersString,
				responseHeaders,
	
				// timeout handle
				timeoutTimer,
	
				// Url cleanup var
				urlAnchor,
	
				// To know if global events are to be dispatched
				fireGlobals,
	
				// Loop variable
				i,
	
				// Create the final options object
				s = jQuery.ajaxSetup( {}, options ),
	
				// Callbacks context
				callbackContext = s.context || s,
	
				// Context for global events is callbackContext if it is a DOM node or jQuery collection
				globalEventContext = s.context &&
					( callbackContext.nodeType || callbackContext.jquery ) ?
						jQuery( callbackContext ) :
						jQuery.event,
	
				// Deferreds
				deferred = jQuery.Deferred(),
				completeDeferred = jQuery.Callbacks( "once memory" ),
	
				// Status-dependent callbacks
				statusCode = s.statusCode || {},
	
				// Headers (they are sent all at once)
				requestHeaders = {},
				requestHeadersNames = {},
	
				// The jqXHR state
				state = 0,
	
				// Default abort message
				strAbort = "canceled",
	
				// Fake xhr
				jqXHR = {
					readyState: 0,
	
					// Builds headers hashtable if needed
					getResponseHeader: function( key ) {
						var match;
						if ( state === 2 ) {
							if ( !responseHeaders ) {
								responseHeaders = {};
								while ( ( match = rheaders.exec( responseHeadersString ) ) ) {
									responseHeaders[ match[ 1 ].toLowerCase() ] = match[ 2 ];
								}
							}
							match = responseHeaders[ key.toLowerCase() ];
						}
						return match == null ? null : match;
					},
	
					// Raw string
					getAllResponseHeaders: function() {
						return state === 2 ? responseHeadersString : null;
					},
	
					// Caches the header
					setRequestHeader: function( name, value ) {
						var lname = name.toLowerCase();
						if ( !state ) {
							name = requestHeadersNames[ lname ] = requestHeadersNames[ lname ] || name;
							requestHeaders[ name ] = value;
						}
						return this;
					},
	
					// Overrides response content-type header
					overrideMimeType: function( type ) {
						if ( !state ) {
							s.mimeType = type;
						}
						return this;
					},
	
					// Status-dependent callbacks
					statusCode: function( map ) {
						var code;
						if ( map ) {
							if ( state < 2 ) {
								for ( code in map ) {
	
									// Lazy-add the new callback in a way that preserves old ones
									statusCode[ code ] = [ statusCode[ code ], map[ code ] ];
								}
							} else {
	
								// Execute the appropriate callbacks
								jqXHR.always( map[ jqXHR.status ] );
							}
						}
						return this;
					},
	
					// Cancel the request
					abort: function( statusText ) {
						var finalText = statusText || strAbort;
						if ( transport ) {
							transport.abort( finalText );
						}
						done( 0, finalText );
						return this;
					}
				};
	
			// Attach deferreds
			deferred.promise( jqXHR ).complete = completeDeferred.add;
			jqXHR.success = jqXHR.done;
			jqXHR.error = jqXHR.fail;
	
			// Remove hash character (#7531: and string promotion)
			// Add protocol if not provided (prefilters might expect it)
			// Handle falsy url in the settings object (#10093: consistency with old signature)
			// We also use the url parameter if available
			s.url = ( ( url || s.url || location.href ) + "" ).replace( rhash, "" )
				.replace( rprotocol, location.protocol + "//" );
	
			// Alias method option to type as per ticket #12004
			s.type = options.method || options.type || s.method || s.type;
	
			// Extract dataTypes list
			s.dataTypes = jQuery.trim( s.dataType || "*" ).toLowerCase().match( rnotwhite ) || [ "" ];
	
			// A cross-domain request is in order when the origin doesn't match the current origin.
			if ( s.crossDomain == null ) {
				urlAnchor = document.createElement( "a" );
	
				// Support: IE8-11+
				// IE throws exception if url is malformed, e.g. http://example.com:80x/
				try {
					urlAnchor.href = s.url;
	
					// Support: IE8-11+
					// Anchor's host property isn't correctly set when s.url is relative
					urlAnchor.href = urlAnchor.href;
					s.crossDomain = originAnchor.protocol + "//" + originAnchor.host !==
						urlAnchor.protocol + "//" + urlAnchor.host;
				} catch ( e ) {
	
					// If there is an error parsing the URL, assume it is crossDomain,
					// it can be rejected by the transport if it is invalid
					s.crossDomain = true;
				}
			}
	
			// Convert data if not already a string
			if ( s.data && s.processData && typeof s.data !== "string" ) {
				s.data = jQuery.param( s.data, s.traditional );
			}
	
			// Apply prefilters
			inspectPrefiltersOrTransports( prefilters, s, options, jqXHR );
	
			// If request was aborted inside a prefilter, stop there
			if ( state === 2 ) {
				return jqXHR;
			}
	
			// We can fire global events as of now if asked to
			// Don't fire events if jQuery.event is undefined in an AMD-usage scenario (#15118)
			fireGlobals = jQuery.event && s.global;
	
			// Watch for a new set of requests
			if ( fireGlobals && jQuery.active++ === 0 ) {
				jQuery.event.trigger( "ajaxStart" );
			}
	
			// Uppercase the type
			s.type = s.type.toUpperCase();
	
			// Determine if request has content
			s.hasContent = !rnoContent.test( s.type );
	
			// Save the URL in case we're toying with the If-Modified-Since
			// and/or If-None-Match header later on
			cacheURL = s.url;
	
			// More options handling for requests with no content
			if ( !s.hasContent ) {
	
				// If data is available, append data to url
				if ( s.data ) {
					cacheURL = ( s.url += ( rquery.test( cacheURL ) ? "&" : "?" ) + s.data );
	
					// #9682: remove data so that it's not used in an eventual retry
					delete s.data;
				}
	
				// Add anti-cache in url if needed
				if ( s.cache === false ) {
					s.url = rts.test( cacheURL ) ?
	
						// If there is already a '_' parameter, set its value
						cacheURL.replace( rts, "$1_=" + nonce++ ) :
	
						// Otherwise add one to the end
						cacheURL + ( rquery.test( cacheURL ) ? "&" : "?" ) + "_=" + nonce++;
				}
			}
	
			// Set the If-Modified-Since and/or If-None-Match header, if in ifModified mode.
			if ( s.ifModified ) {
				if ( jQuery.lastModified[ cacheURL ] ) {
					jqXHR.setRequestHeader( "If-Modified-Since", jQuery.lastModified[ cacheURL ] );
				}
				if ( jQuery.etag[ cacheURL ] ) {
					jqXHR.setRequestHeader( "If-None-Match", jQuery.etag[ cacheURL ] );
				}
			}
	
			// Set the correct header, if data is being sent
			if ( s.data && s.hasContent && s.contentType !== false || options.contentType ) {
				jqXHR.setRequestHeader( "Content-Type", s.contentType );
			}
	
			// Set the Accepts header for the server, depending on the dataType
			jqXHR.setRequestHeader(
				"Accept",
				s.dataTypes[ 0 ] && s.accepts[ s.dataTypes[ 0 ] ] ?
					s.accepts[ s.dataTypes[ 0 ] ] +
						( s.dataTypes[ 0 ] !== "*" ? ", " + allTypes + "; q=0.01" : "" ) :
					s.accepts[ "*" ]
			);
	
			// Check for headers option
			for ( i in s.headers ) {
				jqXHR.setRequestHeader( i, s.headers[ i ] );
			}
	
			// Allow custom headers/mimetypes and early abort
			if ( s.beforeSend &&
				( s.beforeSend.call( callbackContext, jqXHR, s ) === false || state === 2 ) ) {
	
				// Abort if not done already and return
				return jqXHR.abort();
			}
	
			// Aborting is no longer a cancellation
			strAbort = "abort";
	
			// Install callbacks on deferreds
			for ( i in { success: 1, error: 1, complete: 1 } ) {
				jqXHR[ i ]( s[ i ] );
			}
	
			// Get transport
			transport = inspectPrefiltersOrTransports( transports, s, options, jqXHR );
	
			// If no transport, we auto-abort
			if ( !transport ) {
				done( -1, "No Transport" );
			} else {
				jqXHR.readyState = 1;
	
				// Send global event
				if ( fireGlobals ) {
					globalEventContext.trigger( "ajaxSend", [ jqXHR, s ] );
				}
	
				// If request was aborted inside ajaxSend, stop there
				if ( state === 2 ) {
					return jqXHR;
				}
	
				// Timeout
				if ( s.async && s.timeout > 0 ) {
					timeoutTimer = window.setTimeout( function() {
						jqXHR.abort( "timeout" );
					}, s.timeout );
				}
	
				try {
					state = 1;
					transport.send( requestHeaders, done );
				} catch ( e ) {
	
					// Propagate exception as error if not done
					if ( state < 2 ) {
						done( -1, e );
	
					// Simply rethrow otherwise
					} else {
						throw e;
					}
				}
			}
	
			// Callback for when everything is done
			function done( status, nativeStatusText, responses, headers ) {
				var isSuccess, success, error, response, modified,
					statusText = nativeStatusText;
	
				// Called once
				if ( state === 2 ) {
					return;
				}
	
				// State is "done" now
				state = 2;
	
				// Clear timeout if it exists
				if ( timeoutTimer ) {
					window.clearTimeout( timeoutTimer );
				}
	
				// Dereference transport for early garbage collection
				// (no matter how long the jqXHR object will be used)
				transport = undefined;
	
				// Cache response headers
				responseHeadersString = headers || "";
	
				// Set readyState
				jqXHR.readyState = status > 0 ? 4 : 0;
	
				// Determine if successful
				isSuccess = status >= 200 && status < 300 || status === 304;
	
				// Get response data
				if ( responses ) {
					response = ajaxHandleResponses( s, jqXHR, responses );
				}
	
				// Convert no matter what (that way responseXXX fields are always set)
				response = ajaxConvert( s, response, jqXHR, isSuccess );
	
				// If successful, handle type chaining
				if ( isSuccess ) {
	
					// Set the If-Modified-Since and/or If-None-Match header, if in ifModified mode.
					if ( s.ifModified ) {
						modified = jqXHR.getResponseHeader( "Last-Modified" );
						if ( modified ) {
							jQuery.lastModified[ cacheURL ] = modified;
						}
						modified = jqXHR.getResponseHeader( "etag" );
						if ( modified ) {
							jQuery.etag[ cacheURL ] = modified;
						}
					}
	
					// if no content
					if ( status === 204 || s.type === "HEAD" ) {
						statusText = "nocontent";
	
					// if not modified
					} else if ( status === 304 ) {
						statusText = "notmodified";
	
					// If we have data, let's convert it
					} else {
						statusText = response.state;
						success = response.data;
						error = response.error;
						isSuccess = !error;
					}
				} else {
	
					// Extract error from statusText and normalize for non-aborts
					error = statusText;
					if ( status || !statusText ) {
						statusText = "error";
						if ( status < 0 ) {
							status = 0;
						}
					}
				}
	
				// Set data for the fake xhr object
				jqXHR.status = status;
				jqXHR.statusText = ( nativeStatusText || statusText ) + "";
	
				// Success/Error
				if ( isSuccess ) {
					deferred.resolveWith( callbackContext, [ success, statusText, jqXHR ] );
				} else {
					deferred.rejectWith( callbackContext, [ jqXHR, statusText, error ] );
				}
	
				// Status-dependent callbacks
				jqXHR.statusCode( statusCode );
				statusCode = undefined;
	
				if ( fireGlobals ) {
					globalEventContext.trigger( isSuccess ? "ajaxSuccess" : "ajaxError",
						[ jqXHR, s, isSuccess ? success : error ] );
				}
	
				// Complete
				completeDeferred.fireWith( callbackContext, [ jqXHR, statusText ] );
	
				if ( fireGlobals ) {
					globalEventContext.trigger( "ajaxComplete", [ jqXHR, s ] );
	
					// Handle the global AJAX counter
					if ( !( --jQuery.active ) ) {
						jQuery.event.trigger( "ajaxStop" );
					}
				}
			}
	
			return jqXHR;
		},
	
		getJSON: function( url, data, callback ) {
			return jQuery.get( url, data, callback, "json" );
		},
	
		getScript: function( url, callback ) {
			return jQuery.get( url, undefined, callback, "script" );
		}
	} );
	
	jQuery.each( [ "get", "post" ], function( i, method ) {
		jQuery[ method ] = function( url, data, callback, type ) {
	
			// Shift arguments if data argument was omitted
			if ( jQuery.isFunction( data ) ) {
				type = type || callback;
				callback = data;
				data = undefined;
			}
	
			// The url can be an options object (which then must have .url)
			return jQuery.ajax( jQuery.extend( {
				url: url,
				type: method,
				dataType: type,
				data: data,
				success: callback
			}, jQuery.isPlainObject( url ) && url ) );
		};
	} );
	
	
	jQuery._evalUrl = function( url ) {
		return jQuery.ajax( {
			url: url,
	
			// Make this explicit, since user can override this through ajaxSetup (#11264)
			type: "GET",
			dataType: "script",
			async: false,
			global: false,
			"throws": true
		} );
	};
	
	
	jQuery.fn.extend( {
		wrapAll: function( html ) {
			var wrap;
	
			if ( jQuery.isFunction( html ) ) {
				return this.each( function( i ) {
					jQuery( this ).wrapAll( html.call( this, i ) );
				} );
			}
	
			if ( this[ 0 ] ) {
	
				// The elements to wrap the target around
				wrap = jQuery( html, this[ 0 ].ownerDocument ).eq( 0 ).clone( true );
	
				if ( this[ 0 ].parentNode ) {
					wrap.insertBefore( this[ 0 ] );
				}
	
				wrap.map( function() {
					var elem = this;
	
					while ( elem.firstElementChild ) {
						elem = elem.firstElementChild;
					}
	
					return elem;
				} ).append( this );
			}
	
			return this;
		},
	
		wrapInner: function( html ) {
			if ( jQuery.isFunction( html ) ) {
				return this.each( function( i ) {
					jQuery( this ).wrapInner( html.call( this, i ) );
				} );
			}
	
			return this.each( function() {
				var self = jQuery( this ),
					contents = self.contents();
	
				if ( contents.length ) {
					contents.wrapAll( html );
	
				} else {
					self.append( html );
				}
			} );
		},
	
		wrap: function( html ) {
			var isFunction = jQuery.isFunction( html );
	
			return this.each( function( i ) {
				jQuery( this ).wrapAll( isFunction ? html.call( this, i ) : html );
			} );
		},
	
		unwrap: function() {
			return this.parent().each( function() {
				if ( !jQuery.nodeName( this, "body" ) ) {
					jQuery( this ).replaceWith( this.childNodes );
				}
			} ).end();
		}
	} );
	
	
	jQuery.expr.filters.hidden = function( elem ) {
		return !jQuery.expr.filters.visible( elem );
	};
	jQuery.expr.filters.visible = function( elem ) {
	
		// Support: Opera <= 12.12
		// Opera reports offsetWidths and offsetHeights less than zero on some elements
		// Use OR instead of AND as the element is not visible if either is true
		// See tickets #10406 and #13132
		return elem.offsetWidth > 0 || elem.offsetHeight > 0 || elem.getClientRects().length > 0;
	};
	
	
	
	
	var r20 = /%20/g,
		rbracket = /\[\]$/,
		rCRLF = /\r?\n/g,
		rsubmitterTypes = /^(?:submit|button|image|reset|file)$/i,
		rsubmittable = /^(?:input|select|textarea|keygen)/i;
	
	function buildParams( prefix, obj, traditional, add ) {
		var name;
	
		if ( jQuery.isArray( obj ) ) {
	
			// Serialize array item.
			jQuery.each( obj, function( i, v ) {
				if ( traditional || rbracket.test( prefix ) ) {
	
					// Treat each array item as a scalar.
					add( prefix, v );
	
				} else {
	
					// Item is non-scalar (array or object), encode its numeric index.
					buildParams(
						prefix + "[" + ( typeof v === "object" && v != null ? i : "" ) + "]",
						v,
						traditional,
						add
					);
				}
			} );
	
		} else if ( !traditional && jQuery.type( obj ) === "object" ) {
	
			// Serialize object item.
			for ( name in obj ) {
				buildParams( prefix + "[" + name + "]", obj[ name ], traditional, add );
			}
	
		} else {
	
			// Serialize scalar item.
			add( prefix, obj );
		}
	}
	
	// Serialize an array of form elements or a set of
	// key/values into a query string
	jQuery.param = function( a, traditional ) {
		var prefix,
			s = [],
			add = function( key, value ) {
	
				// If value is a function, invoke it and return its value
				value = jQuery.isFunction( value ) ? value() : ( value == null ? "" : value );
				s[ s.length ] = encodeURIComponent( key ) + "=" + encodeURIComponent( value );
			};
	
		// Set traditional to true for jQuery <= 1.3.2 behavior.
		if ( traditional === undefined ) {
			traditional = jQuery.ajaxSettings && jQuery.ajaxSettings.traditional;
		}
	
		// If an array was passed in, assume that it is an array of form elements.
		if ( jQuery.isArray( a ) || ( a.jquery && !jQuery.isPlainObject( a ) ) ) {
	
			// Serialize the form elements
			jQuery.each( a, function() {
				add( this.name, this.value );
			} );
	
		} else {
	
			// If traditional, encode the "old" way (the way 1.3.2 or older
			// did it), otherwise encode params recursively.
			for ( prefix in a ) {
				buildParams( prefix, a[ prefix ], traditional, add );
			}
		}
	
		// Return the resulting serialization
		return s.join( "&" ).replace( r20, "+" );
	};
	
	jQuery.fn.extend( {
		serialize: function() {
			return jQuery.param( this.serializeArray() );
		},
		serializeArray: function() {
			return this.map( function() {
	
				// Can add propHook for "elements" to filter or add form elements
				var elements = jQuery.prop( this, "elements" );
				return elements ? jQuery.makeArray( elements ) : this;
			} )
			.filter( function() {
				var type = this.type;
	
				// Use .is( ":disabled" ) so that fieldset[disabled] works
				return this.name && !jQuery( this ).is( ":disabled" ) &&
					rsubmittable.test( this.nodeName ) && !rsubmitterTypes.test( type ) &&
					( this.checked || !rcheckableType.test( type ) );
			} )
			.map( function( i, elem ) {
				var val = jQuery( this ).val();
	
				return val == null ?
					null :
					jQuery.isArray( val ) ?
						jQuery.map( val, function( val ) {
							return { name: elem.name, value: val.replace( rCRLF, "\r\n" ) };
						} ) :
						{ name: elem.name, value: val.replace( rCRLF, "\r\n" ) };
			} ).get();
		}
	} );
	
	
	jQuery.ajaxSettings.xhr = function() {
		try {
			return new window.XMLHttpRequest();
		} catch ( e ) {}
	};
	
	var xhrSuccessStatus = {
	
			// File protocol always yields status code 0, assume 200
			0: 200,
	
			// Support: IE9
			// #1450: sometimes IE returns 1223 when it should be 204
			1223: 204
		},
		xhrSupported = jQuery.ajaxSettings.xhr();
	
	support.cors = !!xhrSupported && ( "withCredentials" in xhrSupported );
	support.ajax = xhrSupported = !!xhrSupported;
	
	jQuery.ajaxTransport( function( options ) {
		var callback, errorCallback;
	
		// Cross domain only allowed if supported through XMLHttpRequest
		if ( support.cors || xhrSupported && !options.crossDomain ) {
			return {
				send: function( headers, complete ) {
					var i,
						xhr = options.xhr();
	
					xhr.open(
						options.type,
						options.url,
						options.async,
						options.username,
						options.password
					);
	
					// Apply custom fields if provided
					if ( options.xhrFields ) {
						for ( i in options.xhrFields ) {
							xhr[ i ] = options.xhrFields[ i ];
						}
					}
	
					// Override mime type if needed
					if ( options.mimeType && xhr.overrideMimeType ) {
						xhr.overrideMimeType( options.mimeType );
					}
	
					// X-Requested-With header
					// For cross-domain requests, seeing as conditions for a preflight are
					// akin to a jigsaw puzzle, we simply never set it to be sure.
					// (it can always be set on a per-request basis or even using ajaxSetup)
					// For same-domain requests, won't change header if already provided.
					if ( !options.crossDomain && !headers[ "X-Requested-With" ] ) {
						headers[ "X-Requested-With" ] = "XMLHttpRequest";
					}
	
					// Set headers
					for ( i in headers ) {
						xhr.setRequestHeader( i, headers[ i ] );
					}
	
					// Callback
					callback = function( type ) {
						return function() {
							if ( callback ) {
								callback = errorCallback = xhr.onload =
									xhr.onerror = xhr.onabort = xhr.onreadystatechange = null;
	
								if ( type === "abort" ) {
									xhr.abort();
								} else if ( type === "error" ) {
	
									// Support: IE9
									// On a manual native abort, IE9 throws
									// errors on any property access that is not readyState
									if ( typeof xhr.status !== "number" ) {
										complete( 0, "error" );
									} else {
										complete(
	
											// File: protocol always yields status 0; see #8605, #14207
											xhr.status,
											xhr.statusText
										);
									}
								} else {
									complete(
										xhrSuccessStatus[ xhr.status ] || xhr.status,
										xhr.statusText,
	
										// Support: IE9 only
										// IE9 has no XHR2 but throws on binary (trac-11426)
										// For XHR2 non-text, let the caller handle it (gh-2498)
										( xhr.responseType || "text" ) !== "text"  ||
										typeof xhr.responseText !== "string" ?
											{ binary: xhr.response } :
											{ text: xhr.responseText },
										xhr.getAllResponseHeaders()
									);
								}
							}
						};
					};
	
					// Listen to events
					xhr.onload = callback();
					errorCallback = xhr.onerror = callback( "error" );
	
					// Support: IE9
					// Use onreadystatechange to replace onabort
					// to handle uncaught aborts
					if ( xhr.onabort !== undefined ) {
						xhr.onabort = errorCallback;
					} else {
						xhr.onreadystatechange = function() {
	
							// Check readyState before timeout as it changes
							if ( xhr.readyState === 4 ) {
	
								// Allow onerror to be called first,
								// but that will not handle a native abort
								// Also, save errorCallback to a variable
								// as xhr.onerror cannot be accessed
								window.setTimeout( function() {
									if ( callback ) {
										errorCallback();
									}
								} );
							}
						};
					}
	
					// Create the abort callback
					callback = callback( "abort" );
	
					try {
	
						// Do send the request (this may raise an exception)
						xhr.send( options.hasContent && options.data || null );
					} catch ( e ) {
	
						// #14683: Only rethrow if this hasn't been notified as an error yet
						if ( callback ) {
							throw e;
						}
					}
				},
	
				abort: function() {
					if ( callback ) {
						callback();
					}
				}
			};
		}
	} );
	
	
	
	
	// Install script dataType
	jQuery.ajaxSetup( {
		accepts: {
			script: "text/javascript, application/javascript, " +
				"application/ecmascript, application/x-ecmascript"
		},
		contents: {
			script: /\b(?:java|ecma)script\b/
		},
		converters: {
			"text script": function( text ) {
				jQuery.globalEval( text );
				return text;
			}
		}
	} );
	
	// Handle cache's special case and crossDomain
	jQuery.ajaxPrefilter( "script", function( s ) {
		if ( s.cache === undefined ) {
			s.cache = false;
		}
		if ( s.crossDomain ) {
			s.type = "GET";
		}
	} );
	
	// Bind script tag hack transport
	jQuery.ajaxTransport( "script", function( s ) {
	
		// This transport only deals with cross domain requests
		if ( s.crossDomain ) {
			var script, callback;
			return {
				send: function( _, complete ) {
					script = jQuery( "<script>" ).prop( {
						charset: s.scriptCharset,
						src: s.url
					} ).on(
						"load error",
						callback = function( evt ) {
							script.remove();
							callback = null;
							if ( evt ) {
								complete( evt.type === "error" ? 404 : 200, evt.type );
							}
						}
					);
	
					// Use native DOM manipulation to avoid our domManip AJAX trickery
					document.head.appendChild( script[ 0 ] );
				},
				abort: function() {
					if ( callback ) {
						callback();
					}
				}
			};
		}
	} );
	
	
	
	
	var oldCallbacks = [],
		rjsonp = /(=)\?(?=&|$)|\?\?/;
	
	// Default jsonp settings
	jQuery.ajaxSetup( {
		jsonp: "callback",
		jsonpCallback: function() {
			var callback = oldCallbacks.pop() || ( jQuery.expando + "_" + ( nonce++ ) );
			this[ callback ] = true;
			return callback;
		}
	} );
	
	// Detect, normalize options and install callbacks for jsonp requests
	jQuery.ajaxPrefilter( "json jsonp", function( s, originalSettings, jqXHR ) {
	
		var callbackName, overwritten, responseContainer,
			jsonProp = s.jsonp !== false && ( rjsonp.test( s.url ) ?
				"url" :
				typeof s.data === "string" &&
					( s.contentType || "" )
						.indexOf( "application/x-www-form-urlencoded" ) === 0 &&
					rjsonp.test( s.data ) && "data"
			);
	
		// Handle iff the expected data type is "jsonp" or we have a parameter to set
		if ( jsonProp || s.dataTypes[ 0 ] === "jsonp" ) {
	
			// Get callback name, remembering preexisting value associated with it
			callbackName = s.jsonpCallback = jQuery.isFunction( s.jsonpCallback ) ?
				s.jsonpCallback() :
				s.jsonpCallback;
	
			// Insert callback into url or form data
			if ( jsonProp ) {
				s[ jsonProp ] = s[ jsonProp ].replace( rjsonp, "$1" + callbackName );
			} else if ( s.jsonp !== false ) {
				s.url += ( rquery.test( s.url ) ? "&" : "?" ) + s.jsonp + "=" + callbackName;
			}
	
			// Use data converter to retrieve json after script execution
			s.converters[ "script json" ] = function() {
				if ( !responseContainer ) {
					jQuery.error( callbackName + " was not called" );
				}
				return responseContainer[ 0 ];
			};
	
			// Force json dataType
			s.dataTypes[ 0 ] = "json";
	
			// Install callback
			overwritten = window[ callbackName ];
			window[ callbackName ] = function() {
				responseContainer = arguments;
			};
	
			// Clean-up function (fires after converters)
			jqXHR.always( function() {
	
				// If previous value didn't exist - remove it
				if ( overwritten === undefined ) {
					jQuery( window ).removeProp( callbackName );
	
				// Otherwise restore preexisting value
				} else {
					window[ callbackName ] = overwritten;
				}
	
				// Save back as free
				if ( s[ callbackName ] ) {
	
					// Make sure that re-using the options doesn't screw things around
					s.jsonpCallback = originalSettings.jsonpCallback;
	
					// Save the callback name for future use
					oldCallbacks.push( callbackName );
				}
	
				// Call if it was a function and we have a response
				if ( responseContainer && jQuery.isFunction( overwritten ) ) {
					overwritten( responseContainer[ 0 ] );
				}
	
				responseContainer = overwritten = undefined;
			} );
	
			// Delegate to script
			return "script";
		}
	} );
	
	
	
	
	// Support: Safari 8+
	// In Safari 8 documents created via document.implementation.createHTMLDocument
	// collapse sibling forms: the second one becomes a child of the first one.
	// Because of that, this security measure has to be disabled in Safari 8.
	// https://bugs.webkit.org/show_bug.cgi?id=137337
	support.createHTMLDocument = ( function() {
		var body = document.implementation.createHTMLDocument( "" ).body;
		body.innerHTML = "<form></form><form></form>";
		return body.childNodes.length === 2;
	} )();
	
	
	// Argument "data" should be string of html
	// context (optional): If specified, the fragment will be created in this context,
	// defaults to document
	// keepScripts (optional): If true, will include scripts passed in the html string
	jQuery.parseHTML = function( data, context, keepScripts ) {
		if ( !data || typeof data !== "string" ) {
			return null;
		}
		if ( typeof context === "boolean" ) {
			keepScripts = context;
			context = false;
		}
	
		// Stop scripts or inline event handlers from being executed immediately
		// by using document.implementation
		context = context || ( support.createHTMLDocument ?
			document.implementation.createHTMLDocument( "" ) :
			document );
	
		var parsed = rsingleTag.exec( data ),
			scripts = !keepScripts && [];
	
		// Single tag
		if ( parsed ) {
			return [ context.createElement( parsed[ 1 ] ) ];
		}
	
		parsed = buildFragment( [ data ], context, scripts );
	
		if ( scripts && scripts.length ) {
			jQuery( scripts ).remove();
		}
	
		return jQuery.merge( [], parsed.childNodes );
	};
	
	
	// Keep a copy of the old load method
	var _load = jQuery.fn.load;
	
	/**
	 * Load a url into a page
	 */
	jQuery.fn.load = function( url, params, callback ) {
		if ( typeof url !== "string" && _load ) {
			return _load.apply( this, arguments );
		}
	
		var selector, type, response,
			self = this,
			off = url.indexOf( " " );
	
		if ( off > -1 ) {
			selector = jQuery.trim( url.slice( off ) );
			url = url.slice( 0, off );
		}
	
		// If it's a function
		if ( jQuery.isFunction( params ) ) {
	
			// We assume that it's the callback
			callback = params;
			params = undefined;
	
		// Otherwise, build a param string
		} else if ( params && typeof params === "object" ) {
			type = "POST";
		}
	
		// If we have elements to modify, make the request
		if ( self.length > 0 ) {
			jQuery.ajax( {
				url: url,
	
				// If "type" variable is undefined, then "GET" method will be used.
				// Make value of this field explicit since
				// user can override it through ajaxSetup method
				type: type || "GET",
				dataType: "html",
				data: params
			} ).done( function( responseText ) {
	
				// Save response for use in complete callback
				response = arguments;
	
				self.html( selector ?
	
					// If a selector was specified, locate the right elements in a dummy div
					// Exclude scripts to avoid IE 'Permission Denied' errors
					jQuery( "<div>" ).append( jQuery.parseHTML( responseText ) ).find( selector ) :
	
					// Otherwise use the full result
					responseText );
	
			// If the request succeeds, this function gets "data", "status", "jqXHR"
			// but they are ignored because response was set above.
			// If it fails, this function gets "jqXHR", "status", "error"
			} ).always( callback && function( jqXHR, status ) {
				self.each( function() {
					callback.apply( self, response || [ jqXHR.responseText, status, jqXHR ] );
				} );
			} );
		}
	
		return this;
	};
	
	
	
	
	// Attach a bunch of functions for handling common AJAX events
	jQuery.each( [
		"ajaxStart",
		"ajaxStop",
		"ajaxComplete",
		"ajaxError",
		"ajaxSuccess",
		"ajaxSend"
	], function( i, type ) {
		jQuery.fn[ type ] = function( fn ) {
			return this.on( type, fn );
		};
	} );
	
	
	
	
	jQuery.expr.filters.animated = function( elem ) {
		return jQuery.grep( jQuery.timers, function( fn ) {
			return elem === fn.elem;
		} ).length;
	};
	
	
	
	
	/**
	 * Gets a window from an element
	 */
	function getWindow( elem ) {
		return jQuery.isWindow( elem ) ? elem : elem.nodeType === 9 && elem.defaultView;
	}
	
	jQuery.offset = {
		setOffset: function( elem, options, i ) {
			var curPosition, curLeft, curCSSTop, curTop, curOffset, curCSSLeft, calculatePosition,
				position = jQuery.css( elem, "position" ),
				curElem = jQuery( elem ),
				props = {};
	
			// Set position first, in-case top/left are set even on static elem
			if ( position === "static" ) {
				elem.style.position = "relative";
			}
	
			curOffset = curElem.offset();
			curCSSTop = jQuery.css( elem, "top" );
			curCSSLeft = jQuery.css( elem, "left" );
			calculatePosition = ( position === "absolute" || position === "fixed" ) &&
				( curCSSTop + curCSSLeft ).indexOf( "auto" ) > -1;
	
			// Need to be able to calculate position if either
			// top or left is auto and position is either absolute or fixed
			if ( calculatePosition ) {
				curPosition = curElem.position();
				curTop = curPosition.top;
				curLeft = curPosition.left;
	
			} else {
				curTop = parseFloat( curCSSTop ) || 0;
				curLeft = parseFloat( curCSSLeft ) || 0;
			}
	
			if ( jQuery.isFunction( options ) ) {
	
				// Use jQuery.extend here to allow modification of coordinates argument (gh-1848)
				options = options.call( elem, i, jQuery.extend( {}, curOffset ) );
			}
	
			if ( options.top != null ) {
				props.top = ( options.top - curOffset.top ) + curTop;
			}
			if ( options.left != null ) {
				props.left = ( options.left - curOffset.left ) + curLeft;
			}
	
			if ( "using" in options ) {
				options.using.call( elem, props );
	
			} else {
				curElem.css( props );
			}
		}
	};
	
	jQuery.fn.extend( {
		offset: function( options ) {
			if ( arguments.length ) {
				return options === undefined ?
					this :
					this.each( function( i ) {
						jQuery.offset.setOffset( this, options, i );
					} );
			}
	
			var docElem, win,
				elem = this[ 0 ],
				box = { top: 0, left: 0 },
				doc = elem && elem.ownerDocument;
	
			if ( !doc ) {
				return;
			}
	
			docElem = doc.documentElement;
	
			// Make sure it's not a disconnected DOM node
			if ( !jQuery.contains( docElem, elem ) ) {
				return box;
			}
	
			box = elem.getBoundingClientRect();
			win = getWindow( doc );
			return {
				top: box.top + win.pageYOffset - docElem.clientTop,
				left: box.left + win.pageXOffset - docElem.clientLeft
			};
		},
	
		position: function() {
			if ( !this[ 0 ] ) {
				return;
			}
	
			var offsetParent, offset,
				elem = this[ 0 ],
				parentOffset = { top: 0, left: 0 };
	
			// Fixed elements are offset from window (parentOffset = {top:0, left: 0},
			// because it is its only offset parent
			if ( jQuery.css( elem, "position" ) === "fixed" ) {
	
				// Assume getBoundingClientRect is there when computed position is fixed
				offset = elem.getBoundingClientRect();
	
			} else {
	
				// Get *real* offsetParent
				offsetParent = this.offsetParent();
	
				// Get correct offsets
				offset = this.offset();
				if ( !jQuery.nodeName( offsetParent[ 0 ], "html" ) ) {
					parentOffset = offsetParent.offset();
				}
	
				// Add offsetParent borders
				parentOffset.top += jQuery.css( offsetParent[ 0 ], "borderTopWidth", true );
				parentOffset.left += jQuery.css( offsetParent[ 0 ], "borderLeftWidth", true );
			}
	
			// Subtract parent offsets and element margins
			return {
				top: offset.top - parentOffset.top - jQuery.css( elem, "marginTop", true ),
				left: offset.left - parentOffset.left - jQuery.css( elem, "marginLeft", true )
			};
		},
	
		// This method will return documentElement in the following cases:
		// 1) For the element inside the iframe without offsetParent, this method will return
		//    documentElement of the parent window
		// 2) For the hidden or detached element
		// 3) For body or html element, i.e. in case of the html node - it will return itself
		//
		// but those exceptions were never presented as a real life use-cases
		// and might be considered as more preferable results.
		//
		// This logic, however, is not guaranteed and can change at any point in the future
		offsetParent: function() {
			return this.map( function() {
				var offsetParent = this.offsetParent;
	
				while ( offsetParent && jQuery.css( offsetParent, "position" ) === "static" ) {
					offsetParent = offsetParent.offsetParent;
				}
	
				return offsetParent || documentElement;
			} );
		}
	} );
	
	// Create scrollLeft and scrollTop methods
	jQuery.each( { scrollLeft: "pageXOffset", scrollTop: "pageYOffset" }, function( method, prop ) {
		var top = "pageYOffset" === prop;
	
		jQuery.fn[ method ] = function( val ) {
			return access( this, function( elem, method, val ) {
				var win = getWindow( elem );
	
				if ( val === undefined ) {
					return win ? win[ prop ] : elem[ method ];
				}
	
				if ( win ) {
					win.scrollTo(
						!top ? val : win.pageXOffset,
						top ? val : win.pageYOffset
					);
	
				} else {
					elem[ method ] = val;
				}
			}, method, val, arguments.length );
		};
	} );
	
	// Support: Safari<7-8+, Chrome<37-44+
	// Add the top/left cssHooks using jQuery.fn.position
	// Webkit bug: https://bugs.webkit.org/show_bug.cgi?id=29084
	// Blink bug: https://code.google.com/p/chromium/issues/detail?id=229280
	// getComputedStyle returns percent when specified for top/left/bottom/right;
	// rather than make the css module depend on the offset module, just check for it here
	jQuery.each( [ "top", "left" ], function( i, prop ) {
		jQuery.cssHooks[ prop ] = addGetHookIf( support.pixelPosition,
			function( elem, computed ) {
				if ( computed ) {
					computed = curCSS( elem, prop );
	
					// If curCSS returns percentage, fallback to offset
					return rnumnonpx.test( computed ) ?
						jQuery( elem ).position()[ prop ] + "px" :
						computed;
				}
			}
		);
	} );
	
	
	// Create innerHeight, innerWidth, height, width, outerHeight and outerWidth methods
	jQuery.each( { Height: "height", Width: "width" }, function( name, type ) {
		jQuery.each( { padding: "inner" + name, content: type, "": "outer" + name },
			function( defaultExtra, funcName ) {
	
			// Margin is only for outerHeight, outerWidth
			jQuery.fn[ funcName ] = function( margin, value ) {
				var chainable = arguments.length && ( defaultExtra || typeof margin !== "boolean" ),
					extra = defaultExtra || ( margin === true || value === true ? "margin" : "border" );
	
				return access( this, function( elem, type, value ) {
					var doc;
	
					if ( jQuery.isWindow( elem ) ) {
	
						// As of 5/8/2012 this will yield incorrect results for Mobile Safari, but there
						// isn't a whole lot we can do. See pull request at this URL for discussion:
						// https://github.com/jquery/jquery/pull/764
						return elem.document.documentElement[ "client" + name ];
					}
	
					// Get document width or height
					if ( elem.nodeType === 9 ) {
						doc = elem.documentElement;
	
						// Either scroll[Width/Height] or offset[Width/Height] or client[Width/Height],
						// whichever is greatest
						return Math.max(
							elem.body[ "scroll" + name ], doc[ "scroll" + name ],
							elem.body[ "offset" + name ], doc[ "offset" + name ],
							doc[ "client" + name ]
						);
					}
	
					return value === undefined ?
	
						// Get width or height on the element, requesting but not forcing parseFloat
						jQuery.css( elem, type, extra ) :
	
						// Set width or height on the element
						jQuery.style( elem, type, value, extra );
				}, type, chainable ? margin : undefined, chainable, null );
			};
		} );
	} );
	
	
	jQuery.fn.extend( {
	
		bind: function( types, data, fn ) {
			return this.on( types, null, data, fn );
		},
		unbind: function( types, fn ) {
			return this.off( types, null, fn );
		},
	
		delegate: function( selector, types, data, fn ) {
			return this.on( types, selector, data, fn );
		},
		undelegate: function( selector, types, fn ) {
	
			// ( namespace ) or ( selector, types [, fn] )
			return arguments.length === 1 ?
				this.off( selector, "**" ) :
				this.off( types, selector || "**", fn );
		},
		size: function() {
			return this.length;
		}
	} );
	
	jQuery.fn.andSelf = jQuery.fn.addBack;
	
	
	
	
	// Register as a named AMD module, since jQuery can be concatenated with other
	// files that may use define, but not via a proper concatenation script that
	// understands anonymous AMD modules. A named AMD is safest and most robust
	// way to register. Lowercase jquery is used because AMD module names are
	// derived from file names, and jQuery is normally delivered in a lowercase
	// file name. Do this after creating the global so that if an AMD module wants
	// to call noConflict to hide this version of jQuery, it will work.
	
	// Note that for maximum portability, libraries that are not jQuery should
	// declare themselves as anonymous modules, and avoid setting a global if an
	// AMD loader is present. jQuery is a special case. For more information, see
	// https://github.com/jrburke/requirejs/wiki/Updating-existing-libraries#wiki-anon
	
	if ( true ) {
		!(__WEBPACK_AMD_DEFINE_ARRAY__ = [], __WEBPACK_AMD_DEFINE_RESULT__ = function() {
			return jQuery;
		}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
	}
	
	
	
	var
	
		// Map over jQuery in case of overwrite
		_jQuery = window.jQuery,
	
		// Map over the $ in case of overwrite
		_$ = window.$;
	
	jQuery.noConflict = function( deep ) {
		if ( window.$ === jQuery ) {
			window.$ = _$;
		}
	
		if ( deep && window.jQuery === jQuery ) {
			window.jQuery = _jQuery;
		}
	
		return jQuery;
	};
	
	// Expose jQuery and $ identifiers, even in AMD
	// (#7102#comment:10, https://github.com/jquery/jquery/pull/557)
	// and CommonJS for browser emulators (#13566)
	if ( !noGlobal ) {
		window.jQuery = window.$ = jQuery;
	}
	
	return jQuery;
	}));


/***/ },
/* 3 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function(jQuery) {'use strict';
	
	var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol ? "symbol" : typeof obj; };
	
	/**
	* autoNumeric.js
	* @author: Bob Knothe
	* @author: Sokolov Yura
	* @version: 1.9.26 - 2014-10-07 GMT 2:00 PM
	*
	* Created by Robert J. Knothe on 2010-10-25. Please report any bugs to https://github.com/BobKnothe/autoNumeric
	* Created by Sokolov Yura on 2010-11-07
	*
	* Copyright (c) 2011 Robert J. Knothe http://www.decorplanit.com/plugin/
	*
	* The MIT License (http://www.opensource.org/licenses/mit-license.php)
	*
	* Permission is hereby granted, free of charge, to any person
	* obtaining a copy of this software and associated documentation
	* files (the "Software"), to deal in the Software without
	* restriction, including without limitation the rights to use,
	* copy, modify, merge, publish, distribute, sublicense, and/or sell
	* copies of the Software, and to permit persons to whom the
	* Software is furnished to do so, subject to the following
	* conditions:
	*
	* The above copyright notice and this permission notice shall be
	* included in all copies or substantial portions of the Software.
	*
	* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
	* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
	* OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
	* NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
	* HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
	* WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
	* FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
	* OTHER DEALINGS IN THE SOFTWARE.
	*/
	(function ($) {
	    "use strict";
	    /*jslint browser: true*/
	    /*global jQuery: false*/
	    /* Cross browser routine for getting selected range/cursor position
	     */
	
	    function getElementSelection(that) {
	        var position = {};
	        if (that.selectionStart === undefined) {
	            that.focus();
	            var select = document.selection.createRange();
	            position.length = select.text.length;
	            select.moveStart('character', -that.value.length);
	            position.end = select.text.length;
	            position.start = position.end - position.length;
	        } else {
	            position.start = that.selectionStart;
	            position.end = that.selectionEnd;
	            position.length = position.end - position.start;
	        }
	        return position;
	    }
	    /**
	     * Cross browser routine for setting selected range/cursor position
	     */
	    function setElementSelection(that, start, end) {
	        if (that.selectionStart === undefined) {
	            that.focus();
	            var r = that.createTextRange();
	            r.collapse(true);
	            r.moveEnd('character', end);
	            r.moveStart('character', start);
	            r.select();
	        } else {
	            that.selectionStart = start;
	            that.selectionEnd = end;
	        }
	    }
	    /**
	     * run callbacks in parameters if any
	     * any parameter could be a callback:
	     * - a function, which invoked with jQuery element, parameters and this parameter name and returns parameter value
	     * - a name of function, attached to $(selector).autoNumeric.functionName(){} - which was called previously
	     */
	    function runCallbacks($this, settings) {
	        /**
	         * loops through the settings object (option array) to find the following
	         * k = option name example k=aNum
	         * val = option value example val=0123456789
	         */
	        $.each(settings, function (k, val) {
	            if (typeof val === 'function') {
	                settings[k] = val($this, settings, k);
	            } else if (typeof $this.autoNumeric[val] === 'function') {
	                /**
	                 * calls the attached function from the html5 data example: data-a-sign="functionName"
	                 */
	                settings[k] = $this.autoNumeric[val]($this, settings, k);
	            }
	        });
	    }
	    function convertKeyToNumber(settings, key) {
	        if (typeof settings[key] === 'string') {
	            settings[key] *= 1;
	        }
	    }
	    /**
	     * Preparing user defined options for further usage
	     * merge them with defaults appropriately
	     */
	    function autoCode($this, settings) {
	        runCallbacks($this, settings);
	        settings.oEvent = null;
	        settings.tagList = ['b', 'caption', 'cite', 'code', 'dd', 'del', 'div', 'dfn', 'dt', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ins', 'kdb', 'label', 'li', 'output', 'p', 'q', 's', 'sample', 'span', 'strong', 'td', 'th', 'u', 'var'];
	        var vmax = settings.vMax.toString().split('.'),
	            vmin = !settings.vMin && settings.vMin !== 0 ? [] : settings.vMin.toString().split('.');
	        convertKeyToNumber(settings, 'vMax');
	        convertKeyToNumber(settings, 'vMin');
	        convertKeyToNumber(settings, 'mDec'); /** set mDec if not defined by user */
	        settings.mDec = settings.mRound === 'CHF' ? '2' : settings.mDec;
	        settings.allowLeading = true;
	        settings.aNeg = settings.vMin < 0 ? '-' : '';
	        vmax[0] = vmax[0].replace('-', '');
	        vmin[0] = vmin[0].replace('-', '');
	        settings.mInt = Math.max(vmax[0].length, vmin[0].length, 1);
	        if (settings.mDec === null) {
	            var vmaxLength = 0,
	                vminLength = 0;
	            if (vmax[1]) {
	                vmaxLength = vmax[1].length;
	            }
	            if (vmin[1]) {
	                vminLength = vmin[1].length;
	            }
	            settings.mDec = Math.max(vmaxLength, vminLength);
	        } /** set alternative decimal separator key */
	        if (settings.altDec === null && settings.mDec > 0) {
	            if (settings.aDec === '.' && settings.aSep !== ',') {
	                settings.altDec = ',';
	            } else if (settings.aDec === ',' && settings.aSep !== '.') {
	                settings.altDec = '.';
	            }
	        }
	        /** cache regexps for autoStrip */
	        var aNegReg = settings.aNeg ? '([-\\' + settings.aNeg + ']?)' : '(-?)';
	        settings.aNegRegAutoStrip = aNegReg;
	        settings.skipFirstAutoStrip = new RegExp(aNegReg + '[^-' + (settings.aNeg ? '\\' + settings.aNeg : '') + '\\' + settings.aDec + '\\d]' + '.*?(\\d|\\' + settings.aDec + '\\d)');
	        settings.skipLastAutoStrip = new RegExp('(\\d\\' + settings.aDec + '?)[^\\' + settings.aDec + '\\d]\\D*$');
	        var allowed = '-' + settings.aNum + '\\' + settings.aDec;
	        settings.allowedAutoStrip = new RegExp('[^' + allowed + ']', 'gi');
	        settings.numRegAutoStrip = new RegExp(aNegReg + '(?:\\' + settings.aDec + '?(\\d+\\' + settings.aDec + '\\d+)|(\\d*(?:\\' + settings.aDec + '\\d*)?))');
	        return settings;
	    }
	    /**
	     * strip all unwanted characters and leave only a number alert
	     */
	    function autoStrip(s, settings, strip_zero) {
	        if (settings.aSign) {
	            /** remove currency sign */
	            while (s.indexOf(settings.aSign) > -1) {
	                s = s.replace(settings.aSign, '');
	            }
	        }
	        s = s.replace(settings.skipFirstAutoStrip, '$1$2'); /** first replace anything before digits */
	        s = s.replace(settings.skipLastAutoStrip, '$1'); /** then replace anything after digits */
	        s = s.replace(settings.allowedAutoStrip, ''); /** then remove any uninterested characters */
	        if (settings.altDec) {
	            s = s.replace(settings.altDec, settings.aDec);
	        } /** get only number string */
	        var m = s.match(settings.numRegAutoStrip);
	        s = m ? [m[1], m[2], m[3]].join('') : '';
	        if ((settings.lZero === 'allow' || settings.lZero === 'keep') && strip_zero !== 'strip') {
	            var parts = [],
	                nSign = '';
	            parts = s.split(settings.aDec);
	            if (parts[0].indexOf('-') !== -1) {
	                nSign = '-';
	                parts[0] = parts[0].replace('-', '');
	            }
	            if (parts[0].length > settings.mInt && parts[0].charAt(0) === '0') {
	                /** strip leading zero if need */
	                parts[0] = parts[0].slice(1);
	            }
	            s = nSign + parts.join(settings.aDec);
	        }
	        if (strip_zero && settings.lZero === 'deny' || strip_zero && settings.lZero === 'allow' && settings.allowLeading === false) {
	            var strip_reg = '^' + settings.aNegRegAutoStrip + '0*(\\d' + (strip_zero === 'leading' ? ')' : '|$)');
	            strip_reg = new RegExp(strip_reg);
	            s = s.replace(strip_reg, '$1$2');
	        }
	        return s;
	    }
	    /**
	     * places or removes brackets on negative values
	     */
	    function negativeBracket(s, nBracket, oEvent) {
	        /** oEvent = settings.oEvent */
	        nBracket = nBracket.split(',');
	        if (oEvent === 'set' || oEvent === 'focusout') {
	            s = s.replace('-', '');
	            s = nBracket[0] + s + nBracket[1];
	        } else if ((oEvent === 'get' || oEvent === 'focusin' || oEvent === 'pageLoad') && s.charAt(0) === nBracket[0]) {
	            s = s.replace(nBracket[0], '-');
	            s = s.replace(nBracket[1], '');
	        }
	        return s;
	    }
	    /**
	     * truncate decimal part of a number
	     */
	    function truncateDecimal(s, aDec, mDec) {
	        if (aDec && mDec) {
	            var parts = s.split(aDec);
	            /** truncate decimal part to satisfying length
	             * cause we would round it anyway */
	            if (parts[1] && parts[1].length > mDec) {
	                if (mDec > 0) {
	                    parts[1] = parts[1].substring(0, mDec);
	                    s = parts.join(aDec);
	                } else {
	                    s = parts[0];
	                }
	            }
	        }
	        return s;
	    }
	    /**
	     * prepare number string to be converted to real number
	     */
	    function fixNumber(s, aDec, aNeg) {
	        if (aDec && aDec !== '.') {
	            s = s.replace(aDec, '.');
	        }
	        if (aNeg && aNeg !== '-') {
	            s = s.replace(aNeg, '-');
	        }
	        if (!s.match(/\d/)) {
	            s += '0';
	        }
	        return s;
	    }
	    /**
	     * function to handle numbers less than 0 that are stored in Exponential notation ex: .0000001 stored as 1e-7
	     */
	    function checkValue(value, settings) {
	        if (value) {
	            var checkSmall = +value;
	            if (checkSmall < 0.000001 && checkSmall > -1) {
	                value = +value;
	                if (value < 0.000001 && value > 0) {
	                    value = (value + 10).toString();
	                    value = value.substring(1);
	                }
	                if (value < 0 && value > -1) {
	                    value = (value - 10).toString();
	                    value = '-' + value.substring(2);
	                }
	                value = value.toString();
	            } else {
	                var parts = value.split('.');
	                if (parts[1] !== undefined) {
	                    if (+parts[1] === 0) {
	                        value = parts[0];
	                    } else {
	                        parts[1] = parts[1].replace(/0*$/, '');
	                        value = parts.join('.');
	                    }
	                }
	            }
	        }
	        return settings.lZero === 'keep' ? value : value.replace(/^0*(\d)/, '$1');
	    }
	    /**
	     * prepare real number to be converted to our format
	     */
	    function presentNumber(s, aDec, aNeg) {
	        if (aNeg && aNeg !== '-') {
	            s = s.replace('-', aNeg);
	        }
	        if (aDec && aDec !== '.') {
	            s = s.replace('.', aDec);
	        }
	        return s;
	    }
	    /**
	     * checking that number satisfy format conditions
	     * and lays between settings.vMin and settings.vMax
	     * and the string length does not exceed the digits in settings.vMin and settings.vMax
	     */
	    function autoCheck(s, settings) {
	        s = autoStrip(s, settings);
	        s = truncateDecimal(s, settings.aDec, settings.mDec);
	        s = fixNumber(s, settings.aDec, settings.aNeg);
	        var value = +s;
	        if (settings.oEvent === 'set' && (value < settings.vMin || value > settings.vMax)) {
	            $.error("The value (" + value + ") from the 'set' method falls outside of the vMin / vMax range");
	        }
	        return value >= settings.vMin && value <= settings.vMax;
	    }
	    /**
	     * private function to check for empty value
	     */
	    function checkEmpty(iv, settings, signOnEmpty) {
	        if (iv === '' || iv === settings.aNeg) {
	            if (settings.wEmpty === 'zero') {
	                return iv + '0';
	            }
	            if (settings.wEmpty === 'sign' || signOnEmpty) {
	                return iv + settings.aSign;
	            }
	            return iv;
	        }
	        return null;
	    }
	    /**
	     * private function that formats our number
	     */
	    function autoGroup(iv, settings) {
	        iv = autoStrip(iv, settings);
	        var testNeg = iv.replace(',', '.'),
	            empty = checkEmpty(iv, settings, true);
	        if (empty !== null) {
	            return empty;
	        }
	        var digitalGroup = '';
	        if (settings.dGroup === 2) {
	            digitalGroup = /(\d)((\d)(\d{2}?)+)$/;
	        } else if (settings.dGroup === 4) {
	            digitalGroup = /(\d)((\d{4}?)+)$/;
	        } else {
	            digitalGroup = /(\d)((\d{3}?)+)$/;
	        } /** splits the string at the decimal string */
	        var ivSplit = iv.split(settings.aDec);
	        if (settings.altDec && ivSplit.length === 1) {
	            ivSplit = iv.split(settings.altDec);
	        } /** assigns the whole number to the a varibale (s) */
	        var s = ivSplit[0];
	        if (settings.aSep) {
	            while (digitalGroup.test(s)) {
	                /** re-inserts the thousand sepparator via a regualer expression */
	                s = s.replace(digitalGroup, '$1' + settings.aSep + '$2');
	            }
	        }
	        if (settings.mDec !== 0 && ivSplit.length > 1) {
	            if (ivSplit[1].length > settings.mDec) {
	                ivSplit[1] = ivSplit[1].substring(0, settings.mDec);
	            } /** joins the whole number with the deciaml value */
	            iv = s + settings.aDec + ivSplit[1];
	        } else {
	            /** if whole numbers only */
	            iv = s;
	        }
	        if (settings.aSign) {
	            var has_aNeg = iv.indexOf(settings.aNeg) !== -1;
	            iv = iv.replace(settings.aNeg, '');
	            iv = settings.pSign === 'p' ? settings.aSign + iv : iv + settings.aSign;
	            if (has_aNeg) {
	                iv = settings.aNeg + iv;
	            }
	        }
	        if (settings.oEvent === 'set' && testNeg < 0 && settings.nBracket !== null) {
	            /** removes the negative sign and places brackets */
	            iv = negativeBracket(iv, settings.nBracket, settings.oEvent);
	        }
	        return iv;
	    }
	    /**
	     * round number after setting by pasting or $().autoNumericSet()
	     * private function for round the number
	     * please note this handled as text - JavaScript math function can return inaccurate values
	     * also this offers multiple rounding methods that are not easily accomplished in JavaScript
	     */
	    function autoRound(iv, settings) {
	        /** value to string */
	        iv = iv === '' ? '0' : iv.toString();
	        convertKeyToNumber(settings, 'mDec'); /** set mDec to number needed when mDec set by 'update method */
	        if (settings.mRound === 'CHF') {
	            iv = (Math.round(iv * 20) / 20).toString();
	        }
	        var ivRounded = '',
	            i = 0,
	            nSign = '',
	            rDec = typeof settings.aPad === 'boolean' || settings.aPad === null ? settings.aPad ? settings.mDec : 0 : +settings.aPad;
	        var truncateZeros = function truncateZeros(ivRounded) {
	            /** truncate not needed zeros */
	            var regex = rDec === 0 ? /(\.(?:\d*[1-9])?)0*$/ : rDec === 1 ? /(\.\d(?:\d*[1-9])?)0*$/ : new RegExp('(\\.\\d{' + rDec + '}(?:\\d*[1-9])?)0*$');
	            ivRounded = ivRounded.replace(regex, '$1'); /** If there are no decimal places, we don't need a decimal point at the end */
	            if (rDec === 0) {
	                ivRounded = ivRounded.replace(/\.$/, '');
	            }
	            return ivRounded;
	        };
	        if (iv.charAt(0) === '-') {
	            /** Checks if the iv (input Value)is a negative value */
	            nSign = '-';
	            iv = iv.replace('-', ''); /** removes the negative sign will be added back later if required */
	        }
	        if (!iv.match(/^\d/)) {
	            /** append a zero if first character is not a digit (then it is likely to be a dot)*/
	            iv = '0' + iv;
	        }
	        if (nSign === '-' && +iv === 0) {
	            /** determines if the value is zero - if zero no negative sign */
	            nSign = '';
	        }
	        if (+iv > 0 && settings.lZero !== 'keep' || iv.length > 0 && settings.lZero === 'allow') {
	            /** trims leading zero's if needed */
	            iv = iv.replace(/^0*(\d)/, '$1');
	        }
	        var dPos = iv.lastIndexOf('.'),
	            /** virtual decimal position */
	        vdPos = dPos === -1 ? iv.length - 1 : dPos,
	            /** checks decimal places to determine if rounding is required */
	        cDec = iv.length - 1 - vdPos; /** check if no rounding is required */
	        if (cDec <= settings.mDec) {
	            ivRounded = iv; /** check if we need to pad with zeros */
	            if (cDec < rDec) {
	                if (dPos === -1) {
	                    ivRounded += '.';
	                }
	                var zeros = '000000';
	                while (cDec < rDec) {
	                    zeros = zeros.substring(0, rDec - cDec);
	                    ivRounded += zeros;
	                    cDec += zeros.length;
	                }
	            } else if (cDec > rDec) {
	                ivRounded = truncateZeros(ivRounded);
	            } else if (cDec === 0 && rDec === 0) {
	                ivRounded = ivRounded.replace(/\.$/, '');
	            }
	            if (settings.mRound !== 'CHF') {
	                return +ivRounded === 0 ? ivRounded : nSign + ivRounded;
	            }
	            if (settings.mRound === 'CHF') {
	                dPos = ivRounded.lastIndexOf('.');
	                iv = ivRounded;
	            }
	        } /** rounded length of the string after rounding */
	        var rLength = dPos + settings.mDec,
	            tRound = +iv.charAt(rLength + 1),
	            ivArray = iv.substring(0, rLength + 1).split(''),
	            odd = iv.charAt(rLength) === '.' ? iv.charAt(rLength - 1) % 2 : iv.charAt(rLength) % 2,
	            onePass = true;
	        if (odd !== 1) {
	            odd = odd === 0 && iv.substring(rLength + 2, iv.length) > 0 ? 1 : 0;
	        }
	        if (tRound > 4 && settings.mRound === 'S' || /** Round half up symmetric */
	        tRound > 4 && settings.mRound === 'A' && nSign === '' || /** Round half up asymmetric positive values */
	        tRound > 5 && settings.mRound === 'A' && nSign === '-' || /** Round half up asymmetric negative values */
	        tRound > 5 && settings.mRound === 's' || /** Round half down symmetric */
	        tRound > 5 && settings.mRound === 'a' && nSign === '' || /** Round half down asymmetric positive values */
	        tRound > 4 && settings.mRound === 'a' && nSign === '-' || /** Round half down asymmetric negative values */
	        tRound > 5 && settings.mRound === 'B' || /** Round half even "Banker's Rounding" */
	        tRound === 5 && settings.mRound === 'B' && odd === 1 || /** Round half even "Banker's Rounding" */
	        tRound > 0 && settings.mRound === 'C' && nSign === '' || /** Round to ceiling toward positive infinite */
	        tRound > 0 && settings.mRound === 'F' && nSign === '-' || /** Round to floor toward negative infinite */
	        tRound > 0 && settings.mRound === 'U' || settings.mRound === 'CHF') {
	            /** round up away from zero */
	            for (i = ivArray.length - 1; i >= 0; i -= 1) {
	                /** Round up the last digit if required, and continue until no more 9's are found */
	                if (ivArray[i] !== '.') {
	                    if (settings.mRound === 'CHF' && ivArray[i] <= 2 && onePass) {
	                        ivArray[i] = 0;
	                        onePass = false;
	                        break;
	                    }
	                    if (settings.mRound === 'CHF' && ivArray[i] <= 7 && onePass) {
	                        ivArray[i] = 5;
	                        onePass = false;
	                        break;
	                    }
	                    if (settings.mRound === 'CHF' && onePass) {
	                        ivArray[i] = 10;
	                        onePass = false;
	                    } else {
	                        ivArray[i] = +ivArray[i] + 1;
	                    }
	                    if (ivArray[i] < 10) {
	                        break;
	                    }
	                    if (i > 0) {
	                        ivArray[i] = '0';
	                    }
	                }
	            }
	        }
	        ivArray = ivArray.slice(0, rLength + 1); /** Reconstruct the string, converting any 10's to 0's */
	        ivRounded = truncateZeros(ivArray.join('')); /** return rounded value */
	        return +ivRounded === 0 ? ivRounded : nSign + ivRounded;
	    }
	    /**
	     * Holder object for field properties
	     */
	    function AutoNumericHolder(that, settings) {
	        this.settings = settings;
	        this.that = that;
	        this.$that = $(that);
	        this.formatted = false;
	        this.settingsClone = autoCode(this.$that, this.settings);
	        this.value = that.value;
	    }
	    AutoNumericHolder.prototype = {
	        init: function init(e) {
	            this.value = this.that.value;
	            this.settingsClone = autoCode(this.$that, this.settings);
	            this.ctrlKey = e.ctrlKey;
	            this.cmdKey = e.metaKey;
	            this.shiftKey = e.shiftKey;
	            this.selection = getElementSelection(this.that); /** keypress event overwrites meaningful value of e.keyCode */
	            if (e.type === 'keydown' || e.type === 'keyup') {
	                this.kdCode = e.keyCode;
	            }
	            this.which = e.which;
	            this.processed = false;
	            this.formatted = false;
	        },
	        setSelection: function setSelection(start, end, setReal) {
	            start = Math.max(start, 0);
	            end = Math.min(end, this.that.value.length);
	            this.selection = {
	                start: start,
	                end: end,
	                length: end - start
	            };
	            if (setReal === undefined || setReal) {
	                setElementSelection(this.that, start, end);
	            }
	        },
	        setPosition: function setPosition(pos, setReal) {
	            this.setSelection(pos, pos, setReal);
	        },
	        getBeforeAfter: function getBeforeAfter() {
	            var value = this.value,
	                left = value.substring(0, this.selection.start),
	                right = value.substring(this.selection.end, value.length);
	            return [left, right];
	        },
	        getBeforeAfterStriped: function getBeforeAfterStriped() {
	            var parts = this.getBeforeAfter();
	            parts[0] = autoStrip(parts[0], this.settingsClone);
	            parts[1] = autoStrip(parts[1], this.settingsClone);
	            return parts;
	        },
	        /**
	         * strip parts from excess characters and leading zeroes
	         */
	        normalizeParts: function normalizeParts(left, right) {
	            var settingsClone = this.settingsClone;
	            right = autoStrip(right, settingsClone); /** if right is not empty and first character is not aDec, */
	            /** we could strip all zeros, otherwise only leading */
	            var strip = right.match(/^\d/) ? true : 'leading';
	            left = autoStrip(left, settingsClone, strip); /** prevents multiple leading zeros from being entered */
	            if ((left === '' || left === settingsClone.aNeg) && settingsClone.lZero === 'deny') {
	                if (right > '') {
	                    right = right.replace(/^0*(\d)/, '$1');
	                }
	            }
	            var new_value = left + right; /** insert zero if has leading dot */
	            if (settingsClone.aDec) {
	                var m = new_value.match(new RegExp('^' + settingsClone.aNegRegAutoStrip + '\\' + settingsClone.aDec));
	                if (m) {
	                    left = left.replace(m[1], m[1] + '0');
	                    new_value = left + right;
	                }
	            } /** insert zero if number is empty and io.wEmpty == 'zero' */
	            if (settingsClone.wEmpty === 'zero' && (new_value === settingsClone.aNeg || new_value === '')) {
	                left += '0';
	            }
	            return [left, right];
	        },
	        /**
	         * set part of number to value keeping position of cursor
	         */
	        setValueParts: function setValueParts(left, right) {
	            var settingsClone = this.settingsClone,
	                parts = this.normalizeParts(left, right),
	                new_value = parts.join(''),
	                position = parts[0].length;
	            if (autoCheck(new_value, settingsClone)) {
	                new_value = truncateDecimal(new_value, settingsClone.aDec, settingsClone.mDec);
	                if (position > new_value.length) {
	                    position = new_value.length;
	                }
	                this.value = new_value;
	                this.setPosition(position, false);
	                return true;
	            }
	            return false;
	        },
	        /**
	         * helper function for expandSelectionOnSign
	         * returns sign position of a formatted value
	         */
	        signPosition: function signPosition() {
	            var settingsClone = this.settingsClone,
	                aSign = settingsClone.aSign,
	                that = this.that;
	            if (aSign) {
	                var aSignLen = aSign.length;
	                if (settingsClone.pSign === 'p') {
	                    var hasNeg = settingsClone.aNeg && that.value && that.value.charAt(0) === settingsClone.aNeg;
	                    return hasNeg ? [1, aSignLen + 1] : [0, aSignLen];
	                }
	                var valueLen = that.value.length;
	                return [valueLen - aSignLen, valueLen];
	            }
	            return [1000, -1];
	        },
	        /**
	         * expands selection to cover whole sign
	         * prevents partial deletion/copying/overwriting of a sign
	         */
	        expandSelectionOnSign: function expandSelectionOnSign(setReal) {
	            var sign_position = this.signPosition(),
	                selection = this.selection;
	            if (selection.start < sign_position[1] && selection.end > sign_position[0]) {
	                /** if selection catches something except sign and catches only space from sign */
	                if ((selection.start < sign_position[0] || selection.end > sign_position[1]) && this.value.substring(Math.max(selection.start, sign_position[0]), Math.min(selection.end, sign_position[1])).match(/^\s*$/)) {
	                    /** then select without empty space */
	                    if (selection.start < sign_position[0]) {
	                        this.setSelection(selection.start, sign_position[0], setReal);
	                    } else {
	                        this.setSelection(sign_position[1], selection.end, setReal);
	                    }
	                } else {
	                    /** else select with whole sign */
	                    this.setSelection(Math.min(selection.start, sign_position[0]), Math.max(selection.end, sign_position[1]), setReal);
	                }
	            }
	        },
	        /**
	         * try to strip pasted value to digits
	         */
	        checkPaste: function checkPaste() {
	            if (this.valuePartsBeforePaste !== undefined) {
	                var parts = this.getBeforeAfter(),
	                    oldParts = this.valuePartsBeforePaste;
	                delete this.valuePartsBeforePaste; /** try to strip pasted value first */
	                parts[0] = parts[0].substr(0, oldParts[0].length) + autoStrip(parts[0].substr(oldParts[0].length), this.settingsClone);
	                if (!this.setValueParts(parts[0], parts[1])) {
	                    this.value = oldParts.join('');
	                    this.setPosition(oldParts[0].length, false);
	                }
	            }
	        },
	        /**
	         * process pasting, cursor moving and skipping of not interesting keys
	         * if returns true, further processing is not performed
	         */
	        skipAllways: function skipAllways(e) {
	            var kdCode = this.kdCode,
	                which = this.which,
	                ctrlKey = this.ctrlKey,
	                cmdKey = this.cmdKey,
	                shiftKey = this.shiftKey; /** catch the ctrl up on ctrl-v */
	            if ((ctrlKey || cmdKey) && e.type === 'keyup' && this.valuePartsBeforePaste !== undefined || shiftKey && kdCode === 45) {
	                this.checkPaste();
	                return false;
	            }
	            /** codes are taken from http://www.cambiaresearch.com/c4/702b8cd1-e5b0-42e6-83ac-25f0306e3e25/Javascript-Char-Codes-Key-Codes.aspx
	             * skip Fx keys, windows keys, other special keys
	             */
	            if (kdCode >= 112 && kdCode <= 123 || kdCode >= 91 && kdCode <= 93 || kdCode >= 9 && kdCode <= 31 || kdCode < 8 && (which === 0 || which === kdCode) || kdCode === 144 || kdCode === 145 || kdCode === 45) {
	                return true;
	            }
	            if ((ctrlKey || cmdKey) && kdCode === 65) {
	                /** if select all (a=65)*/
	                return true;
	            }
	            if ((ctrlKey || cmdKey) && (kdCode === 67 || kdCode === 86 || kdCode === 88)) {
	                /** if copy (c=67) paste (v=86) or cut (x=88) */
	                if (e.type === 'keydown') {
	                    this.expandSelectionOnSign();
	                }
	                if (kdCode === 86 || kdCode === 45) {
	                    /** try to prevent wrong paste */
	                    if (e.type === 'keydown' || e.type === 'keypress') {
	                        if (this.valuePartsBeforePaste === undefined) {
	                            this.valuePartsBeforePaste = this.getBeforeAfter();
	                        }
	                    } else {
	                        this.checkPaste();
	                    }
	                }
	                return e.type === 'keydown' || e.type === 'keypress' || kdCode === 67;
	            }
	            if (ctrlKey || cmdKey) {
	                return true;
	            }
	            if (kdCode === 37 || kdCode === 39) {
	                /** jump over thousand separator */
	                var aSep = this.settingsClone.aSep,
	                    start = this.selection.start,
	                    value = this.that.value;
	                if (e.type === 'keydown' && aSep && !this.shiftKey) {
	                    if (kdCode === 37 && value.charAt(start - 2) === aSep) {
	                        this.setPosition(start - 1);
	                    } else if (kdCode === 39 && value.charAt(start + 1) === aSep) {
	                        this.setPosition(start + 1);
	                    }
	                }
	                return true;
	            }
	            if (kdCode >= 34 && kdCode <= 40) {
	                return true;
	            }
	            return false;
	        },
	        /**
	         * process deletion of characters
	         * returns true if processing performed
	         */
	        processAllways: function processAllways() {
	            var parts; /** process backspace or delete */
	            if (this.kdCode === 8 || this.kdCode === 46) {
	                if (!this.selection.length) {
	                    parts = this.getBeforeAfterStriped();
	                    if (this.kdCode === 8) {
	                        parts[0] = parts[0].substring(0, parts[0].length - 1);
	                    } else {
	                        parts[1] = parts[1].substring(1, parts[1].length);
	                    }
	                    this.setValueParts(parts[0], parts[1]);
	                } else {
	                    this.expandSelectionOnSign(false);
	                    parts = this.getBeforeAfterStriped();
	                    this.setValueParts(parts[0], parts[1]);
	                }
	                return true;
	            }
	            return false;
	        },
	        /**
	         * process insertion of characters
	         * returns true if processing performed
	         */
	        processKeypress: function processKeypress() {
	            var settingsClone = this.settingsClone,
	                cCode = String.fromCharCode(this.which),
	                parts = this.getBeforeAfterStriped(),
	                left = parts[0],
	                right = parts[1]; /** start rules when the decimal character key is pressed */
	            /** always use numeric pad dot to insert decimal separator */
	            if (cCode === settingsClone.aDec || settingsClone.altDec && cCode === settingsClone.altDec || (cCode === '.' || cCode === ',') && this.kdCode === 110) {
	                /** do not allow decimal character if no decimal part allowed */
	                if (!settingsClone.mDec || !settingsClone.aDec) {
	                    return true;
	                } /** do not allow decimal character before aNeg character */
	                if (settingsClone.aNeg && right.indexOf(settingsClone.aNeg) > -1) {
	                    return true;
	                } /** do not allow decimal character if other decimal character present */
	                if (left.indexOf(settingsClone.aDec) > -1) {
	                    return true;
	                }
	                if (right.indexOf(settingsClone.aDec) > 0) {
	                    return true;
	                }
	                if (right.indexOf(settingsClone.aDec) === 0) {
	                    right = right.substr(1);
	                }
	                this.setValueParts(left + settingsClone.aDec, right);
	                return true;
	            }
	            /**
	             * start rule on negative sign & prevent minus if not allowed
	             */
	            if (cCode === '-' || cCode === '+') {
	                if (!settingsClone.aNeg) {
	                    return true;
	                } /** caret is always after minus */
	                if (left === '' && right.indexOf(settingsClone.aNeg) > -1) {
	                    left = settingsClone.aNeg;
	                    right = right.substring(1, right.length);
	                } /** change sign of number, remove part if should */
	                if (left.charAt(0) === settingsClone.aNeg) {
	                    left = left.substring(1, left.length);
	                } else {
	                    left = cCode === '-' ? settingsClone.aNeg + left : left;
	                }
	                this.setValueParts(left, right);
	                return true;
	            } /** digits */
	            if (cCode >= '0' && cCode <= '9') {
	                /** if try to insert digit before minus */
	                if (settingsClone.aNeg && left === '' && right.indexOf(settingsClone.aNeg) > -1) {
	                    left = settingsClone.aNeg;
	                    right = right.substring(1, right.length);
	                }
	                if (settingsClone.vMax <= 0 && settingsClone.vMin < settingsClone.vMax && this.value.indexOf(settingsClone.aNeg) === -1 && cCode !== '0') {
	                    left = settingsClone.aNeg + left;
	                }
	                this.setValueParts(left + cCode, right);
	                return true;
	            } /** prevent any other character */
	            return true;
	        },
	        /**
	         * formatting of just processed value with keeping of cursor position
	         */
	        formatQuick: function formatQuick() {
	            var settingsClone = this.settingsClone,
	                parts = this.getBeforeAfterStriped(),
	                leftLength = this.value;
	            if ((settingsClone.aSep === '' || settingsClone.aSep !== '' && leftLength.indexOf(settingsClone.aSep) === -1) && (settingsClone.aSign === '' || settingsClone.aSign !== '' && leftLength.indexOf(settingsClone.aSign) === -1)) {
	                var subParts = [],
	                    nSign = '';
	                subParts = leftLength.split(settingsClone.aDec);
	                if (subParts[0].indexOf('-') > -1) {
	                    nSign = '-';
	                    subParts[0] = subParts[0].replace('-', '');
	                    parts[0] = parts[0].replace('-', '');
	                }
	                if (subParts[0].length > settingsClone.mInt && parts[0].charAt(0) === '0') {
	                    /** strip leading zero if need */
	                    parts[0] = parts[0].slice(1);
	                }
	                parts[0] = nSign + parts[0];
	            }
	            var value = autoGroup(this.value, this.settingsClone),
	                position = value.length;
	            if (value) {
	                /** prepare regexp which searches for cursor position from unformatted left part */
	                var left_ar = parts[0].split(''),
	                    i = 0;
	                for (i; i < left_ar.length; i += 1) {
	                    /** thanks Peter Kovari */
	                    if (!left_ar[i].match('\\d')) {
	                        left_ar[i] = '\\' + left_ar[i];
	                    }
	                }
	                var leftReg = new RegExp('^.*?' + left_ar.join('.*?'));
	                /** search cursor position in formatted value */
	                var newLeft = value.match(leftReg);
	                if (newLeft) {
	                    position = newLeft[0].length;
	                    /** if we are just before sign which is in prefix position */
	                    if ((position === 0 && value.charAt(0) !== settingsClone.aNeg || position === 1 && value.charAt(0) === settingsClone.aNeg) && settingsClone.aSign && settingsClone.pSign === 'p') {
	                        /** place caret after prefix sign */
	                        position = this.settingsClone.aSign.length + (value.charAt(0) === '-' ? 1 : 0);
	                    }
	                } else if (settingsClone.aSign && settingsClone.pSign === 's') {
	                    /** if we could not find a place for cursor and have a sign as a suffix */
	                    /** place carret before suffix currency sign */
	                    position -= settingsClone.aSign.length;
	                }
	            }
	            this.that.value = value;
	            this.setPosition(position);
	            this.formatted = true;
	        }
	    };
	    /** thanks to Anthony & Evan C */
	    function autoGet(obj) {
	        if (typeof obj === 'string') {
	            obj = obj.replace(/\[/g, "\\[").replace(/\]/g, "\\]");
	            obj = '#' + obj.replace(/(:|\.)/g, '\\$1');
	            /** obj = '#' + obj.replace(/([;&,\.\+\*\~':"\!\^#$%@\[\]\(\)=>\|])/g, '\\$1'); */
	            /** possible modification to replace the above 2 lines */
	        }
	        return $(obj);
	    }
	
	    function getHolder($that, settings, update) {
	        var data = $that.data('autoNumeric');
	        if (!data) {
	            data = {};
	            $that.data('autoNumeric', data);
	        }
	        var holder = data.holder;
	        if (holder === undefined && settings || update) {
	            holder = new AutoNumericHolder($that.get(0), settings);
	            data.holder = holder;
	        }
	        return holder;
	    }
	    var methods = {
	        init: function init(options) {
	            return this.each(function () {
	                var $this = $(this),
	                    settings = $this.data('autoNumeric'),
	                    /** attempt to grab 'autoNumeric' settings, if they don't exist returns "undefined". */
	                tagData = $this.data(); /** attempt to grab HTML5 data, if they don't exist we'll get "undefined".*/
	                if ((typeof settings === 'undefined' ? 'undefined' : _typeof(settings)) !== 'object') {
	                    /** If we couldn't grab settings, create them from defaults and passed options. */
	                    var defaults = {
	                        /** allowed numeric values
	                         * please do not modify
	                         */
	                        aNum: '0123456789',
	                        /** allowed thousand separator characters
	                         * comma = ','
	                         * period "full stop" = '.'
	                         * apostrophe is escaped = '\''
	                         * space = ' '
	                         * none = ''
	                         * NOTE: do not use numeric characters
	                         */
	                        aSep: ',',
	                        /** digital grouping for the thousand separator used in Format
	                         * dGroup: '2', results in 99,99,99,999 common in India for values less than 1 billion and greater than -1 billion
	                         * dGroup: '3', results in 999,999,999 default
	                         * dGroup: '4', results in 9999,9999,9999 used in some Asian countries
	                         */
	                        dGroup: '3',
	                        /** allowed decimal separator characters
	                         * period "full stop" = '.'
	                         * comma = ','
	                         */
	                        aDec: '.',
	                        /** allow to declare alternative decimal separator which is automatically replaced by aDec
	                         * developed for countries the use a comma ',' as the decimal character
	                         * and have keyboards\numeric pads that have a period 'full stop' as the decimal characters (Spain is an example)
	                         */
	                        altDec: null,
	                        /** allowed currency symbol
	                         * Must be in quotes aSign: '$', a space is allowed aSign: '$ '
	                         */
	                        aSign: '',
	                        /** placement of currency sign
	                         * for prefix pSign: 'p',
	                         * for suffix pSign: 's',
	                         */
	                        pSign: 'p',
	                        /** maximum possible value
	                         * value must be enclosed in quotes and use the period for the decimal point
	                         * value must be larger than vMin
	                         */
	                        vMax: '9999999999999.99',
	                        /** minimum possible value
	                         * value must be enclosed in quotes and use the period for the decimal point
	                         * value must be smaller than vMax
	                         */
	                        vMin: '0.00',
	                        /** max number of decimal places = used to override decimal places set by the vMin & vMax values
	                         * value must be enclosed in quotes example mDec: '3',
	                         * This can also set the value via a call back function mDec: 'css:#
	                         */
	                        mDec: null,
	                        /** method used for rounding
	                         * mRound: 'S', Round-Half-Up Symmetric (default)
	                         * mRound: 'A', Round-Half-Up Asymmetric
	                         * mRound: 's', Round-Half-Down Symmetric (lower case s)
	                         * mRound: 'a', Round-Half-Down Asymmetric (lower case a)
	                         * mRound: 'B', Round-Half-Even "Bankers Rounding"
	                         * mRound: 'U', Round Up "Round-Away-From-Zero"
	                         * mRound: 'D', Round Down "Round-Toward-Zero" - same as truncate
	                         * mRound: 'C', Round to Ceiling "Toward Positive Infinity"
	                         * mRound: 'F', Round to Floor "Toward Negative Infinity"
	                         */
	                        mRound: 'S',
	                        /** controls decimal padding
	                         * aPad: true - always Pad decimals with zeros
	                         * aPad: false - does not pad with zeros.
	                         * aPad: `some number` - pad decimals with zero to number different from mDec
	                         * thanks to Jonas Johansson for the suggestion
	                         */
	                        aPad: true,
	                        /** places brackets on negative value -$ 999.99 to (999.99)
	                         * visible only when the field does NOT have focus the left and right symbols should be enclosed in quotes and seperated by a comma
	                         * nBracket: null, nBracket: '(,)', nBracket: '[,]', nBracket: '<,>' or nBracket: '{,}'
	                         */
	                        nBracket: null,
	                        /** Displayed on empty string
	                         * wEmpty: 'empty', - input can be blank
	                         * wEmpty: 'zero', - displays zero
	                         * wEmpty: 'sign', - displays the currency sign
	                         */
	                        wEmpty: 'empty',
	                        /** controls leading zero behavior
	                         * lZero: 'allow', - allows leading zeros to be entered. Zeros will be truncated when entering additional digits. On focusout zeros will be deleted.
	                         * lZero: 'deny', - allows only one leading zero on values less than one
	                         * lZero: 'keep', - allows leading zeros to be entered. on fousout zeros will be retained.
	                         */
	                        lZero: 'allow',
	                        /** determine if the default value will be formatted on page ready.
	                         * true = automatically formats the default value on page ready
	                         * false = will not format the default value
	                         */
	                        aForm: true,
	                        /** future use */
	                        onSomeEvent: function onSomeEvent() {}
	                    };
	                    settings = $.extend({}, defaults, tagData, options); /** Merge defaults, tagData and options */
	                    if (settings.aDec === settings.aSep) {
	                        $.error("autoNumeric will not function properly when the decimal character aDec: '" + settings.aDec + "' and thousand separator aSep: '" + settings.aSep + "' are the same character");
	                        return this;
	                    }
	                    $this.data('autoNumeric', settings); /** Save our new settings */
	                } else {
	                        return this;
	                    }
	                settings.runOnce = false;
	                var holder = getHolder($this, settings);
	                if ($.inArray($this.prop('tagName').toLowerCase(), settings.tagList) === -1 && $this.prop('tagName').toLowerCase() !== 'input') {
	                    $.error("The <" + $this.prop('tagName').toLowerCase() + "> is not supported by autoNumeric()");
	                    return this;
	                }
	                if (settings.runOnce === false && settings.aForm) {
	                    /** routine to format default value on page load */
	                    if ($this.is('input[type=text], input[type=hidden], input[type=tel], input:not([type])')) {
	                        var setValue = true;
	                        if ($this[0].value === '' && settings.wEmpty === 'empty') {
	                            $this[0].value = '';
	                            setValue = false;
	                        }
	                        if ($this[0].value === '' && settings.wEmpty === 'sign') {
	                            $this[0].value = settings.aSign;
	                            setValue = false;
	                        }
	                        if (setValue) {
	                            $this.autoNumeric('set', $this.val());
	                        }
	                    }
	                    if ($.inArray($this.prop('tagName').toLowerCase(), settings.tagList) !== -1 && $this.text() !== '') {
	                        $this.autoNumeric('set', $this.text());
	                    }
	                }
	                settings.runOnce = true;
	                if ($this.is('input[type=text], input[type=hidden], input[type=tel], input:not([type])')) {
	                    /**added hidden type */
	                    $this.on('keydown.autoNumeric', function (e) {
	                        holder = getHolder($this);
	                        if (holder.settings.aDec === holder.settings.aSep) {
	                            $.error("autoNumeric will not function properly when the decimal character aDec: '" + holder.settings.aDec + "' and thousand separator aSep: '" + holder.settings.aSep + "' are the same character");
	                            return this;
	                        }
	                        if (holder.that.readOnly) {
	                            holder.processed = true;
	                            return true;
	                        }
	                        /** The below streamed code / comment allows the "enter" keydown to throw a change() event */
	                        /** if (e.keyCode === 13 && holder.inVal !== $this.val()){
	                            $this.change();
	                            holder.inVal = $this.val();
	                        }*/
	                        holder.init(e);
	                        holder.settings.oEvent = 'keydown';
	                        if (holder.skipAllways(e)) {
	                            holder.processed = true;
	                            return true;
	                        }
	                        if (holder.processAllways()) {
	                            holder.processed = true;
	                            holder.formatQuick();
	                            e.preventDefault();
	                            return false;
	                        }
	                        holder.formatted = false;
	                        return true;
	                    });
	                    $this.on('keypress.autoNumeric', function (e) {
	                        var holder = getHolder($this),
	                            processed = holder.processed;
	                        holder.init(e);
	                        holder.settings.oEvent = 'keypress';
	                        if (holder.skipAllways(e)) {
	                            return true;
	                        }
	                        if (processed) {
	                            e.preventDefault();
	                            return false;
	                        }
	                        if (holder.processAllways() || holder.processKeypress()) {
	                            holder.formatQuick();
	                            e.preventDefault();
	                            return false;
	                        }
	                        holder.formatted = false;
	                    });
	                    $this.on('keyup.autoNumeric', function (e) {
	                        var holder = getHolder($this);
	                        holder.init(e);
	                        holder.settings.oEvent = 'keyup';
	                        var skip = holder.skipAllways(e);
	                        holder.kdCode = 0;
	                        delete holder.valuePartsBeforePaste;
	                        if ($this[0].value === holder.settings.aSign) {
	                            /** added to properly place the caret when only the currency is present */
	                            if (holder.settings.pSign === 's') {
	                                setElementSelection(this, 0, 0);
	                            } else {
	                                setElementSelection(this, holder.settings.aSign.length, holder.settings.aSign.length);
	                            }
	                        }
	                        if (skip) {
	                            return true;
	                        }
	                        if (this.value === '') {
	                            return true;
	                        }
	                        if (!holder.formatted) {
	                            holder.formatQuick();
	                        }
	                    });
	                    $this.on('focusin.autoNumeric', function () {
	                        var holder = getHolder($this);
	                        holder.settingsClone.oEvent = 'focusin';
	                        if (holder.settingsClone.nBracket !== null) {
	                            var checkVal = $this.val();
	                            $this.val(negativeBracket(checkVal, holder.settingsClone.nBracket, holder.settingsClone.oEvent));
	                        }
	                        holder.inVal = $this.val();
	                        var onempty = checkEmpty(holder.inVal, holder.settingsClone, true);
	                        if (onempty !== null) {
	                            $this.val(onempty);
	                            if (holder.settings.pSign === 's') {
	                                setElementSelection(this, 0, 0);
	                            } else {
	                                setElementSelection(this, holder.settings.aSign.length, holder.settings.aSign.length);
	                            }
	                        }
	                    });
	                    $this.on('focusout.autoNumeric', function () {
	                        var holder = getHolder($this),
	                            settingsClone = holder.settingsClone,
	                            value = $this.val(),
	                            origValue = value;
	                        holder.settingsClone.oEvent = 'focusout';
	                        var strip_zero = ''; /** added to control leading zero */
	                        if (settingsClone.lZero === 'allow') {
	                            /** added to control leading zero */
	                            settingsClone.allowLeading = false;
	                            strip_zero = 'leading';
	                        }
	                        if (value !== '') {
	                            value = autoStrip(value, settingsClone, strip_zero);
	                            if (checkEmpty(value, settingsClone) === null && autoCheck(value, settingsClone, $this[0])) {
	                                value = fixNumber(value, settingsClone.aDec, settingsClone.aNeg);
	                                value = autoRound(value, settingsClone);
	                                value = presentNumber(value, settingsClone.aDec, settingsClone.aNeg);
	                            } else {
	                                value = '';
	                            }
	                        }
	                        var groupedValue = checkEmpty(value, settingsClone, false);
	                        if (groupedValue === null) {
	                            groupedValue = autoGroup(value, settingsClone);
	                        }
	                        if (groupedValue !== origValue) {
	                            $this.val(groupedValue);
	                        }
	                        if (groupedValue !== holder.inVal) {
	                            $this.change();
	                            delete holder.inVal;
	                        }
	                        if (settingsClone.nBracket !== null && $this.autoNumeric('get') < 0) {
	                            holder.settingsClone.oEvent = 'focusout';
	                            $this.val(negativeBracket($this.val(), settingsClone.nBracket, settingsClone.oEvent));
	                        }
	                    });
	                }
	            });
	        },
	        /** method to remove settings and stop autoNumeric() */
	        destroy: function destroy() {
	            return $(this).each(function () {
	                var $this = $(this);
	                $this.off('.autoNumeric');
	                $this.removeData('autoNumeric');
	            });
	        },
	        /** method to update settings - can call as many times */
	        update: function update(options) {
	            return $(this).each(function () {
	                var $this = autoGet($(this)),
	                    settings = $this.data('autoNumeric');
	                if ((typeof settings === 'undefined' ? 'undefined' : _typeof(settings)) !== 'object') {
	                    $.error("You must initialize autoNumeric('init', {options}) prior to calling the 'update' method");
	                    return this;
	                }
	                var strip = $this.autoNumeric('get');
	                settings = $.extend(settings, options);
	                getHolder($this, settings, true);
	                if (settings.aDec === settings.aSep) {
	                    $.error("autoNumeric will not function properly when the decimal character aDec: '" + settings.aDec + "' and thousand separator aSep: '" + settings.aSep + "' are the same character");
	                    return this;
	                }
	                $this.data('autoNumeric', settings);
	                if ($this.val() !== '' || $this.text() !== '') {
	                    return $this.autoNumeric('set', strip);
	                }
	                return;
	            });
	        },
	        /** returns a formatted strings for "input:text" fields Uses jQuery's .val() method*/
	        set: function set(valueIn) {
	            if (valueIn === null) {
	                return;
	            }
	            return $(this).each(function () {
	                var $this = autoGet($(this)),
	                    settings = $this.data('autoNumeric'),
	                    value = valueIn.toString(),
	                    testValue = valueIn.toString();
	                if ((typeof settings === 'undefined' ? 'undefined' : _typeof(settings)) !== 'object') {
	                    $.error("You must initialize autoNumeric('init', {options}) prior to calling the 'set' method");
	                    return this;
	                }
	                /** routine to handle page re-load from back button */
	                if (testValue !== $this.attr('value') && $this.prop('tagName').toLowerCase() === 'input' && settings.runOnce === false) {
	                    value = settings.nBracket !== null ? negativeBracket($this.val(), settings.nBracket, 'pageLoad') : value;
	                    value = autoStrip(value, settings);
	                }
	                /** allows locale decimal separator to be a comma */
	                if ((testValue === $this.attr('value') || testValue === $this.text()) && settings.runOnce === false) {
	                    value = value.replace(',', '.');
	                }
	                /** returns a empty string if the value being 'set' contains non-numeric characters and or more than decimal point (full stop) and will not be formatted */
	                if (!$.isNumeric(+value)) {
	                    return '';
	                }
	                value = checkValue(value, settings);
	                settings.oEvent = 'set';
	                value.toString();
	                if (value !== '') {
	                    value = autoRound(value, settings);
	                }
	                value = presentNumber(value, settings.aDec, settings.aNeg);
	                if (!autoCheck(value, settings)) {
	                    value = autoRound('', settings);
	                }
	                value = autoGroup(value, settings);
	                if ($this.is('input[type=text], input[type=hidden], input[type=tel], input:not([type])')) {
	                    /**added hidden type */
	                    return $this.val(value);
	                }
	                if ($.inArray($this.prop('tagName').toLowerCase(), settings.tagList) !== -1) {
	                    return $this.text(value);
	                }
	                $.error("The <" + $this.prop('tagName').toLowerCase() + "> is not supported by autoNumeric()");
	                return false;
	            });
	        },
	        /** method to get the unformatted value from a specific input field, returns a numeric value */
	        get: function get() {
	            var $this = autoGet($(this)),
	                settings = $this.data('autoNumeric');
	            if ((typeof settings === 'undefined' ? 'undefined' : _typeof(settings)) !== 'object') {
	                $.error("You must initialize autoNumeric('init', {options}) prior to calling the 'get' method");
	                return this;
	            }
	            settings.oEvent = 'get';
	            var getValue = '';
	            /** determine the element type then use .eq(0) selector to grab the value of the first element in selector */
	            if ($this.is('input[type=text], input[type=hidden], input[type=tel], input:not([type])')) {
	                /**added hidden type */
	                getValue = $this.eq(0).val();
	            } else if ($.inArray($this.prop('tagName').toLowerCase(), settings.tagList) !== -1) {
	                getValue = $this.eq(0).text();
	            } else {
	                $.error("The <" + $this.prop('tagName').toLowerCase() + "> is not supported by autoNumeric()");
	                return false;
	            }
	            if (getValue === '' && settings.wEmpty === 'empty' || getValue === settings.aSign && (settings.wEmpty === 'sign' || settings.wEmpty === 'empty')) {
	                return '';
	            }
	            if (settings.nBracket !== null && getValue !== '') {
	                getValue = negativeBracket(getValue, settings.nBracket, settings.oEvent);
	            }
	            if (settings.runOnce || settings.aForm === false) {
	                getValue = autoStrip(getValue, settings);
	            }
	            getValue = fixNumber(getValue, settings.aDec, settings.aNeg);
	            if (+getValue === 0 && settings.lZero !== 'keep') {
	                getValue = '0';
	            }
	            if (settings.lZero === 'keep') {
	                return getValue;
	            }
	            getValue = checkValue(getValue, settings);
	            return getValue; /** returned Numeric String */
	        },
	        /** method to get the unformatted value from multiple fields */
	        getString: function getString() {
	            var isAutoNumeric = false,
	                $this = autoGet($(this)),
	                str = $this.serialize(),
	                parts = str.split('&'),
	                formIndex = $('form').index($this),
	                i = 0;
	            for (i; i < parts.length; i += 1) {
	                var miniParts = parts[i].split('='),
	                    $field = $('form:eq(' + formIndex + ') input[name="' + decodeURIComponent(miniParts[0]) + '"]'),
	                    settings = $field.data('autoNumeric');
	                if ((typeof settings === 'undefined' ? 'undefined' : _typeof(settings)) === 'object') {
	                    if (miniParts[1] !== null) {
	                        miniParts[1] = $field.autoNumeric('get');
	                        parts[i] = miniParts.join('=');
	                        isAutoNumeric = true;
	                    }
	                }
	            }
	            if (isAutoNumeric === true) {
	                return parts.join('&');
	            }
	            return str;
	        },
	        /** method to get the unformatted value from multiple fields */
	        getArray: function getArray() {
	            var isAutoNumeric = false,
	                $this = autoGet($(this)),
	                formFields = $this.serializeArray(),
	                formIndex = $('form').index($this);
	            /*jslint unparam: true*/
	            $.each(formFields, function (i, field) {
	                var $field = $('form:eq(' + formIndex + ') input[name="' + decodeURIComponent(field.name) + '"]'),
	                    settings = $field.data('autoNumeric');
	                if ((typeof settings === 'undefined' ? 'undefined' : _typeof(settings)) === 'object') {
	                    if (field.value !== '') {
	                        field.value = $field.autoNumeric('get').toString();
	                    }
	                    isAutoNumeric = true;
	                }
	            });
	            /*jslint unparam: false*/
	            if (isAutoNumeric === true) {
	                return formFields;
	            }
	            return this;
	        },
	        /** returns the settings object for those who need to look under the hood */
	        getSettings: function getSettings() {
	            var $this = autoGet($(this));
	            return $this.eq(0).data('autoNumeric');
	        }
	    };
	    $.fn.autoNumeric = function (method) {
	        if (methods[method]) {
	            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
	        }
	        if ((typeof method === 'undefined' ? 'undefined' : _typeof(method)) === 'object' || !method) {
	            return methods.init.apply(this, arguments);
	        }
	        $.error('Method "' + method + '" is not supported by autoNumeric()');
	    };
	})(jQuery);
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 4 */
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;'use strict';
	
	/*!
		Autosize 3.0.15
		license: MIT
		http://www.jacklmoore.com/autosize
	*/
	(function (global, factory) {
		if (true) {
			!(__WEBPACK_AMD_DEFINE_ARRAY__ = [exports, module], __WEBPACK_AMD_DEFINE_FACTORY__ = (factory), __WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ? (__WEBPACK_AMD_DEFINE_FACTORY__.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__)) : __WEBPACK_AMD_DEFINE_FACTORY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
		} else if (typeof exports !== 'undefined' && typeof module !== 'undefined') {
			factory(exports, module);
		} else {
			var mod = {
				exports: {}
			};
			factory(mod.exports, mod);
			global.autosize = mod.exports;
		}
	})(undefined, function (exports, module) {
		'use strict';
	
		var set = typeof Set === 'function' ? new Set() : function () {
			var list = [];
	
			return {
				has: function has(key) {
					return Boolean(list.indexOf(key) > -1);
				},
				add: function add(key) {
					list.push(key);
				},
				'delete': function _delete(key) {
					list.splice(list.indexOf(key), 1);
				} };
		}();
	
		var createEvent = function createEvent(name) {
			return new Event(name);
		};
		try {
			new Event('test');
		} catch (e) {
			// IE does not support `new Event()`
			createEvent = function createEvent(name) {
				var evt = document.createEvent('Event');
				evt.initEvent(name, true, false);
				return evt;
			};
		}
	
		function assign(ta) {
			var _ref = arguments[1] === undefined ? {} : arguments[1];
	
			var _ref$setOverflowX = _ref.setOverflowX;
			var setOverflowX = _ref$setOverflowX === undefined ? true : _ref$setOverflowX;
			var _ref$setOverflowY = _ref.setOverflowY;
			var setOverflowY = _ref$setOverflowY === undefined ? true : _ref$setOverflowY;
	
			if (!ta || !ta.nodeName || ta.nodeName !== 'TEXTAREA' || set.has(ta)) return;
	
			var heightOffset = null;
			var overflowY = null;
			var clientWidth = ta.clientWidth;
	
			function init() {
				var style = window.getComputedStyle(ta, null);
	
				overflowY = style.overflowY;
	
				if (style.resize === 'vertical') {
					ta.style.resize = 'none';
				} else if (style.resize === 'both') {
					ta.style.resize = 'horizontal';
				}
	
				if (style.boxSizing === 'content-box') {
					heightOffset = -(parseFloat(style.paddingTop) + parseFloat(style.paddingBottom));
				} else {
					heightOffset = parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth);
				}
				// Fix when a textarea is not on document body and heightOffset is Not a Number
				if (isNaN(heightOffset)) {
					heightOffset = 0;
				}
	
				update();
			}
	
			function changeOverflow(value) {
				{
					// Chrome/Safari-specific fix:
					// When the textarea y-overflow is hidden, Chrome/Safari do not reflow the text to account for the space
					// made available by removing the scrollbar. The following forces the necessary text reflow.
					var width = ta.style.width;
					ta.style.width = '0px';
					// Force reflow:
					/* jshint ignore:start */
					ta.offsetWidth;
					/* jshint ignore:end */
					ta.style.width = width;
				}
	
				overflowY = value;
	
				if (setOverflowY) {
					ta.style.overflowY = value;
				}
	
				resize();
			}
	
			function resize() {
				var htmlTop = window.pageYOffset;
				var bodyTop = document.body.scrollTop;
				var originalHeight = ta.style.height;
	
				ta.style.height = 'auto';
	
				var endHeight = ta.scrollHeight + heightOffset;
	
				if (ta.scrollHeight === 0) {
					// If the scrollHeight is 0, then the element probably has display:none or is detached from the DOM.
					ta.style.height = originalHeight;
					return;
				}
	
				ta.style.height = endHeight + 'px';
	
				// used to check if an update is actually necessary on window.resize
				clientWidth = ta.clientWidth;
	
				// prevents scroll-position jumping
				document.documentElement.scrollTop = htmlTop;
				document.body.scrollTop = bodyTop;
			}
	
			function update() {
				var startHeight = ta.style.height;
	
				resize();
	
				var style = window.getComputedStyle(ta, null);
	
				if (style.height !== ta.style.height) {
					if (overflowY !== 'visible') {
						changeOverflow('visible');
					}
				} else {
					if (overflowY !== 'hidden') {
						changeOverflow('hidden');
					}
				}
	
				if (startHeight !== ta.style.height) {
					var evt = createEvent('autosize:resized');
					ta.dispatchEvent(evt);
				}
			}
	
			var pageResize = function pageResize() {
				if (ta.clientWidth !== clientWidth) {
					update();
				}
			};
	
			var destroy = function (style) {
				window.removeEventListener('resize', pageResize, false);
				ta.removeEventListener('input', update, false);
				ta.removeEventListener('keyup', update, false);
				ta.removeEventListener('autosize:destroy', destroy, false);
				ta.removeEventListener('autosize:update', update, false);
				set['delete'](ta);
	
				Object.keys(style).forEach(function (key) {
					ta.style[key] = style[key];
				});
			}.bind(ta, {
				height: ta.style.height,
				resize: ta.style.resize,
				overflowY: ta.style.overflowY,
				overflowX: ta.style.overflowX,
				wordWrap: ta.style.wordWrap });
	
			ta.addEventListener('autosize:destroy', destroy, false);
	
			// IE9 does not fire onpropertychange or oninput for deletions,
			// so binding to onkeyup to catch most of those events.
			// There is no way that I know of to detect something like 'cut' in IE9.
			if ('onpropertychange' in ta && 'oninput' in ta) {
				ta.addEventListener('keyup', update, false);
			}
	
			window.addEventListener('resize', pageResize, false);
			ta.addEventListener('input', update, false);
			ta.addEventListener('autosize:update', update, false);
			set.add(ta);
	
			if (setOverflowX) {
				ta.style.overflowX = 'hidden';
				ta.style.wordWrap = 'break-word';
			}
	
			init();
		}
	
		function destroy(ta) {
			if (!(ta && ta.nodeName && ta.nodeName === 'TEXTAREA')) return;
			var evt = createEvent('autosize:destroy');
			ta.dispatchEvent(evt);
		}
	
		function update(ta) {
			if (!(ta && ta.nodeName && ta.nodeName === 'TEXTAREA')) return;
			var evt = createEvent('autosize:update');
			ta.dispatchEvent(evt);
		}
	
		var autosize = null;
	
		// Do nothing in Node.js environment and IE8 (or lower)
		if (typeof window === 'undefined' || typeof window.getComputedStyle !== 'function') {
			autosize = function autosize(el) {
				return el;
			};
			autosize.destroy = function (el) {
				return el;
			};
			autosize.update = function (el) {
				return el;
			};
		} else {
			autosize = function autosize(el, options) {
				if (el) {
					Array.prototype.forEach.call(el.length ? el : [el], function (x) {
						return assign(x, options);
					});
				}
				return el;
			};
			autosize.destroy = function (el) {
				if (el) {
					Array.prototype.forEach.call(el.length ? el : [el], destroy);
				}
				return el;
			};
			autosize.update = function (el) {
				if (el) {
					Array.prototype.forEach.call(el.length ? el : [el], update);
				}
				return el;
			};
		}
	
		module.exports = autosize;
	});

/***/ },
/* 5 */
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;'use strict';
	
	var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol ? "symbol" : typeof obj; };
	
	/*!
	 * jQuery Cookie Plugin v1.4.1
	 * https://github.com/carhartl/jquery-cookie
	 *
	 * Copyright 2006, 2014 Klaus Hartl
	 * Released under the MIT license
	 */
	(function (factory) {
		if (true) {
			// AMD
			!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2)], __WEBPACK_AMD_DEFINE_FACTORY__ = (factory), __WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ? (__WEBPACK_AMD_DEFINE_FACTORY__.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__)) : __WEBPACK_AMD_DEFINE_FACTORY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
		} else if ((typeof exports === 'undefined' ? 'undefined' : _typeof(exports)) === 'object') {
			// CommonJS
			factory(require('jquery'));
		} else {
			// Browser globals
			factory(jQuery);
		}
	})(function ($) {
	
		var pluses = /\+/g;
	
		function encode(s) {
			return config.raw ? s : encodeURIComponent(s);
		}
	
		function decode(s) {
			return config.raw ? s : decodeURIComponent(s);
		}
	
		function stringifyCookieValue(value) {
			return encode(config.json ? JSON.stringify(value) : String(value));
		}
	
		function parseCookieValue(s) {
			if (s.indexOf('"') === 0) {
				// This is a quoted cookie as according to RFC2068, unescape...
				s = s.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, '\\');
			}
	
			try {
				// Replace server-side written pluses with spaces.
				// If we can't decode the cookie, ignore it, it's unusable.
				// If we can't parse the cookie, ignore it, it's unusable.
				s = decodeURIComponent(s.replace(pluses, ' '));
				return config.json ? JSON.parse(s) : s;
			} catch (e) {}
		}
	
		function read(s, converter) {
			var value = config.raw ? s : parseCookieValue(s);
			return $.isFunction(converter) ? converter(value) : value;
		}
	
		var config = $.cookie = function (key, value, options) {
	
			// Write
	
			if (arguments.length > 1 && !$.isFunction(value)) {
				options = $.extend({}, config.defaults, options);
	
				if (typeof options.expires === 'number') {
					var days = options.expires,
					    t = options.expires = new Date();
					t.setTime(+t + days * 864e+5);
				}
	
				return document.cookie = [encode(key), '=', stringifyCookieValue(value), options.expires ? '; expires=' + options.expires.toUTCString() : '', // use expires attribute, max-age is not supported by IE
				options.path ? '; path=' + options.path : '', options.domain ? '; domain=' + options.domain : '', options.secure ? '; secure' : ''].join('');
			}
	
			// Read
	
			var result = key ? undefined : {};
	
			// To prevent the for loop in the first place assign an empty array
			// in case there are no cookies at all. Also prevents odd result when
			// calling $.cookie().
			var cookies = document.cookie ? document.cookie.split('; ') : [];
	
			for (var i = 0, l = cookies.length; i < l; i++) {
				var parts = cookies[i].split('=');
				var name = decode(parts.shift());
				var cookie = parts.join('=');
	
				if (key && key === name) {
					// If second argument (value) is a function it's a converter...
					result = read(cookie, value);
					break;
				}
	
				// Prevent storing a cookie that we couldn't decode.
				if (!key && (cookie = read(cookie)) !== undefined) {
					result[name] = cookie;
				}
			}
	
			return result;
		};
	
		config.defaults = {};
	
		$.removeCookie = function (key, options) {
			if ($.cookie(key) === undefined) {
				return false;
			}
	
			// Must not alter options, thus extending a fresh object...
			$.cookie(key, '', $.extend({}, options, { expires: -1 }));
			return !$.cookie(key);
		};
	});

/***/ },
/* 6 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function(jQuery) {'use strict';
	
	/**
	 * jQuery Formset 1.2
	 * @author Stanislaus Madueke (stan DOT madueke AT gmail DOT com)
	 * @requires jQuery 1.2.6 or later
	 *
	 * Copyright (c) 2009, Stanislaus Madueke
	 * All rights reserved.
	 *
	 * Licensed under the New BSD License
	 * See: http://www.opensource.org/licenses/bsd-license.php
	 */
	(function ($) {
	    $.fn.formset = function (opts) {
	        var options = $.extend({}, $.fn.formset.defaults, opts),
	            flatExtraClasses = options.extraClasses.join(' '),
	            $$ = $(this),
	            applyExtraClasses = function applyExtraClasses(row, ndx) {
	            if (options.extraClasses) {
	                row.removeClass(flatExtraClasses);
	                row.addClass(options.extraClasses[ndx % options.extraClasses.length]);
	            }
	        },
	            updateElementIndex = function updateElementIndex(elem, prefix, ndx) {
	            var idRegex = new RegExp('(' + prefix + '-\\d+-)|(^)'),
	                replacement = prefix + '-' + ndx + '-';
	            if (elem.attr("for")) elem.attr("for", elem.attr("for").replace(idRegex, replacement));
	            if (elem.attr('id')) elem.attr('id', elem.attr('id').replace(idRegex, replacement));
	            if (elem.attr('name')) elem.attr('name', elem.attr('name').replace(idRegex, replacement));
	        },
	            hasChildElements = function hasChildElements(row) {
	            return row.find('input,select,textarea,label').length > 0;
	        },
	            insertDeleteLink = function insertDeleteLink(row) {
	            if (row.is('TR')) {
	                // If the forms are laid out in table rows, insert
	                // the remove button into the last table cell:
	                row.children(':last').append('<a class="' + options.deleteCssClass + '" href="javascript:void(0)">' + options.deleteText + '</a>');
	            } else if (row.is('UL') || row.is('OL')) {
	                // If they're laid out as an ordered/unordered list,
	                // insert an <li> after the last list item:
	                row.append('<li><a class="' + options.deleteCssClass + '" href="javascript:void(0)">' + options.deleteText + '</a></li>');
	            } else {
	                // Otherwise, just insert the remove button as the
	                // last child element of the form's container:
	                row.append('<a class="' + options.deleteCssClass + '" href="javascript:void(0)">' + options.deleteText + '</a>');
	            }
	            row.find('a.' + options.deleteCssClass).click(function () {
	                var row = $(this).parents('.' + options.formCssClass),
	                    del = row.find('input:hidden[id $= "-DELETE"]');
	                if (del.length) {
	                    // We're dealing with an inline formset; rather than remove
	                    // this form from the DOM, we'll mark it as deleted and hide
	                    // it, then let Django handle the deleting:
	                    del.val('on');
	                    row.hide();
	                } else {
	                    row.remove();
	                    // Update the TOTAL_FORMS form count.
	                    // Also update names and IDs for all remaining form controls so they remain in sequence:
	                    var forms = $('.' + options.formCssClass).not('.formset-custom-template');
	                    $('#id_' + options.prefix + '-TOTAL_FORMS').val(forms.length);
	                    for (var i = 0, formCount = forms.length; i < formCount; i++) {
	                        applyExtraClasses(forms.eq(i), i);
	                        forms.eq(i).find('input,select,textarea,label').each(function () {
	                            updateElementIndex($(this), options.prefix, i);
	                        });
	                    }
	                }
	                // If a post-delete callback was provided, call it with the deleted form:
	                if (options.removed) options.removed(row);
	                return false;
	            });
	        };
	
	        $$.each(function (i) {
	            var row = $(this),
	                del = row.find('input:checkbox[id $= "-DELETE"]');
	            if (del.length) {
	                // If you specify "can_delete = True" when creating an inline formset,
	                // Django adds a checkbox to each form in the formset.
	                // Replace the default checkbox with a hidden field:
	                del.before('<input type="hidden" name="' + del.attr('name') + '" id="' + del.attr('id') + '" />');
	                del.remove();
	            }
	            if (hasChildElements(row)) {
	                insertDeleteLink(row);
	                row.addClass(options.formCssClass);
	                applyExtraClasses(row, i);
	            }
	        });
	
	        if ($$.length) {
	            var addButton, template;
	            if (options.formTemplate) {
	                // If a form template was specified, we'll clone it to generate new form instances:
	                template = options.formTemplate instanceof $ ? options.formTemplate : $(options.formTemplate);
	                template.removeAttr('id').addClass(options.formCssClass).addClass('formset-custom-template');
	                template.find('input,select,textarea,label').each(function () {
	                    updateElementIndex($(this), options.prefix, 2012);
	                });
	                insertDeleteLink(template);
	            } else {
	                // Otherwise, use the last form in the formset; this works much better if you've got
	                // extra (>= 1) forms (thnaks to justhamade for pointing this out):
	                template = $('.' + options.formCssClass + ':last').clone(true).removeAttr('id');
	                template.find('input:hidden[id $= "-DELETE"]').remove();
	                template.find('input,select,textarea,label').each(function () {
	                    var elem = $(this);
	                    // If this is a checkbox or radiobutton, uncheck it.
	                    // This fixes Issue 1, reported by Wilson.Andrew.J:
	                    if (elem.is('input:checkbox') || elem.is('input:radio')) {
	                        elem.attr('checked', false);
	                    } else {
	                        elem.val('');
	                    }
	                });
	            }
	            // FIXME: Perhaps using $.data would be a better idea?
	            options.formTemplate = template;
	
	            if ($$.attr('tagName') == 'TR') {
	                // If forms are laid out as table rows, insert the
	                // "add" button in a new table row:
	                var numCols = $$.eq(0).children().length;
	                $$.parent().append('<tr><td colspan="' + numCols + '"><a class="' + options.addCssClass + '" href="javascript:void(0)">' + options.addText + '</a></tr>');
	                addButton = $$.parent().find('tr:last a');
	                addButton.parents('tr').addClass(options.formCssClass + '-add');
	            } else {
	                // Otherwise, insert it immediately after the last form:
	                $$.filter(':last').after('<a class="' + options.addCssClass + '" href="javascript:void(0)">' + options.addText + '</a>');
	                addButton = $$.filter(':last').next();
	            }
	            addButton.click(function () {
	                var formCount = parseInt($('#id_' + options.prefix + '-TOTAL_FORMS').val()),
	                    row = options.formTemplate.clone(true).removeClass('formset-custom-template'),
	                    buttonRow = $(this).parents('tr.' + options.formCssClass + '-add').get(0) || this;
	                applyExtraClasses(row, formCount);
	                row.insertBefore($(buttonRow)).show();
	                row.find('input,select,textarea,label').each(function () {
	                    updateElementIndex($(this), options.prefix, formCount);
	                });
	                $('#id_' + options.prefix + '-TOTAL_FORMS').val(formCount + 1);
	                // If a post-add callback was supplied, call it with the added form:
	                if (options.added) options.added(row);
	                return false;
	            });
	        }
	
	        return $$;
	    };
	
	    /* Setup plugin defaults */
	    $.fn.formset.defaults = {
	        prefix: 'form', // The form prefix for your django formset
	        formTemplate: null, // The jQuery selection cloned to generate new form instances
	        addText: '<br />add another', // Text for the add link
	        deleteText: 'remove', // Text for the delete link
	        addCssClass: 'add-row', // CSS class applied to the add link
	        deleteCssClass: 'delete-row', // CSS class applied to the delete link
	        formCssClass: 'dynamic-form', // CSS class applied to each form in a formset
	        extraClasses: [], // Additional CSS classes, which will be applied to each form in turn
	        added: null, // Function called each time a new form is added
	        removed: null // Function called each time a form is deleted
	    };
	})(jQuery);
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 7 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function(jQuery) {'use strict';
	
	/**
	 * Loupe: a jQuery image magnifier
	 * (C) 2010 Joe Bartlett, MIT license
	 * http://redoPop.com/loupe
	 */
	(function ($) {
		$.fn.loupe = function (arg) {
			var options = $.extend({
				loupe: 'loupe',
				width: 200,
				height: 150
			}, arg || {});
	
			return this.length ? this.each(function () {
				var $this = $(this),
				    $big,
				    $loupe,
				    $small = $this.is('img') ? $this : $this.find('img:first'),
				    isTouched,
				    isUntouched,
				    time;
	
				if ($this.data('loupe') != null) {
					return $this.data('loupe', arg);
				}
	
				function onTouchStart() {
					isTouched = true;
				}
	
				function onPointerDown(event) {
					if (event.pointerType === 'touch') {
						onTouchStart();
					}
				}
	
				function hide() {
					isTouched = false;
					isUntouched = false;
					$loupe.hide();
				}
	
				function move(e) {
					var os = $small.offset(),
					    sW = $small.outerWidth(),
					    sH = $small.outerHeight(),
					    oW = options.width / 2,
					    oH = options.height / 2;
	
					// Ignore the first movement event -- it could be
					// a simulated mouse event! (Thanks, Android!)
					if (!isUntouched) {
						isUntouched = true;
						return;
					}
	
					if (isTouched || !$this.data('loupe') || e.pageX > sW + os.left + 10 || e.pageX < os.left - 10 || e.pageY > sH + os.top + 10 || e.pageY < os.top - 10) {
						return hide();
					}
	
					time = time ? clearTimeout(time) : 0;
	
					$loupe.show().css({
						left: e.pageX - oW,
						top: e.pageY - oH
					});
					$big.css({
						left: -((e.pageX - os.left) / sW * $big.width() - oW) | 0,
						top: -((e.pageY - os.top) / sH * $big.height() - oH) | 0
					});
				}
	
				$loupe = $('<div />').addClass(options.loupe).css({
					width: options.width,
					height: options.height,
					position: 'absolute',
					overflow: 'hidden'
				}).append($big = $('<img />').attr('src', $this.attr($this.is('img') ? 'src' : 'href')).css('position', 'absolute')).mousemove(move).mouseleave(hide).hide().appendTo('body');
	
				$this
				// Prevent touch screens from triggering the loupe
				.on('touchstart', onTouchStart)
	
				// https://gist.github.com/redoPop/9050999cebcd7e50934a
				.on('pointerdown', onPointerDown).on('MSPointerDown', onPointerDown).data('loupe', true).mousemove(move).mouseout(function () {
					time = setTimeout(hide, 10);
				});
			}) : this;
		};
	})(jQuery);
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 8 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function(__webpack_provided_window_dot_jQuery) {'use strict';
	
	var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol ? "symbol" : typeof obj; };
	
	/*
	* MultiSelect v0.9.11
	* Copyright (c) 2012 Louis Cuny
	*
	* This program is free software. It comes without any warranty, to
	* the extent permitted by applicable law. You can redistribute it
	* and/or modify it under the terms of the Do What The Fuck You Want
	* To Public License, Version 2, as published by Sam Hocevar. See
	* http://sam.zoy.org/wtfpl/COPYING for more details.
	*/
	
	!function ($) {
	
	  "use strict";
	
	  /* MULTISELECT CLASS DEFINITION
	   * ====================== */
	
	  var MultiSelect = function MultiSelect(element, options) {
	    this.options = options;
	    this.$element = $(element);
	    this.$container = $('<div/>', { 'class': "ms-container" });
	    this.$selectableContainer = $('<div/>', { 'class': 'ms-selectable' });
	    this.$selectionContainer = $('<div/>', { 'class': 'ms-selection' });
	    this.$selectableUl = $('<ul/>', { 'class': "ms-list", 'tabindex': '-1' });
	    this.$selectionUl = $('<ul/>', { 'class': "ms-list", 'tabindex': '-1' });
	    this.scrollTo = 0;
	    this.elemsSelector = 'li:visible:not(.ms-optgroup-label,.ms-optgroup-container,.' + options.disabledClass + ')';
	  };
	
	  MultiSelect.prototype = {
	    constructor: MultiSelect,
	
	    init: function init() {
	      var that = this,
	          ms = this.$element;
	
	      if (ms.next('.ms-container').length === 0) {
	        ms.css({ position: 'absolute', left: '-9999px' });
	        ms.attr('id', ms.attr('id') ? ms.attr('id') : Math.ceil(Math.random() * 1000) + 'multiselect');
	        this.$container.attr('id', 'ms-' + ms.attr('id'));
	        this.$container.addClass(that.options.cssClass);
	        ms.find('option').each(function () {
	          that.generateLisFromOption(this);
	        });
	
	        this.$selectionUl.find('.ms-optgroup-label').hide();
	
	        if (that.options.selectableHeader) {
	          that.$selectableContainer.append(that.options.selectableHeader);
	        }
	        that.$selectableContainer.append(that.$selectableUl);
	        if (that.options.selectableFooter) {
	          that.$selectableContainer.append(that.options.selectableFooter);
	        }
	
	        if (that.options.selectionHeader) {
	          that.$selectionContainer.append(that.options.selectionHeader);
	        }
	        that.$selectionContainer.append(that.$selectionUl);
	        if (that.options.selectionFooter) {
	          that.$selectionContainer.append(that.options.selectionFooter);
	        }
	
	        that.$container.append(that.$selectableContainer);
	        that.$container.append(that.$selectionContainer);
	        ms.after(that.$container);
	
	        that.activeMouse(that.$selectableUl);
	        that.activeKeyboard(that.$selectableUl);
	
	        var action = that.options.dblClick ? 'dblclick' : 'click';
	
	        that.$selectableUl.on(action, '.ms-elem-selectable', function () {
	          that.select($(this).data('ms-value'));
	        });
	        that.$selectionUl.on(action, '.ms-elem-selection', function () {
	          that.deselect($(this).data('ms-value'));
	        });
	
	        that.activeMouse(that.$selectionUl);
	        that.activeKeyboard(that.$selectionUl);
	
	        ms.on('focus', function () {
	          that.$selectableUl.focus();
	        });
	      }
	
	      var selectedValues = ms.find('option:selected').map(function () {
	        return $(this).val();
	      }).get();
	      that.select(selectedValues, 'init');
	
	      if (typeof that.options.afterInit === 'function') {
	        that.options.afterInit.call(this, this.$container);
	      }
	    },
	
	    'generateLisFromOption': function generateLisFromOption(option, index, $container) {
	      var that = this,
	          ms = that.$element,
	          attributes = "",
	          $option = $(option);
	
	      for (var cpt = 0; cpt < option.attributes.length; cpt++) {
	        var attr = option.attributes[cpt];
	
	        if (attr.name !== 'value' && attr.name !== 'disabled') {
	          attributes += attr.name + '="' + attr.value + '" ';
	        }
	      }
	      var selectableLi = $('<li ' + attributes + '><span>' + that.escapeHTML($option.text()) + '</span></li>'),
	          selectedLi = selectableLi.clone(),
	          value = $option.val(),
	          elementId = that.sanitize(value);
	
	      selectableLi.data('ms-value', value).addClass('ms-elem-selectable').attr('id', elementId + '-selectable');
	
	      selectedLi.data('ms-value', value).addClass('ms-elem-selection').attr('id', elementId + '-selection').hide();
	
	      if ($option.prop('disabled') || ms.prop('disabled')) {
	        selectedLi.addClass(that.options.disabledClass);
	        selectableLi.addClass(that.options.disabledClass);
	      }
	
	      var $optgroup = $option.parent('optgroup');
	
	      if ($optgroup.length > 0) {
	        var optgroupLabel = $optgroup.attr('label'),
	            optgroupId = that.sanitize(optgroupLabel),
	            $selectableOptgroup = that.$selectableUl.find('#optgroup-selectable-' + optgroupId),
	            $selectionOptgroup = that.$selectionUl.find('#optgroup-selection-' + optgroupId);
	
	        if ($selectableOptgroup.length === 0) {
	          var optgroupContainerTpl = '<li class="ms-optgroup-container"></li>',
	              optgroupTpl = '<ul class="ms-optgroup"><li class="ms-optgroup-label"><span>' + optgroupLabel + '</span></li></ul>';
	
	          $selectableOptgroup = $(optgroupContainerTpl);
	          $selectionOptgroup = $(optgroupContainerTpl);
	          $selectableOptgroup.attr('id', 'optgroup-selectable-' + optgroupId);
	          $selectionOptgroup.attr('id', 'optgroup-selection-' + optgroupId);
	          $selectableOptgroup.append($(optgroupTpl));
	          $selectionOptgroup.append($(optgroupTpl));
	          if (that.options.selectableOptgroup) {
	            $selectableOptgroup.find('.ms-optgroup-label').on('click', function () {
	              var values = $optgroup.children(':not(:selected, :disabled)').map(function () {
	                return $(this).val();
	              }).get();
	              that.select(values);
	            });
	            $selectionOptgroup.find('.ms-optgroup-label').on('click', function () {
	              var values = $optgroup.children(':selected:not(:disabled)').map(function () {
	                return $(this).val();
	              }).get();
	              that.deselect(values);
	            });
	          }
	          that.$selectableUl.append($selectableOptgroup);
	          that.$selectionUl.append($selectionOptgroup);
	        }
	        index = index == undefined ? $selectableOptgroup.find('ul').children().length : index + 1;
	        selectableLi.insertAt(index, $selectableOptgroup.children());
	        selectedLi.insertAt(index, $selectionOptgroup.children());
	      } else {
	        index = index == undefined ? that.$selectableUl.children().length : index;
	
	        selectableLi.insertAt(index, that.$selectableUl);
	        selectedLi.insertAt(index, that.$selectionUl);
	      }
	    },
	
	    'addOption': function addOption(options) {
	      var that = this;
	
	      if (options.value) options = [options];
	      $.each(options, function (index, option) {
	        if (option.value && that.$element.find("option[value='" + option.value + "']").length === 0) {
	          var $option = $('<option value="' + option.value + '">' + option.text + '</option>'),
	              index = parseInt(typeof option.index === 'undefined' ? that.$element.children().length : option.index),
	              $container = option.nested == undefined ? that.$element : $("optgroup[label='" + option.nested + "']");
	
	          $option.insertAt(index, $container);
	          that.generateLisFromOption($option.get(0), index, option.nested);
	        }
	      });
	    },
	
	    'removeOption': function removeOption(options) {
	      var that = this;
	
	      if (options.value) options = [options];
	      $.each(options, function (index, option) {
	        if (option.value && that.$element.find("option[value='" + option.value + "']").length === 1) {
	          that.$element.find("option[value='" + option.value + "']").remove();
	          that.$container.find("ul.ms-list [id^='" + option.value + "']").remove();
	        }
	      });
	    },
	
	    'escapeHTML': function escapeHTML(text) {
	      return $("<div>").text(text).html();
	    },
	
	    'activeKeyboard': function activeKeyboard($list) {
	      var that = this;
	
	      $list.on('focus', function () {
	        $(this).addClass('ms-focus');
	      }).on('blur', function () {
	        $(this).removeClass('ms-focus');
	      }).on('keydown', function (e) {
	        switch (e.which) {
	          case 40:
	          case 38:
	            e.preventDefault();
	            e.stopPropagation();
	            that.moveHighlight($(this), e.which === 38 ? -1 : 1);
	            return;
	          case 37:
	          case 39:
	            e.preventDefault();
	            e.stopPropagation();
	            that.switchList($list);
	            return;
	          case 9:
	            if (that.$element.is('[tabindex]')) {
	              e.preventDefault();
	              var tabindex = parseInt(that.$element.attr('tabindex'), 10);
	              tabindex = e.shiftKey ? tabindex - 1 : tabindex + 1;
	              $('[tabindex="' + tabindex + '"]').focus();
	              return;
	            } else {
	              if (e.shiftKey) {
	                that.$element.trigger('focus');
	              }
	            }
	        }
	        if ($.inArray(e.which, that.options.keySelect) > -1) {
	          e.preventDefault();
	          e.stopPropagation();
	          that.selectHighlighted($list);
	          return;
	        }
	      });
	    },
	
	    'moveHighlight': function moveHighlight($list, direction) {
	      var $elems = $list.find(this.elemsSelector),
	          $currElem = $elems.filter('.ms-hover'),
	          $nextElem = null,
	          elemHeight = $elems.first().outerHeight(),
	          containerHeight = $list.height(),
	          containerSelector = '#' + this.$container.prop('id');
	
	      $elems.removeClass('ms-hover');
	      if (direction === 1) {
	        // DOWN
	
	        $nextElem = $currElem.nextAll(this.elemsSelector).first();
	        if ($nextElem.length === 0) {
	          var $optgroupUl = $currElem.parent();
	
	          if ($optgroupUl.hasClass('ms-optgroup')) {
	            var $optgroupLi = $optgroupUl.parent(),
	                $nextOptgroupLi = $optgroupLi.next(':visible');
	
	            if ($nextOptgroupLi.length > 0) {
	              $nextElem = $nextOptgroupLi.find(this.elemsSelector).first();
	            } else {
	              $nextElem = $elems.first();
	            }
	          } else {
	            $nextElem = $elems.first();
	          }
	        }
	      } else if (direction === -1) {
	        // UP
	
	        $nextElem = $currElem.prevAll(this.elemsSelector).first();
	        if ($nextElem.length === 0) {
	          var $optgroupUl = $currElem.parent();
	
	          if ($optgroupUl.hasClass('ms-optgroup')) {
	            var $optgroupLi = $optgroupUl.parent(),
	                $prevOptgroupLi = $optgroupLi.prev(':visible');
	
	            if ($prevOptgroupLi.length > 0) {
	              $nextElem = $prevOptgroupLi.find(this.elemsSelector).last();
	            } else {
	              $nextElem = $elems.last();
	            }
	          } else {
	            $nextElem = $elems.last();
	          }
	        }
	      }
	      if ($nextElem.length > 0) {
	        $nextElem.addClass('ms-hover');
	        var scrollTo = $list.scrollTop() + $nextElem.position().top - containerHeight / 2 + elemHeight / 2;
	
	        $list.scrollTop(scrollTo);
	      }
	    },
	
	    'selectHighlighted': function selectHighlighted($list) {
	      var $elems = $list.find(this.elemsSelector),
	          $highlightedElem = $elems.filter('.ms-hover').first();
	
	      if ($highlightedElem.length > 0) {
	        if ($list.parent().hasClass('ms-selectable')) {
	          this.select($highlightedElem.data('ms-value'));
	        } else {
	          this.deselect($highlightedElem.data('ms-value'));
	        }
	        $elems.removeClass('ms-hover');
	      }
	    },
	
	    'switchList': function switchList($list) {
	      $list.blur();
	      this.$container.find(this.elemsSelector).removeClass('ms-hover');
	      if ($list.parent().hasClass('ms-selectable')) {
	        this.$selectionUl.focus();
	      } else {
	        this.$selectableUl.focus();
	      }
	    },
	
	    'activeMouse': function activeMouse($list) {
	      var that = this;
	
	      $('body').on('mouseenter', that.elemsSelector, function () {
	        $(this).parents('.ms-container').find(that.elemsSelector).removeClass('ms-hover');
	        $(this).addClass('ms-hover');
	      });
	
	      $('body').on('mouseleave', that.elemsSelector, function () {
	        $(this).parents('.ms-container').find(that.elemsSelector).removeClass('ms-hover');;
	      });
	    },
	
	    'refresh': function refresh() {
	      this.destroy();
	      this.$element.multiSelect(this.options);
	    },
	
	    'destroy': function destroy() {
	      $("#ms-" + this.$element.attr("id")).remove();
	      this.$element.css('position', '').css('left', '');
	      this.$element.removeData('multiselect');
	    },
	
	    'select': function select(value, method) {
	      if (typeof value === 'string') {
	        value = [value];
	      }
	
	      var that = this,
	          ms = this.$element,
	          msIds = $.map(value, function (val) {
	        return that.sanitize(val);
	      }),
	          selectables = this.$selectableUl.find('#' + msIds.join('-selectable, #') + '-selectable').filter(':not(.' + that.options.disabledClass + ')'),
	          selections = this.$selectionUl.find('#' + msIds.join('-selection, #') + '-selection').filter(':not(.' + that.options.disabledClass + ')'),
	          options = ms.find('option:not(:disabled)').filter(function () {
	        return $.inArray(this.value, value) > -1;
	      });
	
	      if (method === 'init') {
	        selectables = this.$selectableUl.find('#' + msIds.join('-selectable, #') + '-selectable'), selections = this.$selectionUl.find('#' + msIds.join('-selection, #') + '-selection');
	      }
	
	      if (selectables.length > 0) {
	        selectables.addClass('ms-selected').hide();
	        selections.addClass('ms-selected').show();
	
	        options.prop('selected', true);
	
	        that.$container.find(that.elemsSelector).removeClass('ms-hover');
	
	        var selectableOptgroups = that.$selectableUl.children('.ms-optgroup-container');
	        if (selectableOptgroups.length > 0) {
	          selectableOptgroups.each(function () {
	            var selectablesLi = $(this).find('.ms-elem-selectable');
	            if (selectablesLi.length === selectablesLi.filter('.ms-selected').length) {
	              $(this).find('.ms-optgroup-label').hide();
	            }
	          });
	
	          var selectionOptgroups = that.$selectionUl.children('.ms-optgroup-container');
	          selectionOptgroups.each(function () {
	            var selectionsLi = $(this).find('.ms-elem-selection');
	            if (selectionsLi.filter('.ms-selected').length > 0) {
	              $(this).find('.ms-optgroup-label').show();
	            }
	          });
	        } else {
	          if (that.options.keepOrder && method !== 'init') {
	            var selectionLiLast = that.$selectionUl.find('.ms-selected');
	            if (selectionLiLast.length > 1 && selectionLiLast.last().get(0) != selections.get(0)) {
	              selections.insertAfter(selectionLiLast.last());
	            }
	          }
	        }
	        if (method !== 'init') {
	          ms.trigger('change');
	          if (typeof that.options.afterSelect === 'function') {
	            that.options.afterSelect.call(this, value);
	          }
	        }
	      }
	    },
	
	    'deselect': function deselect(value) {
	      if (typeof value === 'string') {
	        value = [value];
	      }
	
	      var that = this,
	          ms = this.$element,
	          msIds = $.map(value, function (val) {
	        return that.sanitize(val);
	      }),
	          selectables = this.$selectableUl.find('#' + msIds.join('-selectable, #') + '-selectable'),
	          selections = this.$selectionUl.find('#' + msIds.join('-selection, #') + '-selection').filter('.ms-selected').filter(':not(.' + that.options.disabledClass + ')'),
	          options = ms.find('option').filter(function () {
	        return $.inArray(this.value, value) > -1;
	      });
	
	      if (selections.length > 0) {
	        selectables.removeClass('ms-selected').show();
	        selections.removeClass('ms-selected').hide();
	        options.prop('selected', false);
	
	        that.$container.find(that.elemsSelector).removeClass('ms-hover');
	
	        var selectableOptgroups = that.$selectableUl.children('.ms-optgroup-container');
	        if (selectableOptgroups.length > 0) {
	          selectableOptgroups.each(function () {
	            var selectablesLi = $(this).find('.ms-elem-selectable');
	            if (selectablesLi.filter(':not(.ms-selected)').length > 0) {
	              $(this).find('.ms-optgroup-label').show();
	            }
	          });
	
	          var selectionOptgroups = that.$selectionUl.children('.ms-optgroup-container');
	          selectionOptgroups.each(function () {
	            var selectionsLi = $(this).find('.ms-elem-selection');
	            if (selectionsLi.filter('.ms-selected').length === 0) {
	              $(this).find('.ms-optgroup-label').hide();
	            }
	          });
	        }
	        ms.trigger('change');
	        if (typeof that.options.afterDeselect === 'function') {
	          that.options.afterDeselect.call(this, value);
	        }
	      }
	    },
	
	    'select_all': function select_all() {
	      var ms = this.$element,
	          values = ms.val();
	
	      ms.find('option:not(":disabled")').prop('selected', true);
	      this.$selectableUl.find('.ms-elem-selectable').filter(':not(.' + this.options.disabledClass + ')').addClass('ms-selected').hide();
	      this.$selectionUl.find('.ms-optgroup-label').show();
	      this.$selectableUl.find('.ms-optgroup-label').hide();
	      this.$selectionUl.find('.ms-elem-selection').filter(':not(.' + this.options.disabledClass + ')').addClass('ms-selected').show();
	      this.$selectionUl.focus();
	      ms.trigger('change');
	      if (typeof this.options.afterSelect === 'function') {
	        var selectedValues = $.grep(ms.val(), function (item) {
	          return $.inArray(item, values) < 0;
	        });
	        this.options.afterSelect.call(this, selectedValues);
	      }
	    },
	
	    'deselect_all': function deselect_all() {
	      var ms = this.$element,
	          values = ms.val();
	
	      ms.find('option').prop('selected', false);
	      this.$selectableUl.find('.ms-elem-selectable').removeClass('ms-selected').show();
	      this.$selectionUl.find('.ms-optgroup-label').hide();
	      this.$selectableUl.find('.ms-optgroup-label').show();
	      this.$selectionUl.find('.ms-elem-selection').removeClass('ms-selected').hide();
	      this.$selectableUl.focus();
	      ms.trigger('change');
	      if (typeof this.options.afterDeselect === 'function') {
	        this.options.afterDeselect.call(this, values);
	      }
	    },
	
	    sanitize: function sanitize(value) {
	      var hash = 0,
	          i,
	          character;
	      if (value.length == 0) return hash;
	      var ls = 0;
	      for (i = 0, ls = value.length; i < ls; i++) {
	        character = value.charCodeAt(i);
	        hash = (hash << 5) - hash + character;
	        hash |= 0; // Convert to 32bit integer
	      }
	      return hash;
	    }
	  };
	
	  /* MULTISELECT PLUGIN DEFINITION
	   * ======================= */
	
	  $.fn.multiSelect = function () {
	    var option = arguments[0],
	        args = arguments;
	
	    return this.each(function () {
	      var $this = $(this),
	          data = $this.data('multiselect'),
	          options = $.extend({}, $.fn.multiSelect.defaults, $this.data(), (typeof option === 'undefined' ? 'undefined' : _typeof(option)) === 'object' && option);
	
	      if (!data) {
	        $this.data('multiselect', data = new MultiSelect(this, options));
	      }
	
	      if (typeof option === 'string') {
	        data[option](args[1]);
	      } else {
	        data.init();
	      }
	    });
	  };
	
	  $.fn.multiSelect.defaults = {
	    keySelect: [32],
	    selectableOptgroup: false,
	    disabledClass: 'disabled',
	    dblClick: false,
	    keepOrder: false,
	    cssClass: ''
	  };
	
	  $.fn.multiSelect.Constructor = MultiSelect;
	
	  $.fn.insertAt = function (index, $parent) {
	    return this.each(function () {
	      if (index === 0) {
	        $parent.prepend(this);
	      } else {
	        $parent.children().eq(index - 1).after(this);
	      }
	    });
	  };
	}(__webpack_provided_window_dot_jQuery);
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 9 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function(__webpack_provided_window_dot_jQuery) {'use strict';
	
	var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol ? "symbol" : typeof obj; };
	
	/*! jQuery-QuickSearch - v2.2.0 - 2016-02-09
	* https://deuxhuithuit.github.io/quicksearch/
	* Copyright (c) 2016 Deux Huit Huit (https://deuxhuithuit.com/);
	* Licensed MIT http://deuxhuithuit.mit-license.org */
	/*! jQuery-QuickSearch - v2.0.2 - 2013-11-15
	* Copyright (c) 2013 Deux Huit Huit (https://deuxhuithuit.com/);
	* Licensed MIT http://deuxhuithuit.mit-license.org */
	/**
	 * Copyrights: Deux Huit Huit, Rik Lomas.
	 * Licensed MIT: http://deuxhuithuit.mit-license.org
	 */
	
	(function ($, window, document, undefined) {
		'use strict';
	
		$.quicksearch = {
			defaults: {
				delay: 100,
				selector: null,
				stripeRows: null,
				loader: null,
				noResults: '',
				matchedResultsCount: 0,
				bind: 'keyup search input',
				resetBind: 'reset',
				removeDiacritics: false,
				minValLength: 0,
				onBefore: $.noop,
				onAfter: $.noop,
				onValTooSmall: $.noop,
				onNoResultFound: null,
				show: function show() {
					$(this).show();
				},
				hide: function hide() {
					$(this).hide();
				},
				prepareQuery: function prepareQuery(val) {
					return val.toLowerCase().split(' ');
				},
				testQuery: function testQuery(query, txt, _row) {
					for (var i = 0; i < query.length; i += 1) {
						if (txt.indexOf(query[i]) === -1) {
							return false;
						}
					}
					return true;
				}
			},
			diacriticsRemovalMap: [{ 'base': 'A', 'letters': /[\u0041\u24B6\uFF21\u00C0\u00C1\u00C2\u1EA6\u1EA4\u1EAA\u1EA8\u00C3\u0100\u0102\u1EB0\u1EAE\u1EB4\u1EB2\u0226\u01E0\u00C4\u01DE\u1EA2\u00C5\u01FA\u01CD\u0200\u0202\u1EA0\u1EAC\u1EB6\u1E00\u0104\u023A\u2C6F]/g }, { 'base': 'AA', 'letters': /[\uA732]/g }, { 'base': 'AE', 'letters': /[\u00C6\u01FC\u01E2]/g }, { 'base': 'AO', 'letters': /[\uA734]/g }, { 'base': 'AU', 'letters': /[\uA736]/g }, { 'base': 'AV', 'letters': /[\uA738\uA73A]/g }, { 'base': 'AY', 'letters': /[\uA73C]/g }, { 'base': 'B', 'letters': /[\u0042\u24B7\uFF22\u1E02\u1E04\u1E06\u0243\u0182\u0181]/g }, { 'base': 'C', 'letters': /[\u0043\u24B8\uFF23\u0106\u0108\u010A\u010C\u00C7\u1E08\u0187\u023B\uA73E]/g }, { 'base': 'D', 'letters': /[\u0044\u24B9\uFF24\u1E0A\u010E\u1E0C\u1E10\u1E12\u1E0E\u0110\u018B\u018A\u0189\uA779]/g }, { 'base': 'DZ', 'letters': /[\u01F1\u01C4]/g }, { 'base': 'Dz', 'letters': /[\u01F2\u01C5]/g }, { 'base': 'E', 'letters': /[\u0045\u24BA\uFF25\u00C8\u00C9\u00CA\u1EC0\u1EBE\u1EC4\u1EC2\u1EBC\u0112\u1E14\u1E16\u0114\u0116\u00CB\u1EBA\u011A\u0204\u0206\u1EB8\u1EC6\u0228\u1E1C\u0118\u1E18\u1E1A\u0190\u018E]/g }, { 'base': 'F', 'letters': /[\u0046\u24BB\uFF26\u1E1E\u0191\uA77B]/g }, { 'base': 'G', 'letters': /[\u0047\u24BC\uFF27\u01F4\u011C\u1E20\u011E\u0120\u01E6\u0122\u01E4\u0193\uA7A0\uA77D\uA77E]/g }, { 'base': 'H', 'letters': /[\u0048\u24BD\uFF28\u0124\u1E22\u1E26\u021E\u1E24\u1E28\u1E2A\u0126\u2C67\u2C75\uA78D]/g }, { 'base': 'I', 'letters': /[\u0049\u24BE\uFF29\u00CC\u00CD\u00CE\u0128\u012A\u012C\u0130\u00CF\u1E2E\u1EC8\u01CF\u0208\u020A\u1ECA\u012E\u1E2C\u0197]/g }, { 'base': 'J', 'letters': /[\u004A\u24BF\uFF2A\u0134\u0248]/g }, { 'base': 'K', 'letters': /[\u004B\u24C0\uFF2B\u1E30\u01E8\u1E32\u0136\u1E34\u0198\u2C69\uA740\uA742\uA744\uA7A2]/g }, { 'base': 'L', 'letters': /[\u004C\u24C1\uFF2C\u013F\u0139\u013D\u1E36\u1E38\u013B\u1E3C\u1E3A\u0141\u023D\u2C62\u2C60\uA748\uA746\uA780]/g }, { 'base': 'LJ', 'letters': /[\u01C7]/g }, { 'base': 'Lj', 'letters': /[\u01C8]/g }, { 'base': 'M', 'letters': /[\u004D\u24C2\uFF2D\u1E3E\u1E40\u1E42\u2C6E\u019C]/g }, { 'base': 'N', 'letters': /[\u004E\u24C3\uFF2E\u01F8\u0143\u00D1\u1E44\u0147\u1E46\u0145\u1E4A\u1E48\u0220\u019D\uA790\uA7A4]/g }, { 'base': 'NJ', 'letters': /[\u01CA]/g }, { 'base': 'Nj', 'letters': /[\u01CB]/g }, { 'base': 'O', 'letters': /[\u004F\u24C4\uFF2F\u00D2\u00D3\u00D4\u1ED2\u1ED0\u1ED6\u1ED4\u00D5\u1E4C\u022C\u1E4E\u014C\u1E50\u1E52\u014E\u022E\u0230\u00D6\u022A\u1ECE\u0150\u01D1\u020C\u020E\u01A0\u1EDC\u1EDA\u1EE0\u1EDE\u1EE2\u1ECC\u1ED8\u01EA\u01EC\u00D8\u01FE\u0186\u019F\uA74A\uA74C]/g }, { 'base': 'OI', 'letters': /[\u01A2]/g }, { 'base': 'OO', 'letters': /[\uA74E]/g }, { 'base': 'OU', 'letters': /[\u0222]/g }, { 'base': 'P', 'letters': /[\u0050\u24C5\uFF30\u1E54\u1E56\u01A4\u2C63\uA750\uA752\uA754]/g }, { 'base': 'Q', 'letters': /[\u0051\u24C6\uFF31\uA756\uA758\u024A]/g }, { 'base': 'R', 'letters': /[\u0052\u24C7\uFF32\u0154\u1E58\u0158\u0210\u0212\u1E5A\u1E5C\u0156\u1E5E\u024C\u2C64\uA75A\uA7A6\uA782]/g }, { 'base': 'S', 'letters': /[\u0053\u24C8\uFF33\u1E9E\u015A\u1E64\u015C\u1E60\u0160\u1E66\u1E62\u1E68\u0218\u015E\u2C7E\uA7A8\uA784]/g }, { 'base': 'T', 'letters': /[\u0054\u24C9\uFF34\u1E6A\u0164\u1E6C\u021A\u0162\u1E70\u1E6E\u0166\u01AC\u01AE\u023E\uA786]/g }, { 'base': 'TZ', 'letters': /[\uA728]/g }, { 'base': 'U', 'letters': /[\u0055\u24CA\uFF35\u00D9\u00DA\u00DB\u0168\u1E78\u016A\u1E7A\u016C\u00DC\u01DB\u01D7\u01D5\u01D9\u1EE6\u016E\u0170\u01D3\u0214\u0216\u01AF\u1EEA\u1EE8\u1EEE\u1EEC\u1EF0\u1EE4\u1E72\u0172\u1E76\u1E74\u0244]/g }, { 'base': 'V', 'letters': /[\u0056\u24CB\uFF36\u1E7C\u1E7E\u01B2\uA75E\u0245]/g }, { 'base': 'VY', 'letters': /[\uA760]/g }, { 'base': 'W', 'letters': /[\u0057\u24CC\uFF37\u1E80\u1E82\u0174\u1E86\u1E84\u1E88\u2C72]/g }, { 'base': 'X', 'letters': /[\u0058\u24CD\uFF38\u1E8A\u1E8C]/g }, { 'base': 'Y', 'letters': /[\u0059\u24CE\uFF39\u1EF2\u00DD\u0176\u1EF8\u0232\u1E8E\u0178\u1EF6\u1EF4\u01B3\u024E\u1EFE]/g }, { 'base': 'Z', 'letters': /[\u005A\u24CF\uFF3A\u0179\u1E90\u017B\u017D\u1E92\u1E94\u01B5\u0224\u2C7F\u2C6B\uA762]/g }, { 'base': 'a', 'letters': /[\u0061\u24D0\uFF41\u1E9A\u00E0\u00E1\u00E2\u1EA7\u1EA5\u1EAB\u1EA9\u00E3\u0101\u0103\u1EB1\u1EAF\u1EB5\u1EB3\u0227\u01E1\u00E4\u01DF\u1EA3\u00E5\u01FB\u01CE\u0201\u0203\u1EA1\u1EAD\u1EB7\u1E01\u0105\u2C65\u0250]/g }, { 'base': 'aa', 'letters': /[\uA733]/g }, { 'base': 'ae', 'letters': /[\u00E6\u01FD\u01E3]/g }, { 'base': 'ao', 'letters': /[\uA735]/g }, { 'base': 'au', 'letters': /[\uA737]/g }, { 'base': 'av', 'letters': /[\uA739\uA73B]/g }, { 'base': 'ay', 'letters': /[\uA73D]/g }, { 'base': 'b', 'letters': /[\u0062\u24D1\uFF42\u1E03\u1E05\u1E07\u0180\u0183\u0253]/g }, { 'base': 'c', 'letters': /[\u0063\u24D2\uFF43\u0107\u0109\u010B\u010D\u00E7\u1E09\u0188\u023C\uA73F\u2184]/g }, { 'base': 'd', 'letters': /[\u0064\u24D3\uFF44\u1E0B\u010F\u1E0D\u1E11\u1E13\u1E0F\u0111\u018C\u0256\u0257\uA77A]/g }, { 'base': 'dz', 'letters': /[\u01F3\u01C6]/g }, { 'base': 'e', 'letters': /[\u0065\u24D4\uFF45\u00E8\u00E9\u00EA\u1EC1\u1EBF\u1EC5\u1EC3\u1EBD\u0113\u1E15\u1E17\u0115\u0117\u00EB\u1EBB\u011B\u0205\u0207\u1EB9\u1EC7\u0229\u1E1D\u0119\u1E19\u1E1B\u0247\u025B\u01DD]/g }, { 'base': 'f', 'letters': /[\u0066\u24D5\uFF46\u1E1F\u0192\uA77C]/g }, { 'base': 'g', 'letters': /[\u0067\u24D6\uFF47\u01F5\u011D\u1E21\u011F\u0121\u01E7\u0123\u01E5\u0260\uA7A1\u1D79\uA77F]/g }, { 'base': 'h', 'letters': /[\u0068\u24D7\uFF48\u0125\u1E23\u1E27\u021F\u1E25\u1E29\u1E2B\u1E96\u0127\u2C68\u2C76\u0265]/g }, { 'base': 'hv', 'letters': /[\u0195]/g }, { 'base': 'i', 'letters': /[\u0069\u24D8\uFF49\u00EC\u00ED\u00EE\u0129\u012B\u012D\u00EF\u1E2F\u1EC9\u01D0\u0209\u020B\u1ECB\u012F\u1E2D\u0268\u0131]/g }, { 'base': 'j', 'letters': /[\u006A\u24D9\uFF4A\u0135\u01F0\u0249]/g }, { 'base': 'k', 'letters': /[\u006B\u24DA\uFF4B\u1E31\u01E9\u1E33\u0137\u1E35\u0199\u2C6A\uA741\uA743\uA745\uA7A3]/g }, { 'base': 'l', 'letters': /[\u006C\u24DB\uFF4C\u0140\u013A\u013E\u1E37\u1E39\u013C\u1E3D\u1E3B\u017F\u0142\u019A\u026B\u2C61\uA749\uA781\uA747]/g }, { 'base': 'lj', 'letters': /[\u01C9]/g }, { 'base': 'm', 'letters': /[\u006D\u24DC\uFF4D\u1E3F\u1E41\u1E43\u0271\u026F]/g }, { 'base': 'n', 'letters': /[\u006E\u24DD\uFF4E\u01F9\u0144\u00F1\u1E45\u0148\u1E47\u0146\u1E4B\u1E49\u019E\u0272\u0149\uA791\uA7A5]/g }, { 'base': 'nj', 'letters': /[\u01CC]/g }, { 'base': 'o', 'letters': /[\u006F\u24DE\uFF4F\u00F2\u00F3\u00F4\u1ED3\u1ED1\u1ED7\u1ED5\u00F5\u1E4D\u022D\u1E4F\u014D\u1E51\u1E53\u014F\u022F\u0231\u00F6\u022B\u1ECF\u0151\u01D2\u020D\u020F\u01A1\u1EDD\u1EDB\u1EE1\u1EDF\u1EE3\u1ECD\u1ED9\u01EB\u01ED\u00F8\u01FF\u0254\uA74B\uA74D\u0275]/g }, { 'base': 'oi', 'letters': /[\u01A3]/g }, { 'base': 'ou', 'letters': /[\u0223]/g }, { 'base': 'oo', 'letters': /[\uA74F]/g }, { 'base': 'p', 'letters': /[\u0070\u24DF\uFF50\u1E55\u1E57\u01A5\u1D7D\uA751\uA753\uA755]/g }, { 'base': 'q', 'letters': /[\u0071\u24E0\uFF51\u024B\uA757\uA759]/g }, { 'base': 'r', 'letters': /[\u0072\u24E1\uFF52\u0155\u1E59\u0159\u0211\u0213\u1E5B\u1E5D\u0157\u1E5F\u024D\u027D\uA75B\uA7A7\uA783]/g }, { 'base': 's', 'letters': /[\u0073\u24E2\uFF53\u00DF\u015B\u1E65\u015D\u1E61\u0161\u1E67\u1E63\u1E69\u0219\u015F\u023F\uA7A9\uA785\u1E9B]/g }, { 'base': 't', 'letters': /[\u0074\u24E3\uFF54\u1E6B\u1E97\u0165\u1E6D\u021B\u0163\u1E71\u1E6F\u0167\u01AD\u0288\u2C66\uA787]/g }, { 'base': 'tz', 'letters': /[\uA729]/g }, { 'base': 'u', 'letters': /[\u0075\u24E4\uFF55\u00F9\u00FA\u00FB\u0169\u1E79\u016B\u1E7B\u016D\u00FC\u01DC\u01D8\u01D6\u01DA\u1EE7\u016F\u0171\u01D4\u0215\u0217\u01B0\u1EEB\u1EE9\u1EEF\u1EED\u1EF1\u1EE5\u1E73\u0173\u1E77\u1E75\u0289]/g }, { 'base': 'v', 'letters': /[\u0076\u24E5\uFF56\u1E7D\u1E7F\u028B\uA75F\u028C]/g }, { 'base': 'vy', 'letters': /[\uA761]/g }, { 'base': 'w', 'letters': /[\u0077\u24E6\uFF57\u1E81\u1E83\u0175\u1E87\u1E85\u1E98\u1E89\u2C73]/g }, { 'base': 'x', 'letters': /[\u0078\u24E7\uFF58\u1E8B\u1E8D]/g }, { 'base': 'y', 'letters': /[\u0079\u24E8\uFF59\u1EF3\u00FD\u0177\u1EF9\u0233\u1E8F\u00FF\u1EF7\u1E99\u1EF5\u01B4\u024F\u1EFF]/g }, { 'base': 'z', 'letters': /[\u007A\u24E9\uFF5A\u017A\u1E91\u017C\u017E\u1E93\u1E95\u01B6\u0225\u0240\u2C6C\uA763]/g }]
		};
	
		$.fn.quicksearch = function (target, opt) {
	
			this.removeDiacritics = function (str) {
				var changes = $.quicksearch.diacriticsRemovalMap;
				for (var i = 0; i < changes.length; i++) {
					str = str.replace(changes[i].letters, changes[i].base);
				}
				return str;
			};
	
			var timeout,
			    cache,
			    rowcache,
			    jq_results,
			    val = '',
			    last_val = '',
			    self = this,
			    options = $.extend({}, $.quicksearch.defaults, opt);
	
			// Assure selectors
			options.noResults = !options.noResults ? $() : $(options.noResults);
			options.loader = !options.loader ? $() : $(options.loader);
	
			this.go = function () {
	
				var i = 0,
				    len = 0,
				    numMatchedRows = 0,
				    noresults = true,
				    query,
				    val_empty = val.replace(' ', '').length === 0;
	
				if (options.removeDiacritics) {
					val = self.removeDiacritics(val);
				}
	
				query = options.prepareQuery(val);
	
				for (i = 0, len = rowcache.length; i < len; i++) {
					if (query.length > 0 && query[0].length < options.minValLength) {
						options.show.apply(rowcache[i]);
						noresults = false;
						numMatchedRows++;
					} else if (val_empty || options.testQuery(query, cache[i], rowcache[i])) {
						options.show.apply(rowcache[i]);
						noresults = false;
						numMatchedRows++;
					} else {
						options.hide.apply(rowcache[i]);
					}
				}
	
				if (noresults) {
					if ($.isFunction(options.onNoResultFound)) {
						options.onNoResultFound(this);
					} else {
						this.results(false);
					}
				} else {
					this.results(true);
					this.stripe();
				}
	
				this.matchedResultsCount = numMatchedRows;
				this.loader(false);
				options.onAfter.call(this);
				last_val = val;
				return this;
			};
	
			/*
	   * External API so that users can perform search programatically.
	   * */
			this.search = function (submittedVal) {
				val = submittedVal;
				self.trigger();
			};
	
			/*
	   * External API so that users can perform search programatically.
	   * */
			this.reset = function () {
				val = '';
				this.loader(true);
				options.onBefore.call(this);
				window.clearTimeout(timeout);
				timeout = window.setTimeout(function () {
					self.go();
				}, options.delay);
			};
	
			/*
	   * External API to get the number of matched results as seen in
	   * https://github.com/ruiz107/quicksearch/commit/f78dc440b42d95ce9caed1d087174dd4359982d6
	   * */
			this.currentMatchedResults = function () {
				return this.matchedResultsCount;
			};
	
			this.stripe = function () {
	
				if (_typeof(options.stripeRows) === "object" && options.stripeRows !== null) {
					var joined = options.stripeRows.join(' ');
					var stripeRows_length = options.stripeRows.length;
	
					jq_results.not(':hidden').each(function (i) {
						$(this).removeClass(joined).addClass(options.stripeRows[i % stripeRows_length]);
					});
				}
	
				return this;
			};
	
			this.strip_html = function (input) {
				var output = input.replace(new RegExp('<[^<]+\\>', 'g'), ' ');
				output = $.trim(output.toLowerCase());
				return output;
			};
	
			this.results = function (bool) {
				if (!!options.noResults.length) {
					options.noResults[bool ? 'hide' : 'show']();
				}
	
				return this;
			};
	
			this.loader = function (bool) {
				if (!!options.loader.length) {
					options.loader[bool ? 'show' : 'hide']();
				}
	
				return this;
			};
	
			this.cache = function (doRedraw) {
	
				doRedraw = typeof doRedraw === "undefined" ? true : doRedraw;
	
				jq_results = $(target).not(options.noResults);
	
				if (typeof options.selector === "string") {
					cache = jq_results.map(function () {
						return $(this).find(options.selector).map(function () {
							var temp = self.strip_html(this.innerHTML);
							return options.removeDiacritics ? self.removeDiacritics(temp) : temp;
						}).get().join(" ");
					});
				} else {
					cache = jq_results.map(function () {
						var temp = self.strip_html(this.innerHTML);
						return options.removeDiacritics ? self.removeDiacritics(temp) : temp;
					});
				}
	
				rowcache = jq_results.map(function () {
					return this;
				});
	
				/*
	    * Modified fix for sync-ing "val".
	    * Original fix https://github.com/michaellwest/quicksearch/commit/4ace4008d079298a01f97f885ba8fa956a9703d1
	    * */
				val = val || this.val() || "";
	
				if (doRedraw) {
					this.go();
				}
	
				return this;
			};
	
			this.trigger = function () {
				if (val.length < options.minValLength && val.length > last_val.length || val.length < options.minValLength - 1 && val.length < last_val.length) {
					options.onValTooSmall.call(this, val);
					self.go();
				} else {
					this.loader(true);
					options.onBefore.call(this);
					window.clearTimeout(timeout);
					timeout = window.setTimeout(function () {
						self.go();
					}, options.delay);
				}
	
				return this;
			};
	
			this.cache();
			this.results(true);
			this.stripe();
			this.loader(false);
	
			return this.each(function () {
				$(this).on(options.bind, function () {
					val = $(this).val();
					self.trigger();
				});
				$(this).on(options.resetBind, function () {
					val = '';
					self.reset();
				});
			});
		};
	})(__webpack_provided_window_dot_jQuery, undefined, document);
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 10 */
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;"use strict";
	
	var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol ? "symbol" : typeof obj; };
	
	/*! jQuery UI - v1.11.2 - 2014-11-30
	* http://jqueryui.com
	* Includes: core.js, datepicker.js
	* Copyright 2014 jQuery Foundation and other contributors; Licensed MIT */
	
	(function (factory) {
		if (true) {
	
			// AMD. Register as an anonymous module.
			!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2)], __WEBPACK_AMD_DEFINE_FACTORY__ = (factory), __WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ? (__WEBPACK_AMD_DEFINE_FACTORY__.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__)) : __WEBPACK_AMD_DEFINE_FACTORY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
		} else {
	
			// Browser globals
			factory(jQuery);
		}
	})(function ($) {
		/*!
	  * jQuery UI Core 1.11.2
	  * http://jqueryui.com
	  *
	  * Copyright 2014 jQuery Foundation and other contributors
	  * Released under the MIT license.
	  * http://jquery.org/license
	  *
	  * http://api.jqueryui.com/category/ui-core/
	  */
	
		// $.ui might exist from components with no dependencies, e.g., $.ui.position
		$.ui = $.ui || {};
	
		$.extend($.ui, {
			version: "1.11.2",
	
			keyCode: {
				BACKSPACE: 8,
				COMMA: 188,
				DELETE: 46,
				DOWN: 40,
				END: 35,
				ENTER: 13,
				ESCAPE: 27,
				HOME: 36,
				LEFT: 37,
				PAGE_DOWN: 34,
				PAGE_UP: 33,
				PERIOD: 190,
				RIGHT: 39,
				SPACE: 32,
				TAB: 9,
				UP: 38
			}
		});
	
		// plugins
		$.fn.extend({
			scrollParent: function scrollParent(includeHidden) {
				var position = this.css("position"),
				    excludeStaticParent = position === "absolute",
				    overflowRegex = includeHidden ? /(auto|scroll|hidden)/ : /(auto|scroll)/,
				    scrollParent = this.parents().filter(function () {
					var parent = $(this);
					if (excludeStaticParent && parent.css("position") === "static") {
						return false;
					}
					return overflowRegex.test(parent.css("overflow") + parent.css("overflow-y") + parent.css("overflow-x"));
				}).eq(0);
	
				return position === "fixed" || !scrollParent.length ? $(this[0].ownerDocument || document) : scrollParent;
			},
	
			uniqueId: function () {
				var uuid = 0;
	
				return function () {
					return this.each(function () {
						if (!this.id) {
							this.id = "ui-id-" + ++uuid;
						}
					});
				};
			}(),
	
			removeUniqueId: function removeUniqueId() {
				return this.each(function () {
					if (/^ui-id-\d+$/.test(this.id)) {
						$(this).removeAttr("id");
					}
				});
			}
		});
	
		// selectors
		function _focusable(element, isTabIndexNotNaN) {
			var map,
			    mapName,
			    img,
			    nodeName = element.nodeName.toLowerCase();
			if ("area" === nodeName) {
				map = element.parentNode;
				mapName = map.name;
				if (!element.href || !mapName || map.nodeName.toLowerCase() !== "map") {
					return false;
				}
				img = $("img[usemap='#" + mapName + "']")[0];
				return !!img && visible(img);
			}
			return (/input|select|textarea|button|object/.test(nodeName) ? !element.disabled : "a" === nodeName ? element.href || isTabIndexNotNaN : isTabIndexNotNaN) &&
			// the element and all of its ancestors must be visible
			visible(element);
		}
	
		function visible(element) {
			return $.expr.filters.visible(element) && !$(element).parents().addBack().filter(function () {
				return $.css(this, "visibility") === "hidden";
			}).length;
		}
	
		$.extend($.expr[":"], {
			data: $.expr.createPseudo ? $.expr.createPseudo(function (dataName) {
				return function (elem) {
					return !!$.data(elem, dataName);
				};
			}) :
			// support: jQuery <1.8
			function (elem, i, match) {
				return !!$.data(elem, match[3]);
			},
	
			focusable: function focusable(element) {
				return _focusable(element, !isNaN($.attr(element, "tabindex")));
			},
	
			tabbable: function tabbable(element) {
				var tabIndex = $.attr(element, "tabindex"),
				    isTabIndexNaN = isNaN(tabIndex);
				return (isTabIndexNaN || tabIndex >= 0) && _focusable(element, !isTabIndexNaN);
			}
		});
	
		// support: jQuery <1.8
		if (!$("<a>").outerWidth(1).jquery) {
			$.each(["Width", "Height"], function (i, name) {
				var side = name === "Width" ? ["Left", "Right"] : ["Top", "Bottom"],
				    type = name.toLowerCase(),
				    orig = {
					innerWidth: $.fn.innerWidth,
					innerHeight: $.fn.innerHeight,
					outerWidth: $.fn.outerWidth,
					outerHeight: $.fn.outerHeight
				};
	
				function reduce(elem, size, border, margin) {
					$.each(side, function () {
						size -= parseFloat($.css(elem, "padding" + this)) || 0;
						if (border) {
							size -= parseFloat($.css(elem, "border" + this + "Width")) || 0;
						}
						if (margin) {
							size -= parseFloat($.css(elem, "margin" + this)) || 0;
						}
					});
					return size;
				}
	
				$.fn["inner" + name] = function (size) {
					if (size === undefined) {
						return orig["inner" + name].call(this);
					}
	
					return this.each(function () {
						$(this).css(type, reduce(this, size) + "px");
					});
				};
	
				$.fn["outer" + name] = function (size, margin) {
					if (typeof size !== "number") {
						return orig["outer" + name].call(this, size);
					}
	
					return this.each(function () {
						$(this).css(type, reduce(this, size, true, margin) + "px");
					});
				};
			});
		}
	
		// support: jQuery <1.8
		if (!$.fn.addBack) {
			$.fn.addBack = function (selector) {
				return this.add(selector == null ? this.prevObject : this.prevObject.filter(selector));
			};
		}
	
		// support: jQuery 1.6.1, 1.6.2 (http://bugs.jquery.com/ticket/9413)
		if ($("<a>").data("a-b", "a").removeData("a-b").data("a-b")) {
			$.fn.removeData = function (removeData) {
				return function (key) {
					if (arguments.length) {
						return removeData.call(this, $.camelCase(key));
					} else {
						return removeData.call(this);
					}
				};
			}($.fn.removeData);
		}
	
		// deprecated
		$.ui.ie = !!/msie [\w.]+/.exec(navigator.userAgent.toLowerCase());
	
		$.fn.extend({
			focus: function (orig) {
				return function (delay, fn) {
					return typeof delay === "number" ? this.each(function () {
						var elem = this;
						setTimeout(function () {
							$(elem).focus();
							if (fn) {
								fn.call(elem);
							}
						}, delay);
					}) : orig.apply(this, arguments);
				};
			}($.fn.focus),
	
			disableSelection: function () {
				var eventType = "onselectstart" in document.createElement("div") ? "selectstart" : "mousedown";
	
				return function () {
					return this.bind(eventType + ".ui-disableSelection", function (event) {
						event.preventDefault();
					});
				};
			}(),
	
			enableSelection: function enableSelection() {
				return this.unbind(".ui-disableSelection");
			},
	
			zIndex: function zIndex(_zIndex) {
				if (_zIndex !== undefined) {
					return this.css("zIndex", _zIndex);
				}
	
				if (this.length) {
					var elem = $(this[0]),
					    position,
					    value;
					while (elem.length && elem[0] !== document) {
						// Ignore z-index if position is set to a value where z-index is ignored by the browser
						// This makes behavior of this function consistent across browsers
						// WebKit always returns auto if the element is positioned
						position = elem.css("position");
						if (position === "absolute" || position === "relative" || position === "fixed") {
							// IE returns 0 when zIndex is not specified
							// other browsers return a string
							// we ignore the case of nested elements with an explicit value of 0
							// <div style="z-index: -10;"><div style="z-index: 0;"></div></div>
							value = parseInt(elem.css("zIndex"), 10);
							if (!isNaN(value) && value !== 0) {
								return value;
							}
						}
						elem = elem.parent();
					}
				}
	
				return 0;
			}
		});
	
		// $.ui.plugin is deprecated. Use $.widget() extensions instead.
		$.ui.plugin = {
			add: function add(module, option, set) {
				var i,
				    proto = $.ui[module].prototype;
				for (i in set) {
					proto.plugins[i] = proto.plugins[i] || [];
					proto.plugins[i].push([option, set[i]]);
				}
			},
			call: function call(instance, name, args, allowDisconnected) {
				var i,
				    set = instance.plugins[name];
	
				if (!set) {
					return;
				}
	
				if (!allowDisconnected && (!instance.element[0].parentNode || instance.element[0].parentNode.nodeType === 11)) {
					return;
				}
	
				for (i = 0; i < set.length; i++) {
					if (instance.options[set[i][0]]) {
						set[i][1].apply(instance.element, args);
					}
				}
			}
		};
	
		/*!
	  * jQuery UI Datepicker 1.11.2
	  * http://jqueryui.com
	  *
	  * Copyright 2014 jQuery Foundation and other contributors
	  * Released under the MIT license.
	  * http://jquery.org/license
	  *
	  * http://api.jqueryui.com/datepicker/
	  */
	
		$.extend($.ui, { datepicker: { version: "1.11.2" } });
	
		var datepicker_instActive;
	
		function datepicker_getZindex(elem) {
			var position, value;
			while (elem.length && elem[0] !== document) {
				// Ignore z-index if position is set to a value where z-index is ignored by the browser
				// This makes behavior of this function consistent across browsers
				// WebKit always returns auto if the element is positioned
				position = elem.css("position");
				if (position === "absolute" || position === "relative" || position === "fixed") {
					// IE returns 0 when zIndex is not specified
					// other browsers return a string
					// we ignore the case of nested elements with an explicit value of 0
					// <div style="z-index: -10;"><div style="z-index: 0;"></div></div>
					value = parseInt(elem.css("zIndex"), 10);
					if (!isNaN(value) && value !== 0) {
						return value;
					}
				}
				elem = elem.parent();
			}
	
			return 0;
		}
		/* Date picker manager.
	    Use the singleton instance of this class, $.datepicker, to interact with the date picker.
	    Settings for (groups of) date pickers are maintained in an instance object,
	    allowing multiple different settings on the same page. */
	
		function Datepicker() {
			this._curInst = null; // The current instance in use
			this._keyEvent = false; // If the last event was a key event
			this._disabledInputs = []; // List of date picker inputs that have been disabled
			this._datepickerShowing = false; // True if the popup picker is showing , false if not
			this._inDialog = false; // True if showing within a "dialog", false if not
			this._mainDivId = "ui-datepicker-div"; // The ID of the main datepicker division
			this._inlineClass = "ui-datepicker-inline"; // The name of the inline marker class
			this._appendClass = "ui-datepicker-append"; // The name of the append marker class
			this._triggerClass = "ui-datepicker-trigger"; // The name of the trigger marker class
			this._dialogClass = "ui-datepicker-dialog"; // The name of the dialog marker class
			this._disableClass = "ui-datepicker-disabled"; // The name of the disabled covering marker class
			this._unselectableClass = "ui-datepicker-unselectable"; // The name of the unselectable cell marker class
			this._currentClass = "ui-datepicker-current-day"; // The name of the current day marker class
			this._dayOverClass = "ui-datepicker-days-cell-over"; // The name of the day hover marker class
			this.regional = []; // Available regional settings, indexed by language code
			this.regional[""] = { // Default regional settings
				closeText: "Done", // Display text for close link
				prevText: "Prev", // Display text for previous month link
				nextText: "Next", // Display text for next month link
				currentText: "Today", // Display text for current month link
				monthNames: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], // Names of months for drop-down and formatting
				monthNamesShort: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], // For formatting
				dayNames: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], // For formatting
				dayNamesShort: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], // For formatting
				dayNamesMin: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"], // Column headings for days starting at Sunday
				weekHeader: "Wk", // Column header for week of the year
				dateFormat: "mm/dd/yy", // See format options on parseDate
				firstDay: 0, // The first day of the week, Sun = 0, Mon = 1, ...
				isRTL: false, // True if right-to-left language, false if left-to-right
				showMonthAfterYear: false, // True if the year select precedes month, false for month then year
				yearSuffix: "" // Additional text to append to the year in the month headers
			};
			this._defaults = { // Global defaults for all the date picker instances
				showOn: "focus", // "focus" for popup on focus,
				// "button" for trigger button, or "both" for either
				showAnim: "fadeIn", // Name of jQuery animation for popup
				showOptions: {}, // Options for enhanced animations
				defaultDate: null, // Used when field is blank: actual date,
				// +/-number for offset from today, null for today
				appendText: "", // Display text following the input box, e.g. showing the format
				buttonText: "...", // Text for trigger button
				buttonImage: "", // URL for trigger button image
				buttonImageOnly: false, // True if the image appears alone, false if it appears on a button
				hideIfNoPrevNext: false, // True to hide next/previous month links
				// if not applicable, false to just disable them
				navigationAsDateFormat: false, // True if date formatting applied to prev/today/next links
				gotoCurrent: false, // True if today link goes back to current selection instead
				changeMonth: false, // True if month can be selected directly, false if only prev/next
				changeYear: false, // True if year can be selected directly, false if only prev/next
				yearRange: "c-10:c+10", // Range of years to display in drop-down,
				// either relative to today's year (-nn:+nn), relative to currently displayed year
				// (c-nn:c+nn), absolute (nnnn:nnnn), or a combination of the above (nnnn:-n)
				showOtherMonths: false, // True to show dates in other months, false to leave blank
				selectOtherMonths: false, // True to allow selection of dates in other months, false for unselectable
				showWeek: false, // True to show week of the year, false to not show it
				calculateWeek: this.iso8601Week, // How to calculate the week of the year,
				// takes a Date and returns the number of the week for it
				shortYearCutoff: "+10", // Short year values < this are in the current century,
				// > this are in the previous century,
				// string value starting with "+" for current year + value
				minDate: null, // The earliest selectable date, or null for no limit
				maxDate: null, // The latest selectable date, or null for no limit
				duration: "fast", // Duration of display/closure
				beforeShowDay: null, // Function that takes a date and returns an array with
				// [0] = true if selectable, false if not, [1] = custom CSS class name(s) or "",
				// [2] = cell title (optional), e.g. $.datepicker.noWeekends
				beforeShow: null, // Function that takes an input field and
				// returns a set of custom settings for the date picker
				onSelect: null, // Define a callback function when a date is selected
				onChangeMonthYear: null, // Define a callback function when the month or year is changed
				onClose: null, // Define a callback function when the datepicker is closed
				numberOfMonths: 1, // Number of months to show at a time
				showCurrentAtPos: 0, // The position in multipe months at which to show the current month (starting at 0)
				stepMonths: 1, // Number of months to step back/forward
				stepBigMonths: 12, // Number of months to step back/forward for the big links
				altField: "", // Selector for an alternate field to store selected dates into
				altFormat: "", // The date format to use for the alternate field
				constrainInput: true, // The input is constrained by the current date format
				showButtonPanel: false, // True to show button panel, false to not show it
				autoSize: false, // True to size the input for the date format, false to leave as is
				disabled: false // The initial disabled state
			};
			$.extend(this._defaults, this.regional[""]);
			this.regional.en = $.extend(true, {}, this.regional[""]);
			this.regional["en-US"] = $.extend(true, {}, this.regional.en);
			this.dpDiv = datepicker_bindHover($("<div id='" + this._mainDivId + "' class='ui-datepicker ui-widget ui-widget-content ui-helper-clearfix ui-corner-all'></div>"));
		}
	
		$.extend(Datepicker.prototype, {
			/* Class name added to elements to indicate already configured with a date picker. */
			markerClassName: "hasDatepicker",
	
			//Keep track of the maximum number of rows displayed (see #7043)
			maxRows: 4,
	
			// TODO rename to "widget" when switching to widget factory
			_widgetDatepicker: function _widgetDatepicker() {
				return this.dpDiv;
			},
	
			/* Override the default settings for all instances of the date picker.
	   * @param  settings  object - the new settings to use as defaults (anonymous object)
	   * @return the manager object
	   */
			setDefaults: function setDefaults(settings) {
				datepicker_extendRemove(this._defaults, settings || {});
				return this;
			},
	
			/* Attach the date picker to a jQuery selection.
	   * @param  target	element - the target input field or division or span
	   * @param  settings  object - the new settings to use for this date picker instance (anonymous)
	   */
			_attachDatepicker: function _attachDatepicker(target, settings) {
				var nodeName, inline, inst;
				nodeName = target.nodeName.toLowerCase();
				inline = nodeName === "div" || nodeName === "span";
				if (!target.id) {
					this.uuid += 1;
					target.id = "dp" + this.uuid;
				}
				inst = this._newInst($(target), inline);
				inst.settings = $.extend({}, settings || {});
				if (nodeName === "input") {
					this._connectDatepicker(target, inst);
				} else if (inline) {
					this._inlineDatepicker(target, inst);
				}
			},
	
			/* Create a new instance object. */
			_newInst: function _newInst(target, inline) {
				var id = target[0].id.replace(/([^A-Za-z0-9_\-])/g, "\\\\$1"); // escape jQuery meta chars
				return { id: id, input: target, // associated target
					selectedDay: 0, selectedMonth: 0, selectedYear: 0, // current selection
					drawMonth: 0, drawYear: 0, // month being drawn
					inline: inline, // is datepicker inline or not
					dpDiv: !inline ? this.dpDiv : // presentation div
					datepicker_bindHover($("<div class='" + this._inlineClass + " ui-datepicker ui-widget ui-widget-content ui-helper-clearfix ui-corner-all'></div>")) };
			},
	
			/* Attach the date picker to an input field. */
			_connectDatepicker: function _connectDatepicker(target, inst) {
				var input = $(target);
				inst.append = $([]);
				inst.trigger = $([]);
				if (input.hasClass(this.markerClassName)) {
					return;
				}
				this._attachments(input, inst);
				input.addClass(this.markerClassName).keydown(this._doKeyDown).keypress(this._doKeyPress).keyup(this._doKeyUp);
				this._autoSize(inst);
				$.data(target, "datepicker", inst);
				//If disabled option is true, disable the datepicker once it has been attached to the input (see ticket #5665)
				if (inst.settings.disabled) {
					this._disableDatepicker(target);
				}
			},
	
			/* Make attachments based on settings. */
			_attachments: function _attachments(input, inst) {
				var showOn,
				    buttonText,
				    buttonImage,
				    appendText = this._get(inst, "appendText"),
				    isRTL = this._get(inst, "isRTL");
	
				if (inst.append) {
					inst.append.remove();
				}
				if (appendText) {
					inst.append = $("<span class='" + this._appendClass + "'>" + appendText + "</span>");
					input[isRTL ? "before" : "after"](inst.append);
				}
	
				input.unbind("focus", this._showDatepicker);
	
				if (inst.trigger) {
					inst.trigger.remove();
				}
	
				showOn = this._get(inst, "showOn");
				if (showOn === "focus" || showOn === "both") {
					// pop-up date picker when in the marked field
					input.focus(this._showDatepicker);
				}
				if (showOn === "button" || showOn === "both") {
					// pop-up date picker when button clicked
					buttonText = this._get(inst, "buttonText");
					buttonImage = this._get(inst, "buttonImage");
					inst.trigger = $(this._get(inst, "buttonImageOnly") ? $("<img/>").addClass(this._triggerClass).attr({ src: buttonImage, alt: buttonText, title: buttonText }) : $("<button type='button'></button>").addClass(this._triggerClass).html(!buttonImage ? buttonText : $("<img/>").attr({ src: buttonImage, alt: buttonText, title: buttonText })));
					input[isRTL ? "before" : "after"](inst.trigger);
					inst.trigger.click(function () {
						if ($.datepicker._datepickerShowing && $.datepicker._lastInput === input[0]) {
							$.datepicker._hideDatepicker();
						} else if ($.datepicker._datepickerShowing && $.datepicker._lastInput !== input[0]) {
							$.datepicker._hideDatepicker();
							$.datepicker._showDatepicker(input[0]);
						} else {
							$.datepicker._showDatepicker(input[0]);
						}
						return false;
					});
				}
			},
	
			/* Apply the maximum length for the date format. */
			_autoSize: function _autoSize(inst) {
				if (this._get(inst, "autoSize") && !inst.inline) {
					var findMax,
					    max,
					    maxI,
					    i,
					    date = new Date(2009, 12 - 1, 20),
					    // Ensure double digits
					dateFormat = this._get(inst, "dateFormat");
	
					if (dateFormat.match(/[DM]/)) {
						findMax = function findMax(names) {
							max = 0;
							maxI = 0;
							for (i = 0; i < names.length; i++) {
								if (names[i].length > max) {
									max = names[i].length;
									maxI = i;
								}
							}
							return maxI;
						};
						date.setMonth(findMax(this._get(inst, dateFormat.match(/MM/) ? "monthNames" : "monthNamesShort")));
						date.setDate(findMax(this._get(inst, dateFormat.match(/DD/) ? "dayNames" : "dayNamesShort")) + 20 - date.getDay());
					}
					inst.input.attr("size", this._formatDate(inst, date).length);
				}
			},
	
			/* Attach an inline date picker to a div. */
			_inlineDatepicker: function _inlineDatepicker(target, inst) {
				var divSpan = $(target);
				if (divSpan.hasClass(this.markerClassName)) {
					return;
				}
				divSpan.addClass(this.markerClassName).append(inst.dpDiv);
				$.data(target, "datepicker", inst);
				this._setDate(inst, this._getDefaultDate(inst), true);
				this._updateDatepicker(inst);
				this._updateAlternate(inst);
				//If disabled option is true, disable the datepicker before showing it (see ticket #5665)
				if (inst.settings.disabled) {
					this._disableDatepicker(target);
				}
				// Set display:block in place of inst.dpDiv.show() which won't work on disconnected elements
				// http://bugs.jqueryui.com/ticket/7552 - A Datepicker created on a detached div has zero height
				inst.dpDiv.css("display", "block");
			},
	
			/* Pop-up the date picker in a "dialog" box.
	   * @param  input element - ignored
	   * @param  date	string or Date - the initial date to display
	   * @param  onSelect  function - the function to call when a date is selected
	   * @param  settings  object - update the dialog date picker instance's settings (anonymous object)
	   * @param  pos int[2] - coordinates for the dialog's position within the screen or
	   *					event - with x/y coordinates or
	   *					leave empty for default (screen centre)
	   * @return the manager object
	   */
			_dialogDatepicker: function _dialogDatepicker(input, date, onSelect, settings, pos) {
				var id,
				    browserWidth,
				    browserHeight,
				    scrollX,
				    scrollY,
				    inst = this._dialogInst; // internal instance
	
				if (!inst) {
					this.uuid += 1;
					id = "dp" + this.uuid;
					this._dialogInput = $("<input type='text' id='" + id + "' style='position: absolute; top: -100px; width: 0px;'/>");
					this._dialogInput.keydown(this._doKeyDown);
					$("body").append(this._dialogInput);
					inst = this._dialogInst = this._newInst(this._dialogInput, false);
					inst.settings = {};
					$.data(this._dialogInput[0], "datepicker", inst);
				}
				datepicker_extendRemove(inst.settings, settings || {});
				date = date && date.constructor === Date ? this._formatDate(inst, date) : date;
				this._dialogInput.val(date);
	
				this._pos = pos ? pos.length ? pos : [pos.pageX, pos.pageY] : null;
				if (!this._pos) {
					browserWidth = document.documentElement.clientWidth;
					browserHeight = document.documentElement.clientHeight;
					scrollX = document.documentElement.scrollLeft || document.body.scrollLeft;
					scrollY = document.documentElement.scrollTop || document.body.scrollTop;
					this._pos = // should use actual width/height below
					[browserWidth / 2 - 100 + scrollX, browserHeight / 2 - 150 + scrollY];
				}
	
				// move input on screen for focus, but hidden behind dialog
				this._dialogInput.css("left", this._pos[0] + 20 + "px").css("top", this._pos[1] + "px");
				inst.settings.onSelect = onSelect;
				this._inDialog = true;
				this.dpDiv.addClass(this._dialogClass);
				this._showDatepicker(this._dialogInput[0]);
				if ($.blockUI) {
					$.blockUI(this.dpDiv);
				}
				$.data(this._dialogInput[0], "datepicker", inst);
				return this;
			},
	
			/* Detach a datepicker from its control.
	   * @param  target	element - the target input field or division or span
	   */
			_destroyDatepicker: function _destroyDatepicker(target) {
				var nodeName,
				    $target = $(target),
				    inst = $.data(target, "datepicker");
	
				if (!$target.hasClass(this.markerClassName)) {
					return;
				}
	
				nodeName = target.nodeName.toLowerCase();
				$.removeData(target, "datepicker");
				if (nodeName === "input") {
					inst.append.remove();
					inst.trigger.remove();
					$target.removeClass(this.markerClassName).unbind("focus", this._showDatepicker).unbind("keydown", this._doKeyDown).unbind("keypress", this._doKeyPress).unbind("keyup", this._doKeyUp);
				} else if (nodeName === "div" || nodeName === "span") {
					$target.removeClass(this.markerClassName).empty();
				}
			},
	
			/* Enable the date picker to a jQuery selection.
	   * @param  target	element - the target input field or division or span
	   */
			_enableDatepicker: function _enableDatepicker(target) {
				var nodeName,
				    inline,
				    $target = $(target),
				    inst = $.data(target, "datepicker");
	
				if (!$target.hasClass(this.markerClassName)) {
					return;
				}
	
				nodeName = target.nodeName.toLowerCase();
				if (nodeName === "input") {
					target.disabled = false;
					inst.trigger.filter("button").each(function () {
						this.disabled = false;
					}).end().filter("img").css({ opacity: "1.0", cursor: "" });
				} else if (nodeName === "div" || nodeName === "span") {
					inline = $target.children("." + this._inlineClass);
					inline.children().removeClass("ui-state-disabled");
					inline.find("select.ui-datepicker-month, select.ui-datepicker-year").prop("disabled", false);
				}
				this._disabledInputs = $.map(this._disabledInputs, function (value) {
					return value === target ? null : value;
				}); // delete entry
			},
	
			/* Disable the date picker to a jQuery selection.
	   * @param  target	element - the target input field or division or span
	   */
			_disableDatepicker: function _disableDatepicker(target) {
				var nodeName,
				    inline,
				    $target = $(target),
				    inst = $.data(target, "datepicker");
	
				if (!$target.hasClass(this.markerClassName)) {
					return;
				}
	
				nodeName = target.nodeName.toLowerCase();
				if (nodeName === "input") {
					target.disabled = true;
					inst.trigger.filter("button").each(function () {
						this.disabled = true;
					}).end().filter("img").css({ opacity: "0.5", cursor: "default" });
				} else if (nodeName === "div" || nodeName === "span") {
					inline = $target.children("." + this._inlineClass);
					inline.children().addClass("ui-state-disabled");
					inline.find("select.ui-datepicker-month, select.ui-datepicker-year").prop("disabled", true);
				}
				this._disabledInputs = $.map(this._disabledInputs, function (value) {
					return value === target ? null : value;
				}); // delete entry
				this._disabledInputs[this._disabledInputs.length] = target;
			},
	
			/* Is the first field in a jQuery collection disabled as a datepicker?
	   * @param  target	element - the target input field or division or span
	   * @return boolean - true if disabled, false if enabled
	   */
			_isDisabledDatepicker: function _isDisabledDatepicker(target) {
				if (!target) {
					return false;
				}
				for (var i = 0; i < this._disabledInputs.length; i++) {
					if (this._disabledInputs[i] === target) {
						return true;
					}
				}
				return false;
			},
	
			/* Retrieve the instance data for the target control.
	   * @param  target  element - the target input field or division or span
	   * @return  object - the associated instance data
	   * @throws  error if a jQuery problem getting data
	   */
			_getInst: function _getInst(target) {
				try {
					return $.data(target, "datepicker");
				} catch (err) {
					throw "Missing instance data for this datepicker";
				}
			},
	
			/* Update or retrieve the settings for a date picker attached to an input field or division.
	   * @param  target  element - the target input field or division or span
	   * @param  name	object - the new settings to update or
	   *				string - the name of the setting to change or retrieve,
	   *				when retrieving also "all" for all instance settings or
	   *				"defaults" for all global defaults
	   * @param  value   any - the new value for the setting
	   *				(omit if above is an object or to retrieve a value)
	   */
			_optionDatepicker: function _optionDatepicker(target, name, value) {
				var settings,
				    date,
				    minDate,
				    maxDate,
				    inst = this._getInst(target);
	
				if (arguments.length === 2 && typeof name === "string") {
					return name === "defaults" ? $.extend({}, $.datepicker._defaults) : inst ? name === "all" ? $.extend({}, inst.settings) : this._get(inst, name) : null;
				}
	
				settings = name || {};
				if (typeof name === "string") {
					settings = {};
					settings[name] = value;
				}
	
				if (inst) {
					if (this._curInst === inst) {
						this._hideDatepicker();
					}
	
					date = this._getDateDatepicker(target, true);
					minDate = this._getMinMaxDate(inst, "min");
					maxDate = this._getMinMaxDate(inst, "max");
					datepicker_extendRemove(inst.settings, settings);
					// reformat the old minDate/maxDate values if dateFormat changes and a new minDate/maxDate isn't provided
					if (minDate !== null && settings.dateFormat !== undefined && settings.minDate === undefined) {
						inst.settings.minDate = this._formatDate(inst, minDate);
					}
					if (maxDate !== null && settings.dateFormat !== undefined && settings.maxDate === undefined) {
						inst.settings.maxDate = this._formatDate(inst, maxDate);
					}
					if ("disabled" in settings) {
						if (settings.disabled) {
							this._disableDatepicker(target);
						} else {
							this._enableDatepicker(target);
						}
					}
					this._attachments($(target), inst);
					this._autoSize(inst);
					this._setDate(inst, date);
					this._updateAlternate(inst);
					this._updateDatepicker(inst);
				}
			},
	
			// change method deprecated
			_changeDatepicker: function _changeDatepicker(target, name, value) {
				this._optionDatepicker(target, name, value);
			},
	
			/* Redraw the date picker attached to an input field or division.
	   * @param  target  element - the target input field or division or span
	   */
			_refreshDatepicker: function _refreshDatepicker(target) {
				var inst = this._getInst(target);
				if (inst) {
					this._updateDatepicker(inst);
				}
			},
	
			/* Set the dates for a jQuery selection.
	   * @param  target element - the target input field or division or span
	   * @param  date	Date - the new date
	   */
			_setDateDatepicker: function _setDateDatepicker(target, date) {
				var inst = this._getInst(target);
				if (inst) {
					this._setDate(inst, date);
					this._updateDatepicker(inst);
					this._updateAlternate(inst);
				}
			},
	
			/* Get the date(s) for the first entry in a jQuery selection.
	   * @param  target element - the target input field or division or span
	   * @param  noDefault boolean - true if no default date is to be used
	   * @return Date - the current date
	   */
			_getDateDatepicker: function _getDateDatepicker(target, noDefault) {
				var inst = this._getInst(target);
				if (inst && !inst.inline) {
					this._setDateFromField(inst, noDefault);
				}
				return inst ? this._getDate(inst) : null;
			},
	
			/* Handle keystrokes. */
			_doKeyDown: function _doKeyDown(event) {
				var onSelect,
				    dateStr,
				    sel,
				    inst = $.datepicker._getInst(event.target),
				    handled = true,
				    isRTL = inst.dpDiv.is(".ui-datepicker-rtl");
	
				inst._keyEvent = true;
				if ($.datepicker._datepickerShowing) {
					switch (event.keyCode) {
						case 9:
							$.datepicker._hideDatepicker();
							handled = false;
							break; // hide on tab out
						case 13:
							sel = $("td." + $.datepicker._dayOverClass + ":not(." + $.datepicker._currentClass + ")", inst.dpDiv);
							if (sel[0]) {
								$.datepicker._selectDay(event.target, inst.selectedMonth, inst.selectedYear, sel[0]);
							}
	
							onSelect = $.datepicker._get(inst, "onSelect");
							if (onSelect) {
								dateStr = $.datepicker._formatDate(inst);
	
								// trigger custom callback
								onSelect.apply(inst.input ? inst.input[0] : null, [dateStr, inst]);
							} else {
								$.datepicker._hideDatepicker();
							}
	
							return false; // don't submit the form
						case 27:
							$.datepicker._hideDatepicker();
							break; // hide on escape
						case 33:
							$.datepicker._adjustDate(event.target, event.ctrlKey ? -$.datepicker._get(inst, "stepBigMonths") : -$.datepicker._get(inst, "stepMonths"), "M");
							break; // previous month/year on page up/+ ctrl
						case 34:
							$.datepicker._adjustDate(event.target, event.ctrlKey ? +$.datepicker._get(inst, "stepBigMonths") : +$.datepicker._get(inst, "stepMonths"), "M");
							break; // next month/year on page down/+ ctrl
						case 35:
							if (event.ctrlKey || event.metaKey) {
								$.datepicker._clearDate(event.target);
							}
							handled = event.ctrlKey || event.metaKey;
							break; // clear on ctrl or command +end
						case 36:
							if (event.ctrlKey || event.metaKey) {
								$.datepicker._gotoToday(event.target);
							}
							handled = event.ctrlKey || event.metaKey;
							break; // current on ctrl or command +home
						case 37:
							if (event.ctrlKey || event.metaKey) {
								$.datepicker._adjustDate(event.target, isRTL ? +1 : -1, "D");
							}
							handled = event.ctrlKey || event.metaKey;
							// -1 day on ctrl or command +left
							if (event.originalEvent.altKey) {
								$.datepicker._adjustDate(event.target, event.ctrlKey ? -$.datepicker._get(inst, "stepBigMonths") : -$.datepicker._get(inst, "stepMonths"), "M");
							}
							// next month/year on alt +left on Mac
							break;
						case 38:
							if (event.ctrlKey || event.metaKey) {
								$.datepicker._adjustDate(event.target, -7, "D");
							}
							handled = event.ctrlKey || event.metaKey;
							break; // -1 week on ctrl or command +up
						case 39:
							if (event.ctrlKey || event.metaKey) {
								$.datepicker._adjustDate(event.target, isRTL ? -1 : +1, "D");
							}
							handled = event.ctrlKey || event.metaKey;
							// +1 day on ctrl or command +right
							if (event.originalEvent.altKey) {
								$.datepicker._adjustDate(event.target, event.ctrlKey ? +$.datepicker._get(inst, "stepBigMonths") : +$.datepicker._get(inst, "stepMonths"), "M");
							}
							// next month/year on alt +right
							break;
						case 40:
							if (event.ctrlKey || event.metaKey) {
								$.datepicker._adjustDate(event.target, +7, "D");
							}
							handled = event.ctrlKey || event.metaKey;
							break; // +1 week on ctrl or command +down
						default:
							handled = false;
					}
				} else if (event.keyCode === 36 && event.ctrlKey) {
					// display the date picker on ctrl+home
					$.datepicker._showDatepicker(this);
				} else {
					handled = false;
				}
	
				if (handled) {
					event.preventDefault();
					event.stopPropagation();
				}
			},
	
			/* Filter entered characters - based on date format. */
			_doKeyPress: function _doKeyPress(event) {
				var chars,
				    chr,
				    inst = $.datepicker._getInst(event.target);
	
				if ($.datepicker._get(inst, "constrainInput")) {
					chars = $.datepicker._possibleChars($.datepicker._get(inst, "dateFormat"));
					chr = String.fromCharCode(event.charCode == null ? event.keyCode : event.charCode);
					return event.ctrlKey || event.metaKey || chr < " " || !chars || chars.indexOf(chr) > -1;
				}
			},
	
			/* Synchronise manual entry and field/alternate field. */
			_doKeyUp: function _doKeyUp(event) {
				var date,
				    inst = $.datepicker._getInst(event.target);
	
				if (inst.input.val() !== inst.lastVal) {
					try {
						date = $.datepicker.parseDate($.datepicker._get(inst, "dateFormat"), inst.input ? inst.input.val() : null, $.datepicker._getFormatConfig(inst));
	
						if (date) {
							// only if valid
							$.datepicker._setDateFromField(inst);
							$.datepicker._updateAlternate(inst);
							$.datepicker._updateDatepicker(inst);
						}
					} catch (err) {}
				}
				return true;
			},
	
			/* Pop-up the date picker for a given input field.
	   * If false returned from beforeShow event handler do not show.
	   * @param  input  element - the input field attached to the date picker or
	   *					event - if triggered by focus
	   */
			_showDatepicker: function _showDatepicker(input) {
				input = input.target || input;
				if (input.nodeName.toLowerCase() !== "input") {
					// find from button/image trigger
					input = $("input", input.parentNode)[0];
				}
	
				if ($.datepicker._isDisabledDatepicker(input) || $.datepicker._lastInput === input) {
					// already here
					return;
				}
	
				var inst, beforeShow, beforeShowSettings, isFixed, offset, showAnim, duration;
	
				inst = $.datepicker._getInst(input);
				if ($.datepicker._curInst && $.datepicker._curInst !== inst) {
					$.datepicker._curInst.dpDiv.stop(true, true);
					if (inst && $.datepicker._datepickerShowing) {
						$.datepicker._hideDatepicker($.datepicker._curInst.input[0]);
					}
				}
	
				beforeShow = $.datepicker._get(inst, "beforeShow");
				beforeShowSettings = beforeShow ? beforeShow.apply(input, [input, inst]) : {};
				if (beforeShowSettings === false) {
					return;
				}
				datepicker_extendRemove(inst.settings, beforeShowSettings);
	
				inst.lastVal = null;
				$.datepicker._lastInput = input;
				$.datepicker._setDateFromField(inst);
	
				if ($.datepicker._inDialog) {
					// hide cursor
					input.value = "";
				}
				if (!$.datepicker._pos) {
					// position below input
					$.datepicker._pos = $.datepicker._findPos(input);
					$.datepicker._pos[1] += input.offsetHeight; // add the height
				}
	
				isFixed = false;
				$(input).parents().each(function () {
					isFixed |= $(this).css("position") === "fixed";
					return !isFixed;
				});
	
				offset = { left: $.datepicker._pos[0], top: $.datepicker._pos[1] };
				$.datepicker._pos = null;
				//to avoid flashes on Firefox
				inst.dpDiv.empty();
				// determine sizing offscreen
				inst.dpDiv.css({ position: "absolute", display: "block", top: "-1000px" });
				$.datepicker._updateDatepicker(inst);
				// fix width for dynamic number of date pickers
				// and adjust position before showing
				offset = $.datepicker._checkOffset(inst, offset, isFixed);
				inst.dpDiv.css({ position: $.datepicker._inDialog && $.blockUI ? "static" : isFixed ? "fixed" : "absolute", display: "none",
					left: offset.left + "px", top: offset.top + "px" });
	
				if (!inst.inline) {
					showAnim = $.datepicker._get(inst, "showAnim");
					duration = $.datepicker._get(inst, "duration");
					inst.dpDiv.css("z-index", datepicker_getZindex($(input)) + 1);
					$.datepicker._datepickerShowing = true;
	
					if ($.effects && $.effects.effect[showAnim]) {
						inst.dpDiv.show(showAnim, $.datepicker._get(inst, "showOptions"), duration);
					} else {
						inst.dpDiv[showAnim || "show"](showAnim ? duration : null);
					}
	
					if ($.datepicker._shouldFocusInput(inst)) {
						inst.input.focus();
					}
	
					$.datepicker._curInst = inst;
				}
			},
	
			/* Generate the date picker content. */
			_updateDatepicker: function _updateDatepicker(inst) {
				this.maxRows = 4; //Reset the max number of rows being displayed (see #7043)
				datepicker_instActive = inst; // for delegate hover events
				inst.dpDiv.empty().append(this._generateHTML(inst));
				this._attachHandlers(inst);
	
				var origyearshtml,
				    numMonths = this._getNumberOfMonths(inst),
				    cols = numMonths[1],
				    width = 17,
				    activeCell = inst.dpDiv.find("." + this._dayOverClass + " a");
	
				if (activeCell.length > 0) {
					datepicker_handleMouseover.apply(activeCell.get(0));
				}
	
				inst.dpDiv.removeClass("ui-datepicker-multi-2 ui-datepicker-multi-3 ui-datepicker-multi-4").width("");
				if (cols > 1) {
					inst.dpDiv.addClass("ui-datepicker-multi-" + cols).css("width", width * cols + "em");
				}
				inst.dpDiv[(numMonths[0] !== 1 || numMonths[1] !== 1 ? "add" : "remove") + "Class"]("ui-datepicker-multi");
				inst.dpDiv[(this._get(inst, "isRTL") ? "add" : "remove") + "Class"]("ui-datepicker-rtl");
	
				if (inst === $.datepicker._curInst && $.datepicker._datepickerShowing && $.datepicker._shouldFocusInput(inst)) {
					inst.input.focus();
				}
	
				// deffered render of the years select (to avoid flashes on Firefox)
				if (inst.yearshtml) {
					origyearshtml = inst.yearshtml;
					setTimeout(function () {
						//assure that inst.yearshtml didn't change.
						if (origyearshtml === inst.yearshtml && inst.yearshtml) {
							inst.dpDiv.find("select.ui-datepicker-year:first").replaceWith(inst.yearshtml);
						}
						origyearshtml = inst.yearshtml = null;
					}, 0);
				}
			},
	
			// #6694 - don't focus the input if it's already focused
			// this breaks the change event in IE
			// Support: IE and jQuery <1.9
			_shouldFocusInput: function _shouldFocusInput(inst) {
				return inst.input && inst.input.is(":visible") && !inst.input.is(":disabled") && !inst.input.is(":focus");
			},
	
			/* Check positioning to remain on screen. */
			_checkOffset: function _checkOffset(inst, offset, isFixed) {
				var dpWidth = inst.dpDiv.outerWidth(),
				    dpHeight = inst.dpDiv.outerHeight(),
				    inputWidth = inst.input ? inst.input.outerWidth() : 0,
				    inputHeight = inst.input ? inst.input.outerHeight() : 0,
				    viewWidth = document.documentElement.clientWidth + (isFixed ? 0 : $(document).scrollLeft()),
				    viewHeight = document.documentElement.clientHeight + (isFixed ? 0 : $(document).scrollTop());
	
				offset.left -= this._get(inst, "isRTL") ? dpWidth - inputWidth : 0;
				offset.left -= isFixed && offset.left === inst.input.offset().left ? $(document).scrollLeft() : 0;
				offset.top -= isFixed && offset.top === inst.input.offset().top + inputHeight ? $(document).scrollTop() : 0;
	
				// now check if datepicker is showing outside window viewport - move to a better place if so.
				offset.left -= Math.min(offset.left, offset.left + dpWidth > viewWidth && viewWidth > dpWidth ? Math.abs(offset.left + dpWidth - viewWidth) : 0);
				offset.top -= Math.min(offset.top, offset.top + dpHeight > viewHeight && viewHeight > dpHeight ? Math.abs(dpHeight + inputHeight) : 0);
	
				return offset;
			},
	
			/* Find an object's position on the screen. */
			_findPos: function _findPos(obj) {
				var position,
				    inst = this._getInst(obj),
				    isRTL = this._get(inst, "isRTL");
	
				while (obj && (obj.type === "hidden" || obj.nodeType !== 1 || $.expr.filters.hidden(obj))) {
					obj = obj[isRTL ? "previousSibling" : "nextSibling"];
				}
	
				position = $(obj).offset();
				return [position.left, position.top];
			},
	
			/* Hide the date picker from view.
	   * @param  input  element - the input field attached to the date picker
	   */
			_hideDatepicker: function _hideDatepicker(input) {
				var showAnim,
				    duration,
				    postProcess,
				    onClose,
				    inst = this._curInst;
	
				if (!inst || input && inst !== $.data(input, "datepicker")) {
					return;
				}
	
				if (this._datepickerShowing) {
					showAnim = this._get(inst, "showAnim");
					duration = this._get(inst, "duration");
					postProcess = function postProcess() {
						$.datepicker._tidyDialog(inst);
					};
	
					// DEPRECATED: after BC for 1.8.x $.effects[ showAnim ] is not needed
					if ($.effects && ($.effects.effect[showAnim] || $.effects[showAnim])) {
						inst.dpDiv.hide(showAnim, $.datepicker._get(inst, "showOptions"), duration, postProcess);
					} else {
						inst.dpDiv[showAnim === "slideDown" ? "slideUp" : showAnim === "fadeIn" ? "fadeOut" : "hide"](showAnim ? duration : null, postProcess);
					}
	
					if (!showAnim) {
						postProcess();
					}
					this._datepickerShowing = false;
	
					onClose = this._get(inst, "onClose");
					if (onClose) {
						onClose.apply(inst.input ? inst.input[0] : null, [inst.input ? inst.input.val() : "", inst]);
					}
	
					this._lastInput = null;
					if (this._inDialog) {
						this._dialogInput.css({ position: "absolute", left: "0", top: "-100px" });
						if ($.blockUI) {
							$.unblockUI();
							$("body").append(this.dpDiv);
						}
					}
					this._inDialog = false;
				}
			},
	
			/* Tidy up after a dialog display. */
			_tidyDialog: function _tidyDialog(inst) {
				inst.dpDiv.removeClass(this._dialogClass).unbind(".ui-datepicker-calendar");
			},
	
			/* Close date picker if clicked elsewhere. */
			_checkExternalClick: function _checkExternalClick(event) {
				if (!$.datepicker._curInst) {
					return;
				}
	
				var $target = $(event.target),
				    inst = $.datepicker._getInst($target[0]);
	
				if ($target[0].id !== $.datepicker._mainDivId && $target.parents("#" + $.datepicker._mainDivId).length === 0 && !$target.hasClass($.datepicker.markerClassName) && !$target.closest("." + $.datepicker._triggerClass).length && $.datepicker._datepickerShowing && !($.datepicker._inDialog && $.blockUI) || $target.hasClass($.datepicker.markerClassName) && $.datepicker._curInst !== inst) {
					$.datepicker._hideDatepicker();
				}
			},
	
			/* Adjust one of the date sub-fields. */
			_adjustDate: function _adjustDate(id, offset, period) {
				var target = $(id),
				    inst = this._getInst(target[0]);
	
				if (this._isDisabledDatepicker(target[0])) {
					return;
				}
				this._adjustInstDate(inst, offset + (period === "M" ? this._get(inst, "showCurrentAtPos") : 0), // undo positioning
				period);
				this._updateDatepicker(inst);
			},
	
			/* Action for current link. */
			_gotoToday: function _gotoToday(id) {
				var date,
				    target = $(id),
				    inst = this._getInst(target[0]);
	
				if (this._get(inst, "gotoCurrent") && inst.currentDay) {
					inst.selectedDay = inst.currentDay;
					inst.drawMonth = inst.selectedMonth = inst.currentMonth;
					inst.drawYear = inst.selectedYear = inst.currentYear;
				} else {
					date = new Date();
					inst.selectedDay = date.getDate();
					inst.drawMonth = inst.selectedMonth = date.getMonth();
					inst.drawYear = inst.selectedYear = date.getFullYear();
				}
				this._notifyChange(inst);
				this._adjustDate(target);
			},
	
			/* Action for selecting a new month/year. */
			_selectMonthYear: function _selectMonthYear(id, select, period) {
				var target = $(id),
				    inst = this._getInst(target[0]);
	
				inst["selected" + (period === "M" ? "Month" : "Year")] = inst["draw" + (period === "M" ? "Month" : "Year")] = parseInt(select.options[select.selectedIndex].value, 10);
	
				this._notifyChange(inst);
				this._adjustDate(target);
			},
	
			/* Action for selecting a day. */
			_selectDay: function _selectDay(id, month, year, td) {
				var inst,
				    target = $(id);
	
				if ($(td).hasClass(this._unselectableClass) || this._isDisabledDatepicker(target[0])) {
					return;
				}
	
				inst = this._getInst(target[0]);
				inst.selectedDay = inst.currentDay = $("a", td).html();
				inst.selectedMonth = inst.currentMonth = month;
				inst.selectedYear = inst.currentYear = year;
				this._selectDate(id, this._formatDate(inst, inst.currentDay, inst.currentMonth, inst.currentYear));
			},
	
			/* Erase the input field and hide the date picker. */
			_clearDate: function _clearDate(id) {
				var target = $(id);
				this._selectDate(target, "");
			},
	
			/* Update the input field with the selected date. */
			_selectDate: function _selectDate(id, dateStr) {
				var onSelect,
				    target = $(id),
				    inst = this._getInst(target[0]);
	
				dateStr = dateStr != null ? dateStr : this._formatDate(inst);
				if (inst.input) {
					inst.input.val(dateStr);
				}
				this._updateAlternate(inst);
	
				onSelect = this._get(inst, "onSelect");
				if (onSelect) {
					onSelect.apply(inst.input ? inst.input[0] : null, [dateStr, inst]); // trigger custom callback
				} else if (inst.input) {
						inst.input.trigger("change"); // fire the change event
					}
	
				if (inst.inline) {
					this._updateDatepicker(inst);
				} else {
					this._hideDatepicker();
					this._lastInput = inst.input[0];
					if (_typeof(inst.input[0]) !== "object") {
						inst.input.focus(); // restore focus
					}
					this._lastInput = null;
				}
			},
	
			/* Update any alternate field to synchronise with the main field. */
			_updateAlternate: function _updateAlternate(inst) {
				var altFormat,
				    date,
				    dateStr,
				    altField = this._get(inst, "altField");
	
				if (altField) {
					// update alternate field too
					altFormat = this._get(inst, "altFormat") || this._get(inst, "dateFormat");
					date = this._getDate(inst);
					dateStr = this.formatDate(altFormat, date, this._getFormatConfig(inst));
					$(altField).each(function () {
						$(this).val(dateStr);
					});
				}
			},
	
			/* Set as beforeShowDay function to prevent selection of weekends.
	   * @param  date  Date - the date to customise
	   * @return [boolean, string] - is this date selectable?, what is its CSS class?
	   */
			noWeekends: function noWeekends(date) {
				var day = date.getDay();
				return [day > 0 && day < 6, ""];
			},
	
			/* Set as calculateWeek to determine the week of the year based on the ISO 8601 definition.
	   * @param  date  Date - the date to get the week for
	   * @return  number - the number of the week within the year that contains this date
	   */
			iso8601Week: function iso8601Week(date) {
				var time,
				    checkDate = new Date(date.getTime());
	
				// Find Thursday of this week starting on Monday
				checkDate.setDate(checkDate.getDate() + 4 - (checkDate.getDay() || 7));
	
				time = checkDate.getTime();
				checkDate.setMonth(0); // Compare with Jan 1
				checkDate.setDate(1);
				return Math.floor(Math.round((time - checkDate) / 86400000) / 7) + 1;
			},
	
			/* Parse a string value into a date object.
	   * See formatDate below for the possible formats.
	   *
	   * @param  format string - the expected format of the date
	   * @param  value string - the date in the above format
	   * @param  settings Object - attributes include:
	   *					shortYearCutoff  number - the cutoff year for determining the century (optional)
	   *					dayNamesShort	string[7] - abbreviated names of the days from Sunday (optional)
	   *					dayNames		string[7] - names of the days from Sunday (optional)
	   *					monthNamesShort string[12] - abbreviated names of the months (optional)
	   *					monthNames		string[12] - names of the months (optional)
	   * @return  Date - the extracted date value or null if value is blank
	   */
			parseDate: function parseDate(format, value, settings) {
				if (format == null || value == null) {
					throw "Invalid arguments";
				}
	
				value = (typeof value === "undefined" ? "undefined" : _typeof(value)) === "object" ? value.toString() : value + "";
				if (value === "") {
					return null;
				}
	
				var iFormat,
				    dim,
				    extra,
				    iValue = 0,
				    shortYearCutoffTemp = (settings ? settings.shortYearCutoff : null) || this._defaults.shortYearCutoff,
				    shortYearCutoff = typeof shortYearCutoffTemp !== "string" ? shortYearCutoffTemp : new Date().getFullYear() % 100 + parseInt(shortYearCutoffTemp, 10),
				    dayNamesShort = (settings ? settings.dayNamesShort : null) || this._defaults.dayNamesShort,
				    dayNames = (settings ? settings.dayNames : null) || this._defaults.dayNames,
				    monthNamesShort = (settings ? settings.monthNamesShort : null) || this._defaults.monthNamesShort,
				    monthNames = (settings ? settings.monthNames : null) || this._defaults.monthNames,
				    year = -1,
				    month = -1,
				    day = -1,
				    doy = -1,
				    literal = false,
				    date,
	
				// Check whether a format character is doubled
				lookAhead = function lookAhead(match) {
					var matches = iFormat + 1 < format.length && format.charAt(iFormat + 1) === match;
					if (matches) {
						iFormat++;
					}
					return matches;
				},
	
				// Extract a number from the string value
				getNumber = function getNumber(match) {
					var isDoubled = lookAhead(match),
					    size = match === "@" ? 14 : match === "!" ? 20 : match === "y" && isDoubled ? 4 : match === "o" ? 3 : 2,
					    minSize = match === "y" ? size : 1,
					    digits = new RegExp("^\\d{" + minSize + "," + size + "}"),
					    num = value.substring(iValue).match(digits);
					if (!num) {
						throw "Missing number at position " + iValue;
					}
					iValue += num[0].length;
					return parseInt(num[0], 10);
				},
	
				// Extract a name from the string value and convert to an index
				getName = function getName(match, shortNames, longNames) {
					var index = -1,
					    names = $.map(lookAhead(match) ? longNames : shortNames, function (v, k) {
						return [[k, v]];
					}).sort(function (a, b) {
						return -(a[1].length - b[1].length);
					});
	
					$.each(names, function (i, pair) {
						var name = pair[1];
						if (value.substr(iValue, name.length).toLowerCase() === name.toLowerCase()) {
							index = pair[0];
							iValue += name.length;
							return false;
						}
					});
					if (index !== -1) {
						return index + 1;
					} else {
						throw "Unknown name at position " + iValue;
					}
				},
	
				// Confirm that a literal character matches the string value
				checkLiteral = function checkLiteral() {
					if (value.charAt(iValue) !== format.charAt(iFormat)) {
						throw "Unexpected literal at position " + iValue;
					}
					iValue++;
				};
	
				for (iFormat = 0; iFormat < format.length; iFormat++) {
					if (literal) {
						if (format.charAt(iFormat) === "'" && !lookAhead("'")) {
							literal = false;
						} else {
							checkLiteral();
						}
					} else {
						switch (format.charAt(iFormat)) {
							case "d":
								day = getNumber("d");
								break;
							case "D":
								getName("D", dayNamesShort, dayNames);
								break;
							case "o":
								doy = getNumber("o");
								break;
							case "m":
								month = getNumber("m");
								break;
							case "M":
								month = getName("M", monthNamesShort, monthNames);
								break;
							case "y":
								year = getNumber("y");
								break;
							case "@":
								date = new Date(getNumber("@"));
								year = date.getFullYear();
								month = date.getMonth() + 1;
								day = date.getDate();
								break;
							case "!":
								date = new Date((getNumber("!") - this._ticksTo1970) / 10000);
								year = date.getFullYear();
								month = date.getMonth() + 1;
								day = date.getDate();
								break;
							case "'":
								if (lookAhead("'")) {
									checkLiteral();
								} else {
									literal = true;
								}
								break;
							default:
								checkLiteral();
						}
					}
				}
	
				if (iValue < value.length) {
					extra = value.substr(iValue);
					if (!/^\s+/.test(extra)) {
						throw "Extra/unparsed characters found in date: " + extra;
					}
				}
	
				if (year === -1) {
					year = new Date().getFullYear();
				} else if (year < 100) {
					year += new Date().getFullYear() - new Date().getFullYear() % 100 + (year <= shortYearCutoff ? 0 : -100);
				}
	
				if (doy > -1) {
					month = 1;
					day = doy;
					do {
						dim = this._getDaysInMonth(year, month - 1);
						if (day <= dim) {
							break;
						}
						month++;
						day -= dim;
					} while (true);
				}
	
				date = this._daylightSavingAdjust(new Date(year, month - 1, day));
				if (date.getFullYear() !== year || date.getMonth() + 1 !== month || date.getDate() !== day) {
					throw "Invalid date"; // E.g. 31/02/00
				}
				return date;
			},
	
			/* Standard date formats. */
			ATOM: "yy-mm-dd", // RFC 3339 (ISO 8601)
			COOKIE: "D, dd M yy",
			ISO_8601: "yy-mm-dd",
			RFC_822: "D, d M y",
			RFC_850: "DD, dd-M-y",
			RFC_1036: "D, d M y",
			RFC_1123: "D, d M yy",
			RFC_2822: "D, d M yy",
			RSS: "D, d M y", // RFC 822
			TICKS: "!",
			TIMESTAMP: "@",
			W3C: "yy-mm-dd", // ISO 8601
	
			_ticksTo1970: ((1970 - 1) * 365 + Math.floor(1970 / 4) - Math.floor(1970 / 100) + Math.floor(1970 / 400)) * 24 * 60 * 60 * 10000000,
	
			/* Format a date object into a string value.
	   * The format can be combinations of the following:
	   * d  - day of month (no leading zero)
	   * dd - day of month (two digit)
	   * o  - day of year (no leading zeros)
	   * oo - day of year (three digit)
	   * D  - day name short
	   * DD - day name long
	   * m  - month of year (no leading zero)
	   * mm - month of year (two digit)
	   * M  - month name short
	   * MM - month name long
	   * y  - year (two digit)
	   * yy - year (four digit)
	   * @ - Unix timestamp (ms since 01/01/1970)
	   * ! - Windows ticks (100ns since 01/01/0001)
	   * "..." - literal text
	   * '' - single quote
	   *
	   * @param  format string - the desired format of the date
	   * @param  date Date - the date value to format
	   * @param  settings Object - attributes include:
	   *					dayNamesShort	string[7] - abbreviated names of the days from Sunday (optional)
	   *					dayNames		string[7] - names of the days from Sunday (optional)
	   *					monthNamesShort string[12] - abbreviated names of the months (optional)
	   *					monthNames		string[12] - names of the months (optional)
	   * @return  string - the date in the above format
	   */
			formatDate: function formatDate(format, date, settings) {
				if (!date) {
					return "";
				}
	
				var iFormat,
				    dayNamesShort = (settings ? settings.dayNamesShort : null) || this._defaults.dayNamesShort,
				    dayNames = (settings ? settings.dayNames : null) || this._defaults.dayNames,
				    monthNamesShort = (settings ? settings.monthNamesShort : null) || this._defaults.monthNamesShort,
				    monthNames = (settings ? settings.monthNames : null) || this._defaults.monthNames,
	
				// Check whether a format character is doubled
				lookAhead = function lookAhead(match) {
					var matches = iFormat + 1 < format.length && format.charAt(iFormat + 1) === match;
					if (matches) {
						iFormat++;
					}
					return matches;
				},
	
				// Format a number, with leading zero if necessary
				formatNumber = function formatNumber(match, value, len) {
					var num = "" + value;
					if (lookAhead(match)) {
						while (num.length < len) {
							num = "0" + num;
						}
					}
					return num;
				},
	
				// Format a name, short or long as requested
				formatName = function formatName(match, value, shortNames, longNames) {
					return lookAhead(match) ? longNames[value] : shortNames[value];
				},
				    output = "",
				    literal = false;
	
				if (date) {
					for (iFormat = 0; iFormat < format.length; iFormat++) {
						if (literal) {
							if (format.charAt(iFormat) === "'" && !lookAhead("'")) {
								literal = false;
							} else {
								output += format.charAt(iFormat);
							}
						} else {
							switch (format.charAt(iFormat)) {
								case "d":
									output += formatNumber("d", date.getDate(), 2);
									break;
								case "D":
									output += formatName("D", date.getDay(), dayNamesShort, dayNames);
									break;
								case "o":
									output += formatNumber("o", Math.round((new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime() - new Date(date.getFullYear(), 0, 0).getTime()) / 86400000), 3);
									break;
								case "m":
									output += formatNumber("m", date.getMonth() + 1, 2);
									break;
								case "M":
									output += formatName("M", date.getMonth(), monthNamesShort, monthNames);
									break;
								case "y":
									output += lookAhead("y") ? date.getFullYear() : (date.getYear() % 100 < 10 ? "0" : "") + date.getYear() % 100;
									break;
								case "@":
									output += date.getTime();
									break;
								case "!":
									output += date.getTime() * 10000 + this._ticksTo1970;
									break;
								case "'":
									if (lookAhead("'")) {
										output += "'";
									} else {
										literal = true;
									}
									break;
								default:
									output += format.charAt(iFormat);
							}
						}
					}
				}
				return output;
			},
	
			/* Extract all possible characters from the date format. */
			_possibleChars: function _possibleChars(format) {
				var iFormat,
				    chars = "",
				    literal = false,
	
				// Check whether a format character is doubled
				lookAhead = function lookAhead(match) {
					var matches = iFormat + 1 < format.length && format.charAt(iFormat + 1) === match;
					if (matches) {
						iFormat++;
					}
					return matches;
				};
	
				for (iFormat = 0; iFormat < format.length; iFormat++) {
					if (literal) {
						if (format.charAt(iFormat) === "'" && !lookAhead("'")) {
							literal = false;
						} else {
							chars += format.charAt(iFormat);
						}
					} else {
						switch (format.charAt(iFormat)) {
							case "d":case "m":case "y":case "@":
								chars += "0123456789";
								break;
							case "D":case "M":
								return null; // Accept anything
							case "'":
								if (lookAhead("'")) {
									chars += "'";
								} else {
									literal = true;
								}
								break;
							default:
								chars += format.charAt(iFormat);
						}
					}
				}
				return chars;
			},
	
			/* Get a setting value, defaulting if necessary. */
			_get: function _get(inst, name) {
				return inst.settings[name] !== undefined ? inst.settings[name] : this._defaults[name];
			},
	
			/* Parse existing date and initialise date picker. */
			_setDateFromField: function _setDateFromField(inst, noDefault) {
				if (inst.input.val() === inst.lastVal) {
					return;
				}
	
				var dateFormat = this._get(inst, "dateFormat"),
				    dates = inst.lastVal = inst.input ? inst.input.val() : null,
				    defaultDate = this._getDefaultDate(inst),
				    date = defaultDate,
				    settings = this._getFormatConfig(inst);
	
				try {
					date = this.parseDate(dateFormat, dates, settings) || defaultDate;
				} catch (event) {
					dates = noDefault ? "" : dates;
				}
				inst.selectedDay = date.getDate();
				inst.drawMonth = inst.selectedMonth = date.getMonth();
				inst.drawYear = inst.selectedYear = date.getFullYear();
				inst.currentDay = dates ? date.getDate() : 0;
				inst.currentMonth = dates ? date.getMonth() : 0;
				inst.currentYear = dates ? date.getFullYear() : 0;
				this._adjustInstDate(inst);
			},
	
			/* Retrieve the default date shown on opening. */
			_getDefaultDate: function _getDefaultDate(inst) {
				return this._restrictMinMax(inst, this._determineDate(inst, this._get(inst, "defaultDate"), new Date()));
			},
	
			/* A date may be specified as an exact value or a relative one. */
			_determineDate: function _determineDate(inst, date, defaultDate) {
				var offsetNumeric = function offsetNumeric(offset) {
					var date = new Date();
					date.setDate(date.getDate() + offset);
					return date;
				},
				    offsetString = function offsetString(offset) {
					try {
						return $.datepicker.parseDate($.datepicker._get(inst, "dateFormat"), offset, $.datepicker._getFormatConfig(inst));
					} catch (e) {
						// Ignore
					}
	
					var date = (offset.toLowerCase().match(/^c/) ? $.datepicker._getDate(inst) : null) || new Date(),
					    year = date.getFullYear(),
					    month = date.getMonth(),
					    day = date.getDate(),
					    pattern = /([+\-]?[0-9]+)\s*(d|D|w|W|m|M|y|Y)?/g,
					    matches = pattern.exec(offset);
	
					while (matches) {
						switch (matches[2] || "d") {
							case "d":case "D":
								day += parseInt(matches[1], 10);break;
							case "w":case "W":
								day += parseInt(matches[1], 10) * 7;break;
							case "m":case "M":
								month += parseInt(matches[1], 10);
								day = Math.min(day, $.datepicker._getDaysInMonth(year, month));
								break;
							case "y":case "Y":
								year += parseInt(matches[1], 10);
								day = Math.min(day, $.datepicker._getDaysInMonth(year, month));
								break;
						}
						matches = pattern.exec(offset);
					}
					return new Date(year, month, day);
				},
				    newDate = date == null || date === "" ? defaultDate : typeof date === "string" ? offsetString(date) : typeof date === "number" ? isNaN(date) ? defaultDate : offsetNumeric(date) : new Date(date.getTime());
	
				newDate = newDate && newDate.toString() === "Invalid Date" ? defaultDate : newDate;
				if (newDate) {
					newDate.setHours(0);
					newDate.setMinutes(0);
					newDate.setSeconds(0);
					newDate.setMilliseconds(0);
				}
				return this._daylightSavingAdjust(newDate);
			},
	
			/* Handle switch to/from daylight saving.
	   * Hours may be non-zero on daylight saving cut-over:
	   * > 12 when midnight changeover, but then cannot generate
	   * midnight datetime, so jump to 1AM, otherwise reset.
	   * @param  date  (Date) the date to check
	   * @return  (Date) the corrected date
	   */
			_daylightSavingAdjust: function _daylightSavingAdjust(date) {
				if (!date) {
					return null;
				}
				date.setHours(date.getHours() > 12 ? date.getHours() + 2 : 0);
				return date;
			},
	
			/* Set the date(s) directly. */
			_setDate: function _setDate(inst, date, noChange) {
				var clear = !date,
				    origMonth = inst.selectedMonth,
				    origYear = inst.selectedYear,
				    newDate = this._restrictMinMax(inst, this._determineDate(inst, date, new Date()));
	
				inst.selectedDay = inst.currentDay = newDate.getDate();
				inst.drawMonth = inst.selectedMonth = inst.currentMonth = newDate.getMonth();
				inst.drawYear = inst.selectedYear = inst.currentYear = newDate.getFullYear();
				if ((origMonth !== inst.selectedMonth || origYear !== inst.selectedYear) && !noChange) {
					this._notifyChange(inst);
				}
				this._adjustInstDate(inst);
				if (inst.input) {
					inst.input.val(clear ? "" : this._formatDate(inst));
				}
			},
	
			/* Retrieve the date(s) directly. */
			_getDate: function _getDate(inst) {
				var startDate = !inst.currentYear || inst.input && inst.input.val() === "" ? null : this._daylightSavingAdjust(new Date(inst.currentYear, inst.currentMonth, inst.currentDay));
				return startDate;
			},
	
			/* Attach the onxxx handlers.  These are declared statically so
	   * they work with static code transformers like Caja.
	   */
			_attachHandlers: function _attachHandlers(inst) {
				var stepMonths = this._get(inst, "stepMonths"),
				    id = "#" + inst.id.replace(/\\\\/g, "\\");
				inst.dpDiv.find("[data-handler]").map(function () {
					var handler = {
						prev: function prev() {
							$.datepicker._adjustDate(id, -stepMonths, "M");
						},
						next: function next() {
							$.datepicker._adjustDate(id, +stepMonths, "M");
						},
						hide: function hide() {
							$.datepicker._hideDatepicker();
						},
						today: function today() {
							$.datepicker._gotoToday(id);
						},
						selectDay: function selectDay() {
							$.datepicker._selectDay(id, +this.getAttribute("data-month"), +this.getAttribute("data-year"), this);
							return false;
						},
						selectMonth: function selectMonth() {
							$.datepicker._selectMonthYear(id, this, "M");
							return false;
						},
						selectYear: function selectYear() {
							$.datepicker._selectMonthYear(id, this, "Y");
							return false;
						}
					};
					$(this).bind(this.getAttribute("data-event"), handler[this.getAttribute("data-handler")]);
				});
			},
	
			/* Generate the HTML for the current state of the date picker. */
			_generateHTML: function _generateHTML(inst) {
				var maxDraw,
				    prevText,
				    prev,
				    nextText,
				    next,
				    currentText,
				    gotoDate,
				    controls,
				    buttonPanel,
				    firstDay,
				    showWeek,
				    dayNames,
				    dayNamesMin,
				    monthNames,
				    monthNamesShort,
				    beforeShowDay,
				    showOtherMonths,
				    selectOtherMonths,
				    defaultDate,
				    html,
				    dow,
				    row,
				    group,
				    col,
				    selectedDate,
				    cornerClass,
				    calender,
				    thead,
				    day,
				    daysInMonth,
				    leadDays,
				    curRows,
				    numRows,
				    printDate,
				    dRow,
				    tbody,
				    daySettings,
				    otherMonth,
				    unselectable,
				    tempDate = new Date(),
				    today = this._daylightSavingAdjust(new Date(tempDate.getFullYear(), tempDate.getMonth(), tempDate.getDate())),
				    // clear time
				isRTL = this._get(inst, "isRTL"),
				    showButtonPanel = this._get(inst, "showButtonPanel"),
				    hideIfNoPrevNext = this._get(inst, "hideIfNoPrevNext"),
				    navigationAsDateFormat = this._get(inst, "navigationAsDateFormat"),
				    numMonths = this._getNumberOfMonths(inst),
				    showCurrentAtPos = this._get(inst, "showCurrentAtPos"),
				    stepMonths = this._get(inst, "stepMonths"),
				    isMultiMonth = numMonths[0] !== 1 || numMonths[1] !== 1,
				    currentDate = this._daylightSavingAdjust(!inst.currentDay ? new Date(9999, 9, 9) : new Date(inst.currentYear, inst.currentMonth, inst.currentDay)),
				    minDate = this._getMinMaxDate(inst, "min"),
				    maxDate = this._getMinMaxDate(inst, "max"),
				    drawMonth = inst.drawMonth - showCurrentAtPos,
				    drawYear = inst.drawYear;
	
				if (drawMonth < 0) {
					drawMonth += 12;
					drawYear--;
				}
				if (maxDate) {
					maxDraw = this._daylightSavingAdjust(new Date(maxDate.getFullYear(), maxDate.getMonth() - numMonths[0] * numMonths[1] + 1, maxDate.getDate()));
					maxDraw = minDate && maxDraw < minDate ? minDate : maxDraw;
					while (this._daylightSavingAdjust(new Date(drawYear, drawMonth, 1)) > maxDraw) {
						drawMonth--;
						if (drawMonth < 0) {
							drawMonth = 11;
							drawYear--;
						}
					}
				}
				inst.drawMonth = drawMonth;
				inst.drawYear = drawYear;
	
				prevText = this._get(inst, "prevText");
				prevText = !navigationAsDateFormat ? prevText : this.formatDate(prevText, this._daylightSavingAdjust(new Date(drawYear, drawMonth - stepMonths, 1)), this._getFormatConfig(inst));
	
				prev = this._canAdjustMonth(inst, -1, drawYear, drawMonth) ? "<a class='ui-datepicker-prev ui-corner-all' data-handler='prev' data-event='click'" + " title='" + prevText + "'><span class='ui-icon ui-icon-circle-triangle-" + (isRTL ? "e" : "w") + "'>" + prevText + "</span></a>" : hideIfNoPrevNext ? "" : "<a class='ui-datepicker-prev ui-corner-all ui-state-disabled' title='" + prevText + "'><span class='ui-icon ui-icon-circle-triangle-" + (isRTL ? "e" : "w") + "'>" + prevText + "</span></a>";
	
				nextText = this._get(inst, "nextText");
				nextText = !navigationAsDateFormat ? nextText : this.formatDate(nextText, this._daylightSavingAdjust(new Date(drawYear, drawMonth + stepMonths, 1)), this._getFormatConfig(inst));
	
				next = this._canAdjustMonth(inst, +1, drawYear, drawMonth) ? "<a class='ui-datepicker-next ui-corner-all' data-handler='next' data-event='click'" + " title='" + nextText + "'><span class='ui-icon ui-icon-circle-triangle-" + (isRTL ? "w" : "e") + "'>" + nextText + "</span></a>" : hideIfNoPrevNext ? "" : "<a class='ui-datepicker-next ui-corner-all ui-state-disabled' title='" + nextText + "'><span class='ui-icon ui-icon-circle-triangle-" + (isRTL ? "w" : "e") + "'>" + nextText + "</span></a>";
	
				currentText = this._get(inst, "currentText");
				gotoDate = this._get(inst, "gotoCurrent") && inst.currentDay ? currentDate : today;
				currentText = !navigationAsDateFormat ? currentText : this.formatDate(currentText, gotoDate, this._getFormatConfig(inst));
	
				controls = !inst.inline ? "<button type='button' class='ui-datepicker-close ui-state-default ui-priority-primary ui-corner-all' data-handler='hide' data-event='click'>" + this._get(inst, "closeText") + "</button>" : "";
	
				buttonPanel = showButtonPanel ? "<div class='ui-datepicker-buttonpane ui-widget-content'>" + (isRTL ? controls : "") + (this._isInRange(inst, gotoDate) ? "<button type='button' class='ui-datepicker-current ui-state-default ui-priority-secondary ui-corner-all' data-handler='today' data-event='click'" + ">" + currentText + "</button>" : "") + (isRTL ? "" : controls) + "</div>" : "";
	
				firstDay = parseInt(this._get(inst, "firstDay"), 10);
				firstDay = isNaN(firstDay) ? 0 : firstDay;
	
				showWeek = this._get(inst, "showWeek");
				dayNames = this._get(inst, "dayNames");
				dayNamesMin = this._get(inst, "dayNamesMin");
				monthNames = this._get(inst, "monthNames");
				monthNamesShort = this._get(inst, "monthNamesShort");
				beforeShowDay = this._get(inst, "beforeShowDay");
				showOtherMonths = this._get(inst, "showOtherMonths");
				selectOtherMonths = this._get(inst, "selectOtherMonths");
				defaultDate = this._getDefaultDate(inst);
				html = "";
				dow;
				for (row = 0; row < numMonths[0]; row++) {
					group = "";
					this.maxRows = 4;
					for (col = 0; col < numMonths[1]; col++) {
						selectedDate = this._daylightSavingAdjust(new Date(drawYear, drawMonth, inst.selectedDay));
						cornerClass = " ui-corner-all";
						calender = "";
						if (isMultiMonth) {
							calender += "<div class='ui-datepicker-group";
							if (numMonths[1] > 1) {
								switch (col) {
									case 0:
										calender += " ui-datepicker-group-first";
										cornerClass = " ui-corner-" + (isRTL ? "right" : "left");break;
									case numMonths[1] - 1:
										calender += " ui-datepicker-group-last";
										cornerClass = " ui-corner-" + (isRTL ? "left" : "right");break;
									default:
										calender += " ui-datepicker-group-middle";cornerClass = "";break;
								}
							}
							calender += "'>";
						}
						calender += "<div class='ui-datepicker-header ui-widget-header ui-helper-clearfix" + cornerClass + "'>" + (/all|left/.test(cornerClass) && row === 0 ? isRTL ? next : prev : "") + (/all|right/.test(cornerClass) && row === 0 ? isRTL ? prev : next : "") + this._generateMonthYearHeader(inst, drawMonth, drawYear, minDate, maxDate, row > 0 || col > 0, monthNames, monthNamesShort) + // draw month headers
						"</div><table class='ui-datepicker-calendar'><thead>" + "<tr>";
						thead = showWeek ? "<th class='ui-datepicker-week-col'>" + this._get(inst, "weekHeader") + "</th>" : "";
						for (dow = 0; dow < 7; dow++) {
							// days of the week
							day = (dow + firstDay) % 7;
							thead += "<th scope='col'" + ((dow + firstDay + 6) % 7 >= 5 ? " class='ui-datepicker-week-end'" : "") + ">" + "<span title='" + dayNames[day] + "'>" + dayNamesMin[day] + "</span></th>";
						}
						calender += thead + "</tr></thead><tbody>";
						daysInMonth = this._getDaysInMonth(drawYear, drawMonth);
						if (drawYear === inst.selectedYear && drawMonth === inst.selectedMonth) {
							inst.selectedDay = Math.min(inst.selectedDay, daysInMonth);
						}
						leadDays = (this._getFirstDayOfMonth(drawYear, drawMonth) - firstDay + 7) % 7;
						curRows = Math.ceil((leadDays + daysInMonth) / 7); // calculate the number of rows to generate
						numRows = isMultiMonth ? this.maxRows > curRows ? this.maxRows : curRows : curRows; //If multiple months, use the higher number of rows (see #7043)
						this.maxRows = numRows;
						printDate = this._daylightSavingAdjust(new Date(drawYear, drawMonth, 1 - leadDays));
						for (dRow = 0; dRow < numRows; dRow++) {
							// create date picker rows
							calender += "<tr>";
							tbody = !showWeek ? "" : "<td class='ui-datepicker-week-col'>" + this._get(inst, "calculateWeek")(printDate) + "</td>";
							for (dow = 0; dow < 7; dow++) {
								// create date picker days
								daySettings = beforeShowDay ? beforeShowDay.apply(inst.input ? inst.input[0] : null, [printDate]) : [true, ""];
								otherMonth = printDate.getMonth() !== drawMonth;
								unselectable = otherMonth && !selectOtherMonths || !daySettings[0] || minDate && printDate < minDate || maxDate && printDate > maxDate;
								tbody += "<td class='" + ((dow + firstDay + 6) % 7 >= 5 ? " ui-datepicker-week-end" : "") + ( // highlight weekends
								otherMonth ? " ui-datepicker-other-month" : "") + ( // highlight days from other months
								printDate.getTime() === selectedDate.getTime() && drawMonth === inst.selectedMonth && inst._keyEvent || // user pressed key
								defaultDate.getTime() === printDate.getTime() && defaultDate.getTime() === selectedDate.getTime() ?
								// or defaultDate is current printedDate and defaultDate is selectedDate
								" " + this._dayOverClass : "") + ( // highlight selected day
								unselectable ? " " + this._unselectableClass + " ui-state-disabled" : "") + ( // highlight unselectable days
								otherMonth && !showOtherMonths ? "" : " " + daySettings[1] + ( // highlight custom dates
								printDate.getTime() === currentDate.getTime() ? " " + this._currentClass : "") + ( // highlight selected day
								printDate.getTime() === today.getTime() ? " ui-datepicker-today" : "")) + "'" + ( // highlight today (if different)
								(!otherMonth || showOtherMonths) && daySettings[2] ? " title='" + daySettings[2].replace(/'/g, "&#39;") + "'" : "") + ( // cell title
								unselectable ? "" : " data-handler='selectDay' data-event='click' data-month='" + printDate.getMonth() + "' data-year='" + printDate.getFullYear() + "'") + ">" + ( // actions
								otherMonth && !showOtherMonths ? "&#xa0;" : // display for other months
								unselectable ? "<span class='ui-state-default'>" + printDate.getDate() + "</span>" : "<a class='ui-state-default" + (printDate.getTime() === today.getTime() ? " ui-state-highlight" : "") + (printDate.getTime() === currentDate.getTime() ? " ui-state-active" : "") + ( // highlight selected day
								otherMonth ? " ui-priority-secondary" : "") + // distinguish dates from other months
								"' href='#'>" + printDate.getDate() + "</a>") + "</td>"; // display selectable date
								printDate.setDate(printDate.getDate() + 1);
								printDate = this._daylightSavingAdjust(printDate);
							}
							calender += tbody + "</tr>";
						}
						drawMonth++;
						if (drawMonth > 11) {
							drawMonth = 0;
							drawYear++;
						}
						calender += "</tbody></table>" + (isMultiMonth ? "</div>" + (numMonths[0] > 0 && col === numMonths[1] - 1 ? "<div class='ui-datepicker-row-break'></div>" : "") : "");
						group += calender;
					}
					html += group;
				}
				html += buttonPanel;
				inst._keyEvent = false;
				return html;
			},
	
			/* Generate the month and year header. */
			_generateMonthYearHeader: function _generateMonthYearHeader(inst, drawMonth, drawYear, minDate, maxDate, secondary, monthNames, monthNamesShort) {
	
				var inMinYear,
				    inMaxYear,
				    month,
				    years,
				    thisYear,
				    determineYear,
				    year,
				    endYear,
				    changeMonth = this._get(inst, "changeMonth"),
				    changeYear = this._get(inst, "changeYear"),
				    showMonthAfterYear = this._get(inst, "showMonthAfterYear"),
				    html = "<div class='ui-datepicker-title'>",
				    monthHtml = "";
	
				// month selection
				if (secondary || !changeMonth) {
					monthHtml += "<span class='ui-datepicker-month'>" + monthNames[drawMonth] + "</span>";
				} else {
					inMinYear = minDate && minDate.getFullYear() === drawYear;
					inMaxYear = maxDate && maxDate.getFullYear() === drawYear;
					monthHtml += "<select class='ui-datepicker-month' data-handler='selectMonth' data-event='change'>";
					for (month = 0; month < 12; month++) {
						if ((!inMinYear || month >= minDate.getMonth()) && (!inMaxYear || month <= maxDate.getMonth())) {
							monthHtml += "<option value='" + month + "'" + (month === drawMonth ? " selected='selected'" : "") + ">" + monthNamesShort[month] + "</option>";
						}
					}
					monthHtml += "</select>";
				}
	
				if (!showMonthAfterYear) {
					html += monthHtml + (secondary || !(changeMonth && changeYear) ? "&#xa0;" : "");
				}
	
				// year selection
				if (!inst.yearshtml) {
					inst.yearshtml = "";
					if (secondary || !changeYear) {
						html += "<span class='ui-datepicker-year'>" + drawYear + "</span>";
					} else {
						// determine range of years to display
						years = this._get(inst, "yearRange").split(":");
						thisYear = new Date().getFullYear();
						determineYear = function determineYear(value) {
							var year = value.match(/c[+\-].*/) ? drawYear + parseInt(value.substring(1), 10) : value.match(/[+\-].*/) ? thisYear + parseInt(value, 10) : parseInt(value, 10);
							return isNaN(year) ? thisYear : year;
						};
						year = determineYear(years[0]);
						endYear = Math.max(year, determineYear(years[1] || ""));
						year = minDate ? Math.max(year, minDate.getFullYear()) : year;
						endYear = maxDate ? Math.min(endYear, maxDate.getFullYear()) : endYear;
						inst.yearshtml += "<select class='ui-datepicker-year' data-handler='selectYear' data-event='change'>";
						for (; year <= endYear; year++) {
							inst.yearshtml += "<option value='" + year + "'" + (year === drawYear ? " selected='selected'" : "") + ">" + year + "</option>";
						}
						inst.yearshtml += "</select>";
	
						html += inst.yearshtml;
						inst.yearshtml = null;
					}
				}
	
				html += this._get(inst, "yearSuffix");
				if (showMonthAfterYear) {
					html += (secondary || !(changeMonth && changeYear) ? "&#xa0;" : "") + monthHtml;
				}
				html += "</div>"; // Close datepicker_header
				return html;
			},
	
			/* Adjust one of the date sub-fields. */
			_adjustInstDate: function _adjustInstDate(inst, offset, period) {
				var year = inst.drawYear + (period === "Y" ? offset : 0),
				    month = inst.drawMonth + (period === "M" ? offset : 0),
				    day = Math.min(inst.selectedDay, this._getDaysInMonth(year, month)) + (period === "D" ? offset : 0),
				    date = this._restrictMinMax(inst, this._daylightSavingAdjust(new Date(year, month, day)));
	
				inst.selectedDay = date.getDate();
				inst.drawMonth = inst.selectedMonth = date.getMonth();
				inst.drawYear = inst.selectedYear = date.getFullYear();
				if (period === "M" || period === "Y") {
					this._notifyChange(inst);
				}
			},
	
			/* Ensure a date is within any min/max bounds. */
			_restrictMinMax: function _restrictMinMax(inst, date) {
				var minDate = this._getMinMaxDate(inst, "min"),
				    maxDate = this._getMinMaxDate(inst, "max"),
				    newDate = minDate && date < minDate ? minDate : date;
				return maxDate && newDate > maxDate ? maxDate : newDate;
			},
	
			/* Notify change of month/year. */
			_notifyChange: function _notifyChange(inst) {
				var onChange = this._get(inst, "onChangeMonthYear");
				if (onChange) {
					onChange.apply(inst.input ? inst.input[0] : null, [inst.selectedYear, inst.selectedMonth + 1, inst]);
				}
			},
	
			/* Determine the number of months to show. */
			_getNumberOfMonths: function _getNumberOfMonths(inst) {
				var numMonths = this._get(inst, "numberOfMonths");
				return numMonths == null ? [1, 1] : typeof numMonths === "number" ? [1, numMonths] : numMonths;
			},
	
			/* Determine the current maximum date - ensure no time components are set. */
			_getMinMaxDate: function _getMinMaxDate(inst, minMax) {
				return this._determineDate(inst, this._get(inst, minMax + "Date"), null);
			},
	
			/* Find the number of days in a given month. */
			_getDaysInMonth: function _getDaysInMonth(year, month) {
				return 32 - this._daylightSavingAdjust(new Date(year, month, 32)).getDate();
			},
	
			/* Find the day of the week of the first of a month. */
			_getFirstDayOfMonth: function _getFirstDayOfMonth(year, month) {
				return new Date(year, month, 1).getDay();
			},
	
			/* Determines if we should allow a "next/prev" month display change. */
			_canAdjustMonth: function _canAdjustMonth(inst, offset, curYear, curMonth) {
				var numMonths = this._getNumberOfMonths(inst),
				    date = this._daylightSavingAdjust(new Date(curYear, curMonth + (offset < 0 ? offset : numMonths[0] * numMonths[1]), 1));
	
				if (offset < 0) {
					date.setDate(this._getDaysInMonth(date.getFullYear(), date.getMonth()));
				}
				return this._isInRange(inst, date);
			},
	
			/* Is the given date in the accepted range? */
			_isInRange: function _isInRange(inst, date) {
				var yearSplit,
				    currentYear,
				    minDate = this._getMinMaxDate(inst, "min"),
				    maxDate = this._getMinMaxDate(inst, "max"),
				    minYear = null,
				    maxYear = null,
				    years = this._get(inst, "yearRange");
				if (years) {
					yearSplit = years.split(":");
					currentYear = new Date().getFullYear();
					minYear = parseInt(yearSplit[0], 10);
					maxYear = parseInt(yearSplit[1], 10);
					if (yearSplit[0].match(/[+\-].*/)) {
						minYear += currentYear;
					}
					if (yearSplit[1].match(/[+\-].*/)) {
						maxYear += currentYear;
					}
				}
	
				return (!minDate || date.getTime() >= minDate.getTime()) && (!maxDate || date.getTime() <= maxDate.getTime()) && (!minYear || date.getFullYear() >= minYear) && (!maxYear || date.getFullYear() <= maxYear);
			},
	
			/* Provide the configuration settings for formatting/parsing. */
			_getFormatConfig: function _getFormatConfig(inst) {
				var shortYearCutoff = this._get(inst, "shortYearCutoff");
				shortYearCutoff = typeof shortYearCutoff !== "string" ? shortYearCutoff : new Date().getFullYear() % 100 + parseInt(shortYearCutoff, 10);
				return { shortYearCutoff: shortYearCutoff,
					dayNamesShort: this._get(inst, "dayNamesShort"), dayNames: this._get(inst, "dayNames"),
					monthNamesShort: this._get(inst, "monthNamesShort"), monthNames: this._get(inst, "monthNames") };
			},
	
			/* Format the given date for display. */
			_formatDate: function _formatDate(inst, day, month, year) {
				if (!day) {
					inst.currentDay = inst.selectedDay;
					inst.currentMonth = inst.selectedMonth;
					inst.currentYear = inst.selectedYear;
				}
				var date = day ? (typeof day === "undefined" ? "undefined" : _typeof(day)) === "object" ? day : this._daylightSavingAdjust(new Date(year, month, day)) : this._daylightSavingAdjust(new Date(inst.currentYear, inst.currentMonth, inst.currentDay));
				return this.formatDate(this._get(inst, "dateFormat"), date, this._getFormatConfig(inst));
			}
		});
	
		/*
	  * Bind hover events for datepicker elements.
	  * Done via delegate so the binding only occurs once in the lifetime of the parent div.
	  * Global datepicker_instActive, set by _updateDatepicker allows the handlers to find their way back to the active picker.
	  */
		function datepicker_bindHover(dpDiv) {
			var selector = "button, .ui-datepicker-prev, .ui-datepicker-next, .ui-datepicker-calendar td a";
			return dpDiv.delegate(selector, "mouseout", function () {
				$(this).removeClass("ui-state-hover");
				if (this.className.indexOf("ui-datepicker-prev") !== -1) {
					$(this).removeClass("ui-datepicker-prev-hover");
				}
				if (this.className.indexOf("ui-datepicker-next") !== -1) {
					$(this).removeClass("ui-datepicker-next-hover");
				}
			}).delegate(selector, "mouseover", datepicker_handleMouseover);
		}
	
		function datepicker_handleMouseover() {
			if (!$.datepicker._isDisabledDatepicker(datepicker_instActive.inline ? datepicker_instActive.dpDiv.parent()[0] : datepicker_instActive.input[0])) {
				$(this).parents(".ui-datepicker-calendar").find("a").removeClass("ui-state-hover");
				$(this).addClass("ui-state-hover");
				if (this.className.indexOf("ui-datepicker-prev") !== -1) {
					$(this).addClass("ui-datepicker-prev-hover");
				}
				if (this.className.indexOf("ui-datepicker-next") !== -1) {
					$(this).addClass("ui-datepicker-next-hover");
				}
			}
		}
	
		/* jQuery extend now ignores nulls! */
		function datepicker_extendRemove(target, props) {
			$.extend(target, props);
			for (var name in props) {
				if (props[name] == null) {
					target[name] = props[name];
				}
			}
			return target;
		}
	
		/* Invoke the datepicker functionality.
	    @param  options  string - a command, optionally followed by additional parameters or
	 					Object - settings for attaching new datepicker functionality
	    @return  jQuery object */
		$.fn.datepicker = function (options) {
	
			/* Verify an empty collection wasn't passed - Fixes #6976 */
			if (!this.length) {
				return this;
			}
	
			/* Initialise the date picker. */
			if (!$.datepicker.initialized) {
				$(document).mousedown($.datepicker._checkExternalClick);
				$.datepicker.initialized = true;
			}
	
			/* Append datepicker main container to body if not exist. */
			if ($("#" + $.datepicker._mainDivId).length === 0) {
				$("body").append($.datepicker.dpDiv);
			}
	
			var otherArgs = Array.prototype.slice.call(arguments, 1);
			if (typeof options === "string" && (options === "isDisabled" || options === "getDate" || options === "widget")) {
				return $.datepicker["_" + options + "Datepicker"].apply($.datepicker, [this[0]].concat(otherArgs));
			}
			if (options === "option" && arguments.length === 2 && typeof arguments[1] === "string") {
				return $.datepicker["_" + options + "Datepicker"].apply($.datepicker, [this[0]].concat(otherArgs));
			}
			return this.each(function () {
				typeof options === "string" ? $.datepicker["_" + options + "Datepicker"].apply($.datepicker, [this].concat(otherArgs)) : $.datepicker._attachDatepicker(this, options);
			});
		};
	
		$.datepicker = new Datepicker(); // singleton instance
		$.datepicker.initialized = false;
		$.datepicker.uuid = new Date().getTime();
		$.datepicker.version = "1.11.2";
	
		var datepicker = $.datepicker;
	});

/***/ },
/* 11 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function(jQuery) {'use strict';
	
	// A jQuery function for handling the submission
	// of forms that require a Stripe token.
	// Tokens are obtained by using the Stripe Checkout library.
	// When the form is submitted, we want to raise a Stripe Checkout window.
	// The successful submission of this form will return a token, which we will
	// add back to the form before resubmitting it.
	
	(function ($) {
	
	    var $form = null;
	
	    function formValue(name, newValue) {
	        // Return the value of the form field matching the given name.
	        // If a new value is given, set the value of the field before returning it.
	        var selector = '[name=' + name + ']';
	        var element = $form.find(selector);
	        if (typeof newValue !== 'undefined') {
	            element.val(newValue);
	        }
	        return element.val();
	    }
	
	    function handleToken(token) {
	        // Set the value of the form's token and the email
	        // fields based on the token received by this method
	        formValue('stripe_token', token.id);
	        formValue('stripe_email', token.email);
	        // We submit the form once the token is in place.
	        // As long as the token is added to the form,
	        // it will submit successfully.
	        $form.submit();
	    }
	
	    function handleCheckout(form) {
	        console.log('Using Stripe Checkout to obtain token...');
	        var key = formValue('stripe_pk'),
	            image = formValue('stripe_image'),
	            label = formValue('stripe_label'),
	            description = formValue('stripe_description'),
	            amount = formValue('stripe_amount'),
	            fee = formValue('stripe_fee'),
	            email = formValue('stripe_email'),
	            bitcoin = formValue('stripe_bitcoin'),
	            name = 'MuckRock';
	        amount = parseInt(amount);
	        fee = parseFloat(fee);
	        if (fee > 0) {
	            amount += amount * fee;
	        }
	        var settings = {
	            key: key,
	            image: image,
	            name: 'MuckRock',
	            description: description,
	            amount: amount,
	            email: email,
	            panelLabel: label,
	            token: handleToken,
	            bitcoin: bitcoin
	        };
	        StripeCheckout.open(settings);
	    }
	
	    $.fn.checkout = function () {
	        // We bind a submit event handler for any element
	        // registered with this plugin.
	        $(this).submit(function (event) {
	            // Upon submission, we set this plugin's global
	            // $form variable. This ensures that the other
	            // plugin methods can act freely on just this form.
	            $form = $(this);
	            // We only submit the form when it has a token.
	            // If it doesn't have a token, we will block the
	            // submission and call the handleCheckout method,
	            // which will add a token before resubmitting the form.
	            if (formValue('stripe_token')) {
	                console.log('Obtained Stripe token, submitting form...');
	                return true;
	            } else {
	                event.stopImmediatePropagation();
	                event.preventDefault();
	                handleCheckout(this);
	                return false;
	            }
	        });
	    };
	})(jQuery);
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 12 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function(jQuery) {'use strict';
	
	// A jQuery function for turning a number
	// input into a pretty currency input.
	
	(function ($) {
	    $.fn.currencyField = function () {
	        if (this.length < 1) {
	            return;
	        }
	        // we want to replace the input with a
	        // currency input that automatically
	        // formats and controls inputs
	        var $input = $(this);
	        var $currency = $('<input type="text"/>');
	        var amount = $input.attr('value');
	        // set up the currency field with attributes
	        // and use the autoNumeric plugin on it
	        $currency.attr('name', 'pretty-input').addClass('currency');
	        $currency.autoNumeric('init', { aSign: '$', pSign: 'p' });
	        $currency.autoNumeric('set', amount / 100.00);
	        // we want to copy all the input to the currency field
	        // back to the original amount field, since that is what
	        // will ultimately be submitted
	        function copyValue() {
	            var value = $currency.autoNumeric('get') * 100;
	            $input.attr('value', value);
	        }
	        $currency.keyup(copyValue);
	        // swap out the input with the currency field
	        $currency.insertBefore($input);
	        $input.attr('hidden', true).hide();
	        console.log('Applied currency field to:', $input);
	        return $input;
	    };
	})(jQuery);
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 13 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function(jQuery) {'use strict';
	
	(function ($) {
	
	    function crowdfundAjax(event) {
	        // get the form and the widget state overlays
	        var form = $(this);
	        var overlays = form.parents('.crowdfund').children('.overlay');
	
	        var fields = form.serializeArray();
	        var data = {};
	        $(fields).map(function (index, field) {
	            data[field.name] = field.value;
	        });
	
	        // track this event using Google Analytics
	        ga('send', 'event', 'Crowdfund', 'Donation', window.location.pathname);
	
	        $(document).ajaxStart(function () {
	            overlays.filter('.pending').addClass('visible');
	        }).ajaxError(function () {
	            console.error('AJAX error!');
	            overlays.filter('.pending').removeClass('visible');
	            overlays.filter('.error').addClass('visible');
	            $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
	        }).ajaxComplete(function (e) {
	            console.log('Contributed to crowdfund.');
	            overlays.filter('.pending').removeClass('visible');
	            overlays.filter('.complete').addClass('visible');
	            $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
	        });
	
	        $.ajax({
	            url: form.attr('action'),
	            type: form.attr('method'),
	            data: data,
	            success: null,
	            dataType: 'json'
	        });
	
	        event.preventDefault();
	        return false;
	    }
	
	    $.fn.crowdfund = function () {
	        $(this).submit(crowdfundAjax);
	    };
	})(jQuery);
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 14 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	function showCommForm(selector) {
	    $('.options.dropdown').removeClass('visible');
	    $('.communication-actions').show();
	    $(selector).addClass('visible').siblings().removeClass('visible');
	    $(selector).find('button.cancel').click(function (e) {
	        e.preventDefault();
	        $(selector).removeClass('visible');
	        $('.communication-actions').hide();
	    });
	}
	
	$('.communication-header').click(function () {
	    $(this).closest('.communication').toggleClass('collapsed');
	});
	
	$('.communication-header').find('a').click(function () {
	    window.location.href = $(this).attr('href');
	    return false;
	});
	
	$('.communication-header').find('.dropdown-list').click(function () {
	    return false;
	});
	
	$('.communication .options .svgIcon').click(function () {
	    var thisDropdown = $(this).closest('.options.dropdown');
	    var thisDropdownMenu = $(thisDropdown).find('.dropdown-list');
	    var allOtherCommunications = $(thisDropdown).closest('.communication').siblings();
	    var allOtherDropdowns = $(allOtherCommunications).find('.options.dropdown');
	    $(allOtherDropdowns).removeClass('visible');
	    $(thisDropdown).toggleClass('visible');
	    $(document).click(function (e) {
	        $(thisDropdown).removeClass('visible');
	    });
	    return false;
	});
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 15 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	$('.hidden-reply').hide();
	$('.embed textarea').trigger('autosize.destroy');
	
	function textAreaModal(nextSelector) {
	    modal(nextSelector);
	    $('<textarea name="text"></textarea>').insertBefore(nextSelector.children('button'));
	    $('#modal-overlay').click(function () {
	        console.log('Click!');
	        nextSelector.children('textarea').remove();
	    });
	    $('.close-modal').click(function () {
	        nextSelector.children('textarea').remove();
	    });
	}
	
	function textAreaReply(nextSelector) {
	    console.log(nextSelector);
	    nextSelector.show();
	    $('.reply-button').hide();
	    $('.modal-button').hide();
	    nextSelector.siblings('.hidden-reply:visible').hide();
	    if (nextSelector.children('textarea').length == 0) {
	        $('<textarea name="text"></textarea>').insertBefore(nextSelector.children('.buttons'));
	    }
	    nextSelector.children('.buttons').children('.close-reply').click(function () {
	        nextSelector.hide();
	        nextSelector.children('textarea').remove();
	        $('.reply-button').show();
	        $('.modal-button').show();
	    });
	}
	
	function get_thumbnail(doc_id) {
	    var idx = doc_id.indexOf('-');
	    var num = doc_id.slice(0, idx);
	    var name = doc_id.slice(idx + 1);
	    return 'https://s3.amazonaws.com/s3.documentcloud.org/documents/' + num + '/pages/' + name + '-p1-small.gif';
	}
	
	/* Side Bar */
	
	$('#toggle-specific-information').click(function (e) {
	    e.preventDefault();
	    $('.specific-information').toggleClass('visible');
	    if ($(this).data('state') == 0) {
	        $(this).data('state', 1);
	        $(this).text('Hide details');
	    } else {
	        $(this).data('state', 0);
	        $(this).text('Show details');
	    }
	});
	
	$('.estimated-completion .edit').click(function () {
	    var button = $(this);
	    $('.dates').hide();
	    $('.change-date').addClass('visible');
	    $('.change-date .cancel').click(function (e) {
	        e.preventDefault();
	        $('.change-date').removeClass('visible');
	        $('.dates').show();
	        $(button).show();
	    });
	});
	
	/* Communications */
	
	$('#toggle-communication-collapse').click(function () {
	    var onText = 'Expand All';
	    var offText = 'Collapse All';
	    var state = $(this).data('state');
	    var communications = $('.communications .communication');
	    if (state === 0) {
	        communications.addClass('collapsed');
	        $(this).data('state', 1);
	        $(this).text(onText);
	    } else {
	        communications.removeClass('collapsed');
	        $(this).data('state', 0);
	        $(this).text(offText);
	    }
	});
	
	/* Request action composer */
	
	var composerInputs = $('.composer-input');
	
	function showComposer(id) {
	    // if no id provided, use the inactive panel
	    id = !id ? '#inactive' : id;
	    // hide all the composers, then filter to
	    // the one we're interested in and show it
	    var composer = composerInputs.hide().filter(id).show();
	    // We also want to bring the composer's first input into focus
	    // in order to make it clear to the user that this is actionable
	    composer.find(':text,textarea,select').filter(':visible:first').focus();
	    console.log('Switched to composer: ', id);
	}
	
	// Bind to hashchange event
	$(window).on('hashchange', function () {
	    // check if the hash is a target
	    var hash = location.hash;
	    var composers = composerInputs.filter(hash);
	    if (composers.length > 0) {
	        showComposer(hash);
	    }
	});
	
	// Initialize
	$(document).ready(function () {
	    showComposer(composerInputs.filter(location.hash).length > 0 ? location.hash : '');
	});
	
	/* Documents */
	
	function displayFile(file) {
	    var activeFile = $('.active-document');
	    var files = $('.file');
	    if (!file) {
	        return;
	    }
	    var title = file.data('title');
	    var docId = file.data('doc-id');
	    if (!title) {
	        title = 'Untitled';
	    }
	    $('#doc-title').empty().text(title);
	    // remove the active class from all the list items,
	    // then apply active class to this file's list item
	    files.parent('li').removeClass('active');
	    files.filter(file).parent('li').addClass('active');
	    docCloudSettings = { sidebar: false, container: "#viewer" };
	    DV.load('https://www.documentcloud.org/documents/' + docId + '.js', docCloudSettings);
	    activeFile.addClass('visible');
	    window.scrollTo(0, activeFile.offset().top);
	}
	
	$('.view-file').click(function () {
	    // We force a hashchange when the view-file link is clicked.
	    $(window).trigger('hashchange');
	    window.scrollTo(0, $('.active-document').offset().top);
	});
	
	$('.active-document').find('.cancel.button').click(function () {
	    var activeFile = $('.active-document');
	    var files = $('.file');
	    $('#viewer').empty();
	    activeFile.removeClass('visible');
	    files.parent('li').removeClass('active');
	    console.log('Closed file');
	});
	
	$('.toggle-embed').click(function () {
	    var file = $(this).closest('.file');
	    var embed = $(file).find('.file-embed');
	    $(embed).toggleClass('visible');
	    $(embed).children('textarea').select();
	    $(embed).children('.close-embed').click(function () {
	        $(embed).removeClass('visible');
	    });
	});
	
	/* Notes */
	
	$('.note-header').click(function () {
	    $(this).parent().toggleClass('collapsed');
	});
	
	/* Sharing */
	
	var foiaId = $('.request.detail').attr('id');
	if (foiaId != undefined) {
	    foiaId = foiaId.substring(foiaId.indexOf('-') + 1);
	}
	if ($('#id_users-autocomplete').length) {
	    $('#id_users-autocomplete').yourlabsAutocomplete().data = {
	        foiaId: foiaId
	    };
	}
	
	// Generate private link with AJAX
	
	$('form.generate-private-link').submit(function (e) {
	    e.preventDefault();
	    var linkDisplay = $(this).children('input[type=text]');
	    var dataToSubmit = 'action=generate_key';
	    var flashLinkDisplay = function flashLinkDisplay() {
	        $(linkDisplay).addClass('success');
	        window.setTimeout(function () {
	            $(linkDisplay).removeClass('success');
	        }, 500);
	    };
	    var handleSuccess = function handleSuccess(data, status, jqXHR) {
	        var newLink = window.location.origin + window.location.pathname + '?key=' + data.key;
	        $(linkDisplay).val(newLink);
	        flashLinkDisplay();
	    };
	    $.ajax({
	        method: 'POST',
	        data: dataToSubmit,
	        success: handleSuccess
	    });
	});
	
	/* Modals */
	
	$('.text-area.modal-button').click(function (e) {
	    e.preventDefault();
	    textAreaModal($(this).next());
	    return false;
	});
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 16 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	var identifySortable = function identifySortable() {
	    $('.list-table-head th').each(function () {
	        if (!!$(this).data('sort')) {
	            $(this).addClass('sortable');
	        }
	    });
	};
	
	var tableHeadSortIndicator = function tableHeadSortIndicator() {
	    var sort = $('thead').data('activeSort');
	    var order = $('thead').data('activeOrder');
	    if (!!sort) {
	        // find the right title and add the right arrow to it
	        var arrow = order == 'desc' ? '&#x25B2;' : '&#x25BC;';
	        var inverseOrder = order == 'desc' ? 'asc' : 'desc';
	        $('th').each(function () {
	            if ($(this).data('sort') == sort) {
	                $(this).prepend('<span class="arrow">' + arrow + '</span>').data('order', inverseOrder).addClass('sorted_by');
	            }
	        });
	    }
	};
	
	var sortListByHeader = function sortListByHeader() {
	    var sort = $(this).data('sort');
	    var order = $(this).data('order');
	    if (!!sort) {
	        if (!order) {
	            order = 'asc';
	        }
	        var existing = window.location.search;
	        // check for existing sort and remove it if it exists
	        // there will always be "?" or "&" before "sort"
	        var existingSort = existing.indexOf('sort');
	        if (existingSort > 0) {
	            existing = existing.substring(0, existingSort - 1);
	        }
	        // check for filter
	        var filterExists = false;
	        if (existing.length > 0) {
	            filterExists = true;
	        }
	        // add new sort and order
	        // if adding to a filter use "&", otherwise use "?"
	        var newSearch = existing.length > 0 ? existing + "&" : existing + "?";
	        newSearch += "sort=" + sort;
	        newSearch += "&order=" + order;
	        window.location = window.location.origin + window.location.pathname + newSearch;
	    }
	};
	
	identifySortable();
	tableHeadSortIndicator();
	$('.list-table-head th').click(sortListByHeader);
	
	$('#list-filters-toggle').change(function () {
	    var label = $('#list-filters-toggle-label')[0];
	    if (this.checked) {
	        label.innerText = 'Hide';
	    } else {
	        label.innerText = 'Show';
	    }
	});
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 17 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	// NOTIFICATIONS
	var notificationCloseButton = $('.notification .dismiss .close');
	notificationCloseButton.click(function () {
	    $(this).closest('.notification').hide();
	    if ($('.notifications').children(':visible').length == 0) {
	        $('.notifications').hide();
	    }
	});
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 18 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	/*
	
	tabs.js
	
	Tabbed-based navigation using Javascript
	and the manipulation of URL hashes.
	
	Turn classed anchor links into tabs,
	and allow elements within those tabs to
	be accessible by hash as well.
	
	*/
	
	var tabs = $('.tab').attr('tabindex', '0'); // collect all the tabs and set tabindex to 0
	var tabTargets = tabs.map(function () {
	    // get an array of tab-panel ids
	    return this.hash;
	}).get();
	var tabPanels = $(tabTargets.join(',')); // use those ids to get the actual tab-panels
	var deepItems = $('.file, .note, .communication'); // get all the deep link things
	var deepItemTargets = deepItems.map(function () {
	    // get a list of all the file hashes
	    return '#' + $(this).attr('id');
	}).get();
	
	function showTab(id) {
	    // if no id provided, use the id of the first panel
	    id = !id ? tabTargets[0] : id;
	    if (!id) {
	        return;
	    }
	    // remove the active class from the tabs,
	    // and add it back to the one the user selected
	    tabs.removeClass('active').attr('aria-selected', 'false').filter(function () {
	        return this.hash === id;
	    }).addClass('active').attr('aria-selected', 'true');
	    // hide all the panels, then filter to the one
	    // we're interested in and show it
	    tabPanels.find('.tab-panel-heading').hide();
	    tabPanels.hide().attr('aria-hidden', 'true').filter(id).show().attr('aria-hidden', 'false');
	    console.log('Switched to tab:', id);
	}
	
	function getTabId(id) {
	    var hyphen = id.indexOf('-');
	    var tabId = id.substring(0, hyphen != -1 ? hyphen : id.length) + 's';
	    return tabId;
	}
	
	function deepLink(id) {
	    // we expect a hyphen delimited id, e.g. #file-1
	    if (!id || id.indexOf('-') === -1) {
	        return;
	    }
	    var tab = getTabId(id);
	    showTab(tab);
	    if (tab == '#files') {
	        // deep link to single file
	        var file = deepItems.filter(id).first();
	        displayFile(file);
	    } else if (tab == '#notes' || tab == '#comms') {
	        // deep link to specific element
	        var elementOffset = deepItems.filter(id).first().offset();
	        window.scrollTo(elementOffset.top, elementOffset.left);
	    }
	    console.log('Deeplinked to:', id);
	}
	
	// Bind to hashchange event
	$(window).on('hashchange', function () {
	    // check if the hash is a target
	    var hash = location.hash;
	    if (tabTargets.indexOf(hash) !== -1) {
	        showTab(hash);
	    }
	    if (deepItemTargets.indexOf(hash) !== -1) {
	        deepLink(hash);
	    }
	});
	
	// Initialize
	showTab(tabTargets.indexOf(location.hash) !== -1 ? location.hash : '');
	deepLink(deepItemTargets.indexOf(location.hash) !== -1 ? location.hash : '');
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 19 */
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	// Task.js
	//
	// Logic for client interactions with the MuckRock task system.
	
	function authenticateAjax() {
	    // Sets up authentication for AJAX transactions
	    var csrftoken = $.cookie('csrftoken');
	    function csrfSafeMethod(method) {
	        // these HTTP methods do not require CSRF protection
	        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method)
	        );
	    }
	    $.ajaxSetup({
	        beforeSend: function beforeSend(xhr, settings) {
	            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
	                xhr.setRequestHeader("X-CSRFToken", csrftoken);
	            }
	        }
	    });
	}
	
	function ajaxPost(task, endpoint, data) {
	    var pendingOverlay = $(task).children('.pending.overlay');
	    var errorOverlay = $(task).children('.error.overlay');
	    $(document).ajaxStart(function () {
	        $(pendingOverlay).addClass('visible');
	    }).ajaxError(function (event, response) {
	        $(pendingOverlay).removeClass('visible');
	        $(errorOverlay).addClass('visible');
	        setTimeout(function () {
	            $(errorOverlay).removeClass('visible');
	        }, 3000);
	        $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
	    }).ajaxComplete(function () {
	        $(pendingOverlay).removeClass('visible');
	        markAsResolved(task);
	        $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
	    });
	    $.ajax({
	        url: endpoint,
	        type: 'post',
	        data: data,
	        success: null,
	        dataType: 'json'
	    });
	}
	
	/*
	Need to add the action as a value since the button is being overridden.
	In a non-JS form submission, the button would also include its value in the posted data.
	*/
	
	function resolve(taskForm) {
	    var taskID = '#' + getTaskID($(taskForm).serializeArray()) + '-task';
	    var taskData = $(taskForm).serialize() + '&resolve=true';
	    var taskEndpoint = $(taskForm).attr('action');
	    ajaxPost(taskID, taskEndpoint, taskData);
	}
	
	function reject(taskForm) {
	    var taskID = '#' + getTaskID($(taskForm).serializeArray()) + '-task';
	    var taskData = $(taskForm).serialize() + '&reject=true';
	    var taskEndpoint = $(taskForm).attr('action');
	    ajaxPost(taskID, taskEndpoint, taskData);
	}
	
	function getTaskID(taskFormData) {
	    // Gets the task ID from a task form
	    var taskID;
	    $.each(taskFormData, function (i, input) {
	        if (input.name == 'task') {
	            taskID = input.value;
	        }
	    });
	    return taskID;
	}
	
	function markAsResolved(task) {
	    $(task).addClass('resolved');
	}
	
	function formHasAction(taskForm, action) {
	    // checks whether the task form has a 'Resolve' action or not
	    var actionExists = false;
	    var actionButton = 'button[name="' + action + '"]';
	    if (!!$(taskForm).children(actionButton).length) {
	        actionExists = true;
	    }
	    return actionExists;
	}
	
	////////////////////////////////////////////////////////////////////////////////
	
	authenticateAjax();
	
	var tasks = $('.task');
	
	// Hide all the resolved tasks
	$('.resolved.task').each(function () {
	    markAsResolved(this);
	}).addClass('collapsed');
	
	$('button[name="resolve"]').click(function (e) {
	    /* If the button clicked is the "resolve all" button, then get forms
	    for all the currently checked tasks. Else, just get the form for the
	    task that owns the button. */
	    e.preventDefault();
	    var forms = [];
	    if ($(this).attr('id') == 'batched-resolve') {
	        $(':checked[form=batched]').each(function () {
	            var taskForm = $(this).closest('.task').find('form');
	            // the form needs to have a resolve action in order to be added
	            if (formHasAction(taskForm, 'resolve')) {
	                forms.push(taskForm);
	            }
	        });
	    } else {
	        forms.push($(this).closest('form'));
	    }
	    $(forms).each(function () {
	        resolve(this);
	    });
	    return false;
	});
	
	$('button[name="reject"]').click(function (e) {
	    e.preventDefault();
	    var forms = [];
	    if ($(this).attr('id') == 'batched-reject') {
	        $(':checked[form=batched]').each(function () {
	            var taskForm = $(this).closest('.task').find('form');
	            if (formHasAction(taskForm, 'reject')) {
	                forms.push(taskForm);
	            }
	        });
	    } else {
	        forms.push($(this).closest('form'));
	    }
	    $(forms).each(function () {
	        console.log($(this));
	        reject(this);
	    });
	    return false;
	});
	
	tasks.find('header').click(function () {
	    $(this).parent().toggleClass('collapsed');
	});
	
	$('.task .permalink').click(function (e) {
	    e.stopPropagation();
	});
	
	$('.task .checkbox').click(function (e) {
	    e.stopPropagation();
	});
	
	var checkboxes = $('.task header').find(':checkbox');
	var batchedButtons = $('#batched button').not('#collapse-all');
	function toggleBatchedButtons() {
	    if ($('.task header').find(':checkbox:checked').length > 0) {
	        batchedButtons.attr('disabled', false);
	    } else {
	        batchedButtons.attr('disabled', true);
	    }
	}
	batchedButtons.attr('disabled', true);
	checkboxes.change(toggleBatchedButtons);
	
	$('#collapse-all').click(function (e) {
	    e.preventDefault();
	    if ($(this).text() == "Collapse All") {
	        $(this).text("Reveal All");
	        $('.task').addClass('collapsed');
	    } else {
	        $(this).text("Collapse All");
	        $('.task').removeClass('collapsed');
	    }
	});
	
	$('.reveal-extra-context').click(function (e) {
	    e.preventDefault();
	    if ($(this).data['state']) {
	        // if on, turn off
	        $(this).data['state'] = 0;
	        $(this).text("More Info");
	        $(this).next().addClass('hidden');
	    } else {
	        // if off, turn on
	        $(this).data['state'] = 1;
	        $(this).text("Less Info");
	        $(this).next().removeClass('hidden');
	    }
	});
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(2)))

/***/ },
/* 20 */
/***/ function(module, exports) {

	// removed by extract-text-webpack-plugin

/***/ }
/******/ ]);
//# sourceMappingURL=main.js.map