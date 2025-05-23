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
from odoo.exceptions import UserError


class PurchaseRequestJsonMethods(http.Controller):

    @http.route(
        ["/purchase_request_product_table"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def get_purchase_request_product_table(self, **kw):
        lang = get_lang(request.env).code
        search = kw.get('search', False)
        property_id = kw.get('property_id', False)
        category_id = kw.get('category_id', False)
        seller_id = kw.get('seller_id', False)
        purchase_request = kw.get('purchase_request', False)
        if not property_id:
            return json.dumps(
                {
                    "error": True,
                    "message": "No property_id",
                }
            )

        property_id = request.env['pms.property'].browse(int(property_id))
        if not property_id:
            return json.dumps(
                {
                    "error": True,
                    "message": "No property_id",
                }
            )

        purchase_request = request.env['purchase.request'].browse(int(purchase_request))
        if not purchase_request:
            return json.dumps(
                {
                    "error": True,
                    "message": "No purchase_request",
                }
            )

        product_ids = property_id.sudo().product_ids
        if search and search != '':
            product_ids = request.env["product.product"].sudo().search([
                ("id", "in", product_ids.ids),
                "|",
                ("name", "ilike", search),
                ("default_code", "ilike", search)
            ])
        if category_id and category_id != 'all':
            product_ids = request.env["product.product"].sudo().search([
                ("id", "in", product_ids.ids),
                ("categ_id", "=", int(category_id))
            ])

        if seller_id and seller_id != 'all':
            partner_id = request.env['res.partner'].sudo().search([('id', '=', int(seller_id))])
            commercial_partner_id = partner_id.commercial_partner_id
            product_ids = request.env["product.product"].sudo().search([
                ("id", "in", product_ids.ids),
                "|",
                ("seller_ids.partner_id", "=", partner_id.id),
                ("seller_ids.partner_id", "=", commercial_partner_id.id)
            ])

        if request.env.user.banned_product_ids:
            product_ids = product_ids - request.env.user.banned_product_ids

        values = {
            "product_ids": product_ids,
            "purchase_request": purchase_request,
        }

        return request.env["ir.ui.view"].with_context(lang=lang)._render_template(
            "purchase_portal.purchase_request_product_table", values
        )

    @http.route(
        ["/purchase_request_add_product"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def purchase_request_add_product(self, **kw):
        lang = get_lang(request.env).code
        purchase_request = kw.get('purchase_request', False)
        product_id = kw.get('product_id', False)
        qty = kw.get('qty', False)

        if not purchase_request or not product_id or not qty:
            return json.dumps(
                {
                    "error": True,
                    "message": _("Missing parameters"),
                }
            )

        purchase_request = request.env['purchase.request'].browse(int(purchase_request))
        if not purchase_request or purchase_request.state not in ["to_approve", "draft"]:
            return json.dumps(
                {
                    "error": True,
                    "message": _("No purchase_request or wrong state"),
                }
            )
        try:
            product_info = request.env['product.supplierinfo'].sudo().search([
                '|',
                ('partner_id', 'in', purchase_request.property_id.seller_ids.ids),
                ('partner_id', 'in', purchase_request.property_id.seller_commercial_ids.ids),
                '|',
                ('product_id', '=', int(product_id)),
                ('product_tmpl_id.product_variant_ids', '=', int(product_id)),
            ], order='price asc', limit=1)
            request_line = request.env['purchase.request.line'].with_context(portal=True).create({
                'request_id': purchase_request.id,
                'product_id': int(product_id),
                'product_qty': float(qty),
                'estimated_cost': (product_info.price * float(qty)) if product_info else 0,
            })

            # portal=False to avoid onchange_product_id to be raise error
            request_line.with_context(portal=False).onchange_product_id()
            request_line.with_context(portal=True, no_msg=True).write({
                'product_qty': float(qty),
                'product_uom_id': product_info.product_uom.id if product_info else False,
            })
        except Exception as e:
            return json.dumps(
                {
                    "error": True,
                    "message": str(e),
                }
            )

        values = {
            "line_ids": purchase_request.line_ids,
        }

        return request.env["ir.ui.view"].with_context(lang=lang)._render_template(
            "purchase_portal.purchase_request_details_table", values
        )

    @http.route(
        ["/purchase_request_update_line"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def purchase_request_update_line(self, **kw):
        lang = get_lang(request.env).code
        line_id = kw.get('line_id', False)
        qty = kw.get('qty', False)

        if not line_id or not qty:
            return json.dumps(
                {
                    "error": True,
                    "message": "Missing parameters",
                }
            )

        line_id = request.env['purchase.request.line'].browse(int(line_id))
        if not line_id:
            return json.dumps(
                {
                    "error": True,
                    "message": "No line_id",
                }
            )

        request_id = line_id.request_id

        try:
            qty = float(qty)
            if qty == 0.0:
                line_id.unlink()
            else:
                estimated_cost = (line_id.estimated_cost / line_id.product_qty) * qty
                line_id.with_context(portal=True).write({
                    'product_qty': qty,
                    'estimated_cost': estimated_cost,
                })
        except Exception as e:
            return json.dumps(
                {
                    "error": True,
                    "message": str(e),
                }
            )

        values = {
            "line_ids": request_id.line_ids,
        }

        return request.env["ir.ui.view"].with_context(lang=lang)._render_template(
            "purchase_portal.purchase_request_details_table", values
        )

    @http.route(
        ["/purchase_delete_line"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def purchase_delete_line(self, **kw):
        lang = get_lang(request.env).code
        line_id = kw.get('line_id', False)

        if not line_id:
            return json.dumps(
                {
                    "error": True,
                    "message": "Missing parameters",
                }
            )

        line_id = request.env['purchase.request.line'].browse(int(line_id))
        if not line_id:
            return json.dumps(
                {
                    "error": True,
                    "message": "No line_id",
                }
            )

        request_id = line_id.request_id

        try:
            line_id.unlink()
        except Exception as e:
            return json.dumps(
                {
                    "error": True,
                    "message": str(e),
                }
            )

        values = {
            "line_ids": request_id.line_ids,
        }

        return request.env["ir.ui.view"].with_context(lang=lang)._render_template(
            "purchase_portal.purchase_request_details_table", values
        )

    def _get_seller_ids(self, purchase_request):
        seller_ids = request.env['product.supplierinfo']
        for product in purchase_request.line_ids.mapped('product_id'):
            partners = purchase_request.property_id.seller_ids + purchase_request.property_id.seller_commercial_ids
            seller = seller_ids.sudo().search([
                '&',
                ('partner_id', 'in', partners.ids),
                '|',
                ('product_id', '=', product.id),
                ('product_tmpl_id.product_variant_ids', '=', product.id),
            ], order='price asc', limit=1)
            if seller not in seller_ids:
                seller_ids += seller
        return seller_ids

    @http.route(
        ["/purchase_request_validation"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def purchase_request_validation(self, **kw):
        # lang = get_lang(request.env).code
        purchase_request = kw.get('purchase_request', False)

        if not purchase_request:
            return json.dumps(
                {
                    "error": True,
                    "message": "No purchase_request",
                }
            )

        purchase_request = request.env['purchase.request'].browse(int(purchase_request))
        if not purchase_request:
            return json.dumps(
                {
                    "error": True,
                    "message": "No purchase_request",
                }
            )

        try:
            for line in purchase_request.line_ids:
                if line.product_qty <= 0:
                    raise UserError(_('The quantity for %s must be greater than 0') % (line.product_id.name))

            seller_ids = self._get_seller_ids(purchase_request)

            error_msg = ""

            for partner_id in seller_ids.sudo().mapped('partner_id'):
                min_amount = partner_id.min_purchase_amount
                if not min_amount:
                    min_amount = partner_id.commercial_partner_id.min_purchase_amount
                sellers = seller_ids.sudo().filtered(
                    lambda x: x.partner_id == partner_id or x.partner_id == partner_id.commercial_partner_id
                )
                purchase_seller_amount = 0
                for seller in sellers:
                    lines = purchase_request.sudo().line_ids.filtered(
                        lambda x: x.product_id == seller.product_id or x.product_id in seller.product_tmpl_id.product_variant_ids
                    )
                    purchase_seller_amount += sum(line.estimated_cost for line in lines)

                if min_amount > purchase_seller_amount:
                    if seller.partner_id.property_purchase_currency_id:
                        symbol = seller.partner_id.property_purchase_currency_id.symbol
                    else:
                        symbol = purchase_request.company_id.currency_id.symbol

                    name = partner_id.name
                    if partner_id not in purchase_request.property_id.seller_ids:
                        name = purchase_request.property_id.seller_ids.filtered(
                            lambda x: x.commercial_partner_id == partner_id
                        ).name

                    error_msg += _('The minimum amount for %s is %s%s. Current amount %s%s.<br/>') % (
                        name,
                        min_amount,
                        symbol,
                        purchase_seller_amount,
                        symbol,
                    )

            if error_msg:
                raise UserError(error_msg)

            if purchase_request.estimated_cost <= 300 or not purchase_request.need_validation:
                purchase_request.button_approved()
            else:
                purchase_request.request_validation()
        except Exception as e:
            return json.dumps(
                {
                    "error": True,
                    "message": str(e),
                }
            )
        return json.dumps(
            {
                "error": False,
                "message": "OK",
            }
        )

    @http.route(
        ["/purchase_request_restart_validation"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def purchase_request_restart_validation(self, **kw):
        # lang = get_lang(request.env).code
        purchase_request = kw.get('purchase_request', False)

        if not purchase_request:
            return json.dumps(
                {
                    "error": True,
                    "message": "No purchase_request",
                }
            )

        purchase_request = request.env['purchase.request'].browse(int(purchase_request))
        if not purchase_request:
            return json.dumps(
                {
                    "error": True,
                    "message": "No purchase_request",
                }
            )

        try:
            purchase_request.restart_validation()
        except Exception as e:
            return json.dumps(
                {
                    "error": True,
                    "message": str(e),
                }
            )
        return json.dumps(
            {
                "error": False,
                "message": "OK",
            }
        )
