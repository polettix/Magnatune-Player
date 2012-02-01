"use strict";

// Shims for some new standard functions:
(function () {
	var shim = function (obj, shims) {
		for (var name in shims) {
			if (!(name in obj)) {
				obj[name] = shims[name];
			}
		}
	};

	shim(String.prototype, {
		trim: function () {
			return this.replace(/^\s\s*/, '').replace(/\s\s*$/, '');
		},
		trimLeft: function () {
			return this.replace(/^\s\s*/, '');
		},
		trimRight: function () {
			return this.replace(/\s\s*$/, '');
		}
	});

	shim(Array, {
		isArray: function (object) {
			return Object.prototype.toString.call(object) === '[object Array]';
		}
	});

	shim(Array.prototype, {
		indexOf: function (searchElement, fromIndex) {
			if (!fromIndex || fromIndex < 0) fromIndex = 0;
			for (; fromIndex < this.length; ++ fromIndex) {
				if (this[fromIndex] === searchElement) {
					return fromIndex;
				}
			}
			return -1;
		},
		forEach: function (callback, thisArg) {
			var T, k;

			if (this == null) {
				throw new TypeError("this is null or not defined");
			}

			// 1. Let O be the result of calling ToObject passing the |this| value as the argument.
			var O = Object(this);

			// 2. Let lenValue be the result of calling the Get internal method of O with the argument "length".
			// 3. Let len be ToUint32(lenValue).
			var len = O.length >>> 0; // Hack to convert O.length to a UInt32

			// 4. If IsCallable(callback) is false, throw a TypeError exception.
			// See: http://es5.github.com/#x9.11
			if (Object.prototype.toString.call(callback) != "[object Function]") {
				throw new TypeError(callback + " is not a function");
			}

			// 5. If thisArg was supplied, let T be thisArg; else let T be undefined.
			if (thisArg) {
				T = thisArg;
			}

			// 6. Let k be 0
			k = 0;

			// 7. Repeat, while k < len
			while (k < len) {
				var kValue;

				// a. Let Pk be ToString(k).
				//   This is implicit for LHS operands of the in operator
				// b. Let kPresent be the result of calling the HasProperty internal method of O with argument Pk.
				//   This step can be combined with c
				// c. If kPresent is true, then
				if (k in O) {
					// i. Let kValue be the result of calling the Get internal method of O with argument Pk.
					kValue = O[k];

					// ii. Call the Call internal method of callback with T as the this value and
					// argument list containing kValue, k, and O.
					callback.call(T, kValue, k, O);
				}
				// d. Increase k by 1.
				++ k;
			}
			// 8. return undefined
		},
		filter: function (fun) {
			if (this == null)
				throw new TypeError("this is null or not defined");

			var t = Object(this);
			var len = t.length >>> 0;
			if (typeof fun != "function")
				throw new TypeError(fun+" is not a function");

			var res = [];
			var thisp = arguments[1];
			for (var i = 0; i < len; ++ i) {
				if (i in t) {
					var val = t[i]; // in case fun mutates this
					if (fun.call(thisp, val, i, t))
						res.push(val);
				}
			}

			return res;
		}
	});

	shim(Function.prototype, {
		bind: function (self) {
			var funct   = this;
			var partial = Array.prototype.slice.call(arguments,1);
			return function () {
				return funct.apply(self,partial.concat(Array.prototype.slice.call(arguments)));
			};
		}
	});

	shim(Date, {
		now: function () {
			return new Date().getTime();
		}
	});

	// dummy console object to prevent crashes on forgotten debug messages:
	if (typeof(console) === "undefined")
		shim(window, {console: {}});
	shim(window.console, {log: function () {}});
	shim(window.console, {
		info:  window.console.log,
		warn:  window.console.log,
		error: window.console.log,
		trace: window.console.log,
		dir:   window.console.log
	});
})();