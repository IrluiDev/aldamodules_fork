odoo.define('purchase_portal.StockPickingPortal', function (require) {
'use strict';

var publicWidget = require('web.public.widget');

publicWidget.registry.StockPickingLinePortal = publicWidget.Widget.extend({
    selector: '#stock_picking_container',
    events: {
        "click span.set_quantity_done": "_onClickQuantityDone",
        'focusout .o_hidden_quantity_done_input': '_onQtyDoneInputFocusout',
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
     _onClickQuantityDone: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget).parent().find(".o_hidden_quantity_done_input").removeClass("d-none");
        $(ev.currentTarget).addClass("d-none");
    },

    _onQtyDoneInputFocusout: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget).parent().find(".set_quantity_done").removeClass("d-none");
        $(ev.currentTarget).addClass("d-none");

        var attr_name = $(ev.currentTarget).attr("name");
        var o_val = $(ev.currentTarget).parent().find("span")[0].innerText;
        var new_val = $(ev.currentTarget).val();
        var line_id = $(ev.currentTarget).attr("data-line_id");

        if(parseFloat(o_val) != new_val) {
            this._rpc({
                route: "/stock_picking_line_edit",
                params: {
                    'line_id': parseInt(line_id),
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
                    $("#stock_picking_container").empty();
                    $("#stock_picking_container").html(new_data);
                }
            });
        }
    },
});

publicWidget.registry.StockPickingControlsPortal = publicWidget.Widget.extend({
    selector: '#stock_picking_controls',
    events: {
        "click button.picking_validate": "_onClickPickingValidate",
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */

     _onClickPickingValidate: function (ev) {
        ev.preventDefault();
        var stock_picking = $(ev.currentTarget).attr("data-stock_picking");

        if(stock_picking) {
            this._rpc({
                route: "/stock_picking_validate",
                params: {
                    'picking_id': parseInt(stock_picking),
                },
            }).then(function (new_data) {
                try {
                    let json_data = JSON.parse(new_data);
                    if ("error" in json_data) {
                        $("#edit_errors")[0].innerHTML = "<div class='alert alert-danger' role='alert'>"+json_data["message"]+"</div>";
                    }                
                } catch (e) {
                    location.reload();
                }
            });
        }
    },
});
});
