odoo.define('purchase_portal.SavedCartItems', function (require) {
'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.SavedCartItems = publicWidget.Widget.extend({
        selector: '.o_saved_cart_summary',
        events: {
            "click span.o_cart_line_change_qty": "_onClickChangeQty",
            'focusout .o_hidden_cart_line_quantity_input': '_onLineQtyInputFocusout',
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */
         _onClickChangeQty: function (ev) {
            ev.preventDefault();
            $(ev.currentTarget).parent().find(".o_hidden_cart_line_quantity_input").removeClass("d-none");
            $(ev.currentTarget).addClass("d-none");
        },

        _onLineQtyInputFocusout: function (ev) {
            ev.preventDefault();
            $(ev.currentTarget).parent().find(".o_cart_line_change_qty").removeClass("d-none");
            $(ev.currentTarget).addClass("d-none");

            var attr_name = $(ev.currentTarget).attr("name");
            var o_val = $(ev.currentTarget).parent().find("span")[0].innerText;
            var new_val = $(ev.currentTarget).val();
            var item_id = $(ev.currentTarget).attr("data-item_id");

            if(parseFloat(o_val) != new_val) {
                this._rpc({
                    route: "/saved_cart_item_edit",
                    params: {
                        'item_id': parseInt(item_id),
                        'attr_name': attr_name,
                        'value': new_val,
                    },
                }).then(function (new_data) {
                    try {
                        let json_data = JSON.parse(new_data);
                        if ("error" in json_data) {
                            $("#edit_errors")[0].innerHTML = "<div class='alert alert-danger' role='alert'>"+json_data["message"]+"</div>";
                        }                
                    } catch (e) {
                        $("#edit_errors").empty();
                        $("#o_saved_cart_summary_container").empty();
                        $("#o_saved_cart_summary_container").html(new_data);
                    }
                });
            }
        },
    });

});
