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

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    property_id = fields.Many2one('pms.property', string='Property')
    wating_delivery = fields.Boolean(
        string='Waiting Delivery',
        default=False,
        readonly=True,
        compute='_compute_wating_delivery',
        store=True
    )

    @api.depends('picking_ids.state', 'picking_ids')
    def _compute_wating_delivery(self):
        for purchase in self:
            purchase.wating_delivery = any(picking.state not in ['done', 'cancel'] for picking in purchase.picking_ids)

    @api.model
    def create(self, values):
        property_id = values.get('property_id', False)
        wharehouse_id = self.env['pms.property'].browse(property_id).wharehouse_id.id if property_id else False
        if wharehouse_id:
            values['picking_type_id'] = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', wharehouse_id),
                ('code', '=', 'incoming')
            ], order="id", limit=1).id
        return super().create(values)

    def button_confirm(self):
        force_confirm = self.env.context.get('force_confirm', False)
        if not force_confirm and self.partner_id.min_purchase_amount and self.amount_total < self.partner_id.min_purchase_amount:
            raise UserError(_('The minimum purchase amount for {} is {}').format(self.partner_id.name, self.partner_id.min_purchase_amount))

        res = super().button_confirm()

        for purchase in self:
            if purchase.property_id:
                purchase.message_subscribe(partner_ids=purchase.property_id.partner_id.ids)
                for ps in purchase.picking_ids:
                    ps.message_subscribe(partner_ids=purchase.property_id.partner_id.ids)

        return res

    def _add_supplier_to_product(self):
        return True
