
var fao = window.fao || {};

fao.orig_ac = ckan.module.registry['autocomplete'];

ckan.module('fao-autocomplete', function($){
    fao.autocomplete = {

        setupAutoComplete: function() {
            var settings = {
                width: 'resolve',
                formatResult: this.formatResult,
                formatNoMatches: this.formatNoMatches,
                formatInputTooShort: this.formatInputTooShort,
                dropdownCssClass: this.options.dropdownClass,
                containerCssClass: this.options.containerClass,
            };
            if (!this.el.is('select')) {
                if (this.options.tags) {
                    settings.tags = this._onQuery;
                } else {
                    settings.multiple = true;
                    settings.query = this._onQuery;
                    settings.createSearchChoice = this.formatTerm;
                }
                settings.initSelection = this.formatInitialValue;
            } else {
                if (/MSIE (\d+\.\d+);/.test(navigator.userAgent)) {
                    var ieversion = new Number(RegExp.$1);
                    if (ieversion <= 7) {
                        return
                    }
                }
            }
            var select2 = this.el.select2(settings).data('select2');
            if (this.options.tags && select2 && select2.search) {
                select2.search.on('keydown', this._onKeydown);
            }
            $('.select2-choice', select2.container).on('click', function() {
                return false;
            });
            this._select2 = select2;
        },


     /* Takes a string and converts it into an object used by the select2 plugin.
     *
     * term - The term to convert.
     *
     * Returns an object for use in select2.
     */
    formatTerm: function (term) {
      // Need to replace comma with a unicode character to trick the plugin
      // as it won't split this into multiple items.
      term = jQuery.trim(term || '').replace(/,/g, '\u002C');
      var nterm = term.split('|');
      var tname = term;
      var tid = term;
      if (nterm.length == 2){
        tid = nterm[0];
        tname = nterm[1];
      } else {
        return null;
      }
      return {id: tid, text: tname};
    },

    /* Callback function that parses the initial field value.
     *
     * element  - The initialized input element wrapped in jQuery.
     * callback - A callback to run once the formatting is complete.
     *
     * Returns a term object or an array depending on the type.
     */
    formatInitialValue: function (element, callback) {
      var value = jQuery.trim(element.data('value') || element.val() || '');
      var formatted;

      formatted = jQuery.map(value.split(","), this.formatTerm);

      // Select2 v3.0 supports a callback for async calls.
      if (typeof callback === 'function') {
        callback(formatted);
      }

      return formatted;
    }
    };
    return $.extend({}, fao.orig_ac.prototype, fao.autocomplete);
 });



