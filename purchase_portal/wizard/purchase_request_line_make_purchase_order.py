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

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    property_id = fields.Many2one('pms.property', string='Property')
    multiple_suppliers = fields.Boolean('Multiple suppliers', default=False)

    @api.model
    def _prepare_purchase_order(self, picking_type, group_id, company, origin):
        res = super()._prepare_purchase_order(picking_type, group_id, company, origin)
        if self.property_id:
            res['property_id'] = self.property_id.id
        return res

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model", False)
        request_line_ids = []
        if active_model == "purchase.request.line":
            request_line_ids += self.env.context.get("active_ids", [])
        elif active_model == "purchase.request":
            request_ids = self.env.context.get("active_ids", False)
            request_line_ids += (
                self.env[active_model].browse(request_ids).mapped("line_ids.id")
            )
        if not request_line_ids:
            return res
        request_line_ids
        request_lines = self.env["purchase.request.line"].browse(request_line_ids)
        property_id = request_lines.mapped("property_id")
        if len(property_id) > 1:
            raise UserError(_("You can't select lines from different properties"))
        if property_id:
            res["property_id"] = property_id.id
            if not res.get('supplier_id', False) and request_lines.mapped("suggested_supplier_id"):
                res["supplier_id"] = request_lines.mapped("supplier_id").ids[0] if request_lines.mapped("supplier_id") else False
                res["multiple_suppliers"] = True
        return res

    def make_purchase_order(self):
        res = []
        purchase_obj = self.env["purchase.order"]
        po_line_obj = self.env["purchase.order.line"]
        pr_line_obj = self.env["purchase.request.line"]
        purchase = False

        line_ids = pr_line_obj.sudo().search([
            ('id', 'in', self.item_ids.mapped("line_id").ids)
        ])

        if len(line_ids.mapped('suggested_supplier_id')) < 2:
            return super(PurchaseRequestLineMakePurchaseOrder, self).make_purchase_order()

        # We use the original method with a few moditifications to create a PO for each supplier

        suppliers = line_ids.mapped('suggested_supplier_id')
        for supplier in suppliers:
            purchase = None
            supplier_lines = self.item_ids.filtered(lambda x: x.line_id.suggested_supplier_id == supplier)

            for item in supplier_lines:
                line = item.line_id
                if item.product_qty <= 0.0:
                    raise UserError(_("Enter a positive quantity."))
                if self.purchase_order_id and self.purchase_order_id.partner_id.id == supplier.id:
                    purchase = self.purchase_order_id
                if not purchase:
                    purchase = self.env['purchase.order'].search([
                        ('partner_id', '=', supplier.id),
                        ('state', 'in', ['draft']),
                    ], limit=1)
                if not purchase:
                    po_data = {
                        "origin": line.origin,
                        "partner_id": supplier.id,
                        "fiscal_position_id": supplier.property_account_position_id
                        and supplier.property_account_position_id.id
                        or False,
                        "picking_type_id": line.request_id.picking_type_id.id,
                        "company_id": line.company_id.id,
                        "group_id": line.request_id.group_id.id,
                        "property_id": self.property_id.id,
                    }
                    purchase = purchase_obj.create(po_data)

                # Look for any other PO line in the selected PO with same
                # product and UoM to sum quantities instead of creating a new
                # po line
                domain = self._get_order_line_search_domain(purchase, item)
                available_po_lines = po_line_obj.search(domain)
                new_pr_line = True
                # If Unit of Measure is not set, update from wizard.
                if not line.product_uom_id:
                    line.product_uom_id = item.product_uom_id
                # Allocation UoM has to be the same as PR line UoM
                alloc_uom = line.product_uom_id
                wizard_uom = item.product_uom_id
                if available_po_lines and not item.keep_description:
                    new_pr_line = False
                    po_line = available_po_lines[0]
                    po_line.purchase_request_lines = [(4, line.id)]
                    po_line.move_dest_ids |= line.move_dest_ids
                    po_line_product_uom_qty = po_line.product_uom._compute_quantity(
                        po_line.product_uom_qty, alloc_uom
                    )
                    wizard_product_uom_qty = wizard_uom._compute_quantity(
                        item.product_qty, alloc_uom
                    )
                    all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
                    self.create_allocation(po_line, line, all_qty, alloc_uom)
                else:
                    po_line_data = self._prepare_purchase_order_line(purchase, item)
                    if item.keep_description:
                        po_line_data["name"] = item.name
                    po_line = po_line_obj.create(po_line_data)
                    po_line_product_uom_qty = po_line.product_uom._compute_quantity(
                        po_line.product_uom_qty, alloc_uom
                    )
                    wizard_product_uom_qty = wizard_uom._compute_quantity(
                        item.product_qty, alloc_uom
                    )
                    all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
                    self.create_allocation(po_line, line, all_qty, alloc_uom)
                # TODO: Check propagate_uom compatibility:
                new_qty = pr_line_obj._calc_new_qty(
                    line, po_line=po_line, new_pr_line=new_pr_line
                )
                po_line.product_qty = new_qty
                po_line._compute_price_unit_and_date_planned_and_name()
                # The compute is altering the scheduled date of the PO
                # lines. We do not want that:
                date_required = item.line_id.date_required
                po_line.date_planned = datetime(
                    date_required.year, date_required.month, date_required.day
                )
                res.append(purchase.id)

        return {
            "domain": [("id", "in", res)],
            "name": _("RFQ"),
            "view_mode": "tree,form",
            "res_model": "purchase.order",
            "view_id": False,
            "context": False,
            "type": "ir.actions.act_window",
        }
