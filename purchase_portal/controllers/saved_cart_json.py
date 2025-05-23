##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2023 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
#    Vicente Ángel Gutiérrez <vicente@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import json
from odoo import http, _
from odoo.http import request
from odoo.tools.misc import get_lang


class SavedCartJsonMethods(http.Controller):

    @http.route(
        ["/saved_cart_item_edit"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def saved_cart_item_edit(
        self, item_id=False, value=False, attr_name=False, **kw
    ):
        if item_id and value and attr_name:
            lang = get_lang(request.env).code
            item_id = request.env['purchase.request.saved.cart.item'].browse(item_id)
            if not item_id:
                return json.dumps({"error": True, "message": _("Line not found")})
            try:
                item_id.sudo().update({
                    attr_name: value,
                })

                values = {
                    "saved_cart": item_id.cart_id,
                }
                return request.env["ir.ui.view"].with_context(lang=lang)._render_template(
                    "purchase_portal.portal_my_saved_items", values
                )
            except Exception as e:
                return json.dumps(
                    {
                        "error": True,
                        "message": str(e),
                    }
                )
        return json.dumps({"error": True, "message": _("Line not found")})

    @http.route(
        ["/saved_cart_edit"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def saved_cart_edit(
        self, saved_cart=False, value=False, attr_name=False, **kw
    ):
        if saved_cart and value and attr_name:
            lang = get_lang(request.env).code
            saved_cart = request.env['purchase.request.saved.cart'].browse(saved_cart)
            if not saved_cart:
                return json.dumps({"error": True, "message": _("Line not found")})
            try:
                saved_cart.sudo().update({
                    attr_name: value,
                })

                values = {
                    "saved_cart": saved_cart,
                }
                return request.env["ir.ui.view"].with_context(lang=lang)._render_template(
                    "purchase_portal.portal_saved_cart_info", values
                )
            except Exception as e:
                return json.dumps(
                    {
                        "error": True,
                        "message": str(e),
                    }
                )
        return json.dumps({"error": True, "message": _("Line not found")})
