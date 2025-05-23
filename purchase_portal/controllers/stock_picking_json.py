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
from odoo.tests import Form


class StockPickingJsonMethods(http.Controller):

    @http.route(
        ["/stock_picking_line_edit"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def stock_picking_line_edit(
        self, line_id=False, value=False, attr_name=False, **kw
    ):
        if line_id and value and attr_name:
            lang = get_lang(request.env).code
            line_id = request.env['stock.move'].browse(line_id)
            if not line_id:
                return json.dumps({"error": True, "message": _("Line not found")})
            try:
                line_id.sudo().update({
                    attr_name: value,
                })

                values = {
                    "stock_picking": line_id.picking_id,
                    "move_ids": line_id.picking_id.move_ids,
                }
                return request.env["ir.ui.view"].with_context(lang=lang)._render_template(
                    "purchase_portal.stock_picking_lines_table", values
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
        ["/stock_picking_validate"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def stock_picking_validate(self, picking_id=None, **kw):
        if picking_id:
            # lang = get_lang(request.env).code
            picking_id = request.env['stock.picking'].sudo().browse(picking_id)
            if not picking_id:
                return json.dumps({"error": True, "message": _("Picking not found")})
            try:
                res = picking_id.button_validate()
                if type(res) is dict and res.get('res_model', False) == 'stock.backorder.confirmation':
                    res['context']['default_send_mail_to_seller'] = True
                    back_order_wizard = Form(request.env[(res.get('res_model'))].sudo().with_context(res['context'])).save()
                    res = back_order_wizard.process()
                return res
            except Exception as e:
                return json.dumps(
                    {
                        "error": True,
                        "message": str(e),
                    }
                )
        return json.dumps({"error": True, "message": _("Picking not found")})
