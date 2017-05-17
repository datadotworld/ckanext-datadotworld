ckan.module('info-popover', function($, _) {
    "use strict";
    return {
        initialize: function() {
            this.el.popover({
                trigger: 'focus',
                html: true
            });
        }
    };
});
