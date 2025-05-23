odoo.define('purchase_portal.SavedCart', function (require) {
'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.SavedCart = publicWidget.Widget.extend({
        selector: '.o_saved_cart_data_container',
        events: {
            "click span.o_saved_cart_change_name": "_onClickChangeName",
            'focusout .o_hidden_saved_cart_name_input': '_onNameInputFocusout',
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */
         _onClickChangeName: function (ev) {
            ev.preventDefault();
            $(ev.currentTarget).parent().find(".o_hidden_saved_cart_name_input").removeClass("d-none");
            $(ev.currentTarget).addClass("d-none");
        },

        _onNameInputFocusout: function (ev) {
            ev.preventDefault();
            $(ev.currentTarget).parent().find(".o_saved_cart_change_name").removeClass("d-none");
            $(ev.currentTarget).addClass("d-none");

            var attr_name = $(ev.currentTarget).attr("name");
            var o_val = $(ev.currentTarget).parent().find("span")[0].innerText;
            var new_val = $(ev.currentTarget).val();
            var saved_cart = $(ev.currentTarget).attr("data-saved_cart");

            if(parseFloat(o_val) != new_val) {
                this._rpc({
                    route: "/saved_cart_edit",
                    params: {
                        'saved_cart': parseInt(saved_cart),
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
                        $("#o_saved_cart_data_container").empty();
                        $("#o_saved_cart_data_container").html(new_data);
                    }
                });
            }
        },
    });

});
