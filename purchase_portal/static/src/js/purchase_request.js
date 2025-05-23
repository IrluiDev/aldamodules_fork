odoo.define('purchase_portal.PurchaseRequestPortal', function (require) {
'use strict';

var publicWidget = require('web.public.widget');

publicWidget.registry.PurchaseRequestPortal = publicWidget.Widget.extend({
    selector: '#purchase_request_container',
    events: {
        "keyup input.oe_search_box": "_onSearchKeyup",
        "click button.request_add_to_cart": "_onAddToCart",
        "keyup input.purchase_update_line": "_onUpdateLine",
        "change input.purchase_update_line": "_onUpdateLine",
        "click a.purchase_delete_line": "_onDeleteLine",
        "change select.purchase_select": "_onChangeSelect",
        "click button.request_validation": "_onValidation",
        "click button.restart_validation": "_onRestarValidation",
        "change select.purchase_seller": "_onChangeSeller",
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onSearchKeyup: function (ev) {
        let search = $(ev.currentTarget).val();
        let property_id = $(ev.currentTarget).attr("data-property_id");
        let purchase_request = $(ev.currentTarget).attr("data-purchase_request");
        let seller_id = $("#product_seller").val();
        let category_id = $("#product_category").val();

        this._rpc({
            route: "/purchase_request_product_table",
            params: {
                'search': search,
                'seller_id': seller_id,
                'category_id': category_id,
                'property_id': property_id,
                'purchase_request': purchase_request,
            },
        }).then(function (new_data) {
            $("#purchase_request_product_list").empty();
            $("#purchase_request_product_list").html(new_data);
        });
    },

    _onAddToCart: function (ev) {
        let product_id = $(ev.currentTarget).attr("data-product_id");
        let purchase_request = $(ev.currentTarget).attr("data-purchase_request");
        let qty = $(ev.currentTarget).closest("tr").find("input[name='product_qty']").val();

        this._rpc({
            route: "/purchase_request_add_product",
            params: {
                'purchase_request': purchase_request,
                'product_id': product_id,
                'qty': qty,
            },
        }).then(function (new_data) {
            try {
                let json_data = JSON.parse(new_data);
                if ("error" in json_data) {
                    $("#edit_errors")[0].innerHTML = "<div class='alert alert-danger' role='alert'>"+json_data["message"]+"</div>";
                }
            } catch (e) {
                $("#edit_errors").empty();
                $("#purchase_request_details_list").empty();
                $("#purchase_request_details_list").html(new_data);
            }
        });
    },

    _onUpdateLine: function (ev) {
        let line_id = $(ev.currentTarget).attr("data-line_id");
        let qty = $(ev.currentTarget).val();

        this._rpc({
            route: "/purchase_request_update_line",
            params: {
                'line_id': line_id,
                'qty': qty,
            },
        }).then(function (new_data) {
            try {
                let json_data = JSON.parse(new_data);
                if ("error" in json_data) {
                    $("#edit_errors")[0].innerHTML = "<div class='alert alert-danger' role='alert'>"+json_data["message"]+"</div>";
                }
            } catch (e) {
                $("#edit_errors").empty();
                $("#purchase_request_details_list").empty();
                $("#purchase_request_details_list").html(new_data);
            }
        });
    },

    _onDeleteLine: function (ev) {
        let line_id = $(ev.currentTarget).attr("data-line_id");

        this._rpc({
            route: "/purchase_delete_line",
            params: {
                'line_id': line_id,
            },
        }).then(function (new_data) {
            try {
                let json_data = JSON.parse(new_data);
                if ("error" in json_data) {
                    $("#edit_errors")[0].innerHTML = "<div class='alert alert-danger' role='alert'>"+json_data["message"]+"</div>";
                }
            } catch (e) {
                $("#edit_errors").empty();
                $("#purchase_request_details_list").empty();
                $("#purchase_request_details_list").html(new_data);
            }
        });
    },

    _onChangeSelect: function (ev) {
        let search = $("#search").val();
        let category_id = $(ev.currentTarget).val();
        let seller_id = $("#product_seller").val();
        let property_id = $(ev.currentTarget).attr("data-property_id");
        let purchase_request = $(ev.currentTarget).attr("data-purchase_request");

        this._rpc({
            route: "/purchase_request_product_table",
            params: {
                'search': search,
                'seller_id': seller_id,
                'category_id': category_id,
                'property_id': property_id,
                'purchase_request': purchase_request,
            },
        }).then(function (new_data) {
            $("#purchase_request_product_list").empty();
            $("#purchase_request_product_list").html(new_data);
        });
    },

    _onValidation: function (ev) {
        let purchase_request = $(ev.currentTarget).attr("data-purchase_request");

        this._rpc({
            route: "/purchase_request_validation",
            params: {
                'purchase_request': purchase_request,
            },
        }).then(function (new_data) {
            try {
                let json_data = JSON.parse(new_data);
                if ("error" in json_data && json_data["error"]) {
                    $("#edit_errors")[0].innerHTML = "<div class='alert alert-danger' role='alert'>"+json_data["message"]+"</div>";
                } else {
                    window.location.reload();
                }
            } catch (e) {
                $("#edit_errors").empty();
            }
        });
    },

    _onRestarValidation: function (ev) {
        let purchase_request = $(ev.currentTarget).attr("data-purchase_request");

        this._rpc({
            route: "/purchase_request_restart_validation",
            params: {
                'purchase_request': purchase_request,
            },
        }).then(function (new_data) {
            try {
                let json_data = JSON.parse(new_data);
                if ("error" in json_data && json_data["error"]) {
                    $("#edit_errors")[0].innerHTML = "<div class='alert alert-danger' role='alert'>"+json_data["message"]+"</div>";
                } else {
                    window.location.reload();
                }
            } catch (e) {
                $("#edit_errors").empty();
            }
        });
    },

    _onChangeSeller: function (ev) {
        let search = $("#search").val();
        let seller_id = $(ev.currentTarget).val();
        let category_id = $("#product_category").val();
        let property_id = $(ev.currentTarget).attr("data-property_id");
        let purchase_request = $(ev.currentTarget).attr("data-purchase_request");

        this._rpc({
            route: "/purchase_request_product_table",
            params: {
                'search': search,
                'seller_id': seller_id,
                'category_id': category_id,
                'property_id': property_id,
                'purchase_request': purchase_request,
            },
        }).then(function (new_data) {
            $("#purchase_request_product_list").empty();
            $("#purchase_request_product_list").html(new_data);
        });
    },
});
});
