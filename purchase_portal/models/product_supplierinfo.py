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
from odoo import fields, models, api


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    supplier_stock = fields.Float('Supplier stock')
    seller_children_ids = fields.Many2many(
        'res.partner',
        string='Seller children',
        compute='_compute_seller_children_ids',
        store=False,
        readonly=True
    )

    @api.depends('partner_id')
    def _compute_seller_children_ids(self):
        for record in self:
            if record.partner_id:
                record.seller_children_ids = self.env['res.partner'].search([('parent_id', '=', record.partner_id.id)])
            else:
                record.seller_children_ids = False

    @api.model
    def create(self, values):
        ctx = self.env.context.copy()
        res = super(ProductSupplierinfo, self.with_context(ctx).sudo()).create(values)
        properties = self.env['pms.property'].search([
            '|',
            ('seller_ids', 'in', res.partner_id.ids),
            ('seller_commercial_ids', 'in', res.partner_id.ids)
        ])
        if properties:
            properties.onchange_seller_ids()
        return res

    @api.model
    def unlink(self):
        partner_ids = self.mapped('partner_id')
        properties = self.env['pms.property'].search([
            '|',
            ('seller_ids', 'in', partner_ids.ids),
            ('seller_commercial_ids', 'in', partner_ids.ids)
        ])
        res = super(ProductSupplierinfo, self).unlink()
        if properties:
            properties.onchange_seller_ids()
        return res
