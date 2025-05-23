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


class PMSProperty(models.Model):
    _inherit = 'pms.property'
    seller_ids = fields.Many2many('res.partner', string='Vendors allowed in this property')
    seller_commercial_ids = fields.Many2many(
        'res.partner',
        string='Vendors allowed in this property',
        relation="pms_property_seller_commercial_rel",
        column1="seller_id",
        column2="commercial_id",
        compute="_compute_seller_commercial_ids",
        store=True
    )

    product_ids = fields.Many2many(
        'product.product',
        string='Allowed products',
        relation="pms_property_product_product_rel",
        column1="product_id",
        column2="property_id",
    )

    product_seller_ids = fields.Many2many(
        'product.product',
        string='Allowed products',
        relation="pms_property_product_product_seller_rel",
        column1="product_id",
        column2="property_id",
    )

    wharehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')

    @api.depends('seller_ids')
    def _compute_seller_commercial_ids(self):
        for record in self:
            record.seller_commercial_ids = record.seller_ids.mapped('commercial_partner_id')

    @api.onchange("seller_ids")
    def onchange_seller_ids(self):
        self._compute_seller_commercial_ids()
        for hotel in self:
            if hotel.seller_ids:
                seller_products = self.env['product.supplierinfo'].search([
                    '|',
                    ('partner_id', 'in', hotel.seller_ids.ids),
                    ('partner_id', 'in', hotel.seller_commercial_ids.ids)
                ])
                seller_product_product = seller_products.mapped('product_tmpl_id.product_variant_ids')
                seller_product_product += seller_products.mapped('product_id')
                hotel.product_seller_ids = [(6, 0, seller_product_product.ids)]
            else:
                hotel.product_seller_ids = [(5,)]

    def action_load_all_seller_products(self):
        for prop in self:
            prop.onchange_seller_ids()
            prop.product_ids = prop.product_seller_ids

    def action_remove_products_not_in_sellers(self):
        for prop in self:
            prop.onchange_seller_ids()
            prop.product_ids = [(6, 0, prop.product_ids.filtered(lambda x: x.id in prop.product_seller_ids.ids).ids)]

    def action_open_supplier_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Supplier Products',
            'res_model': 'supplier.products.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_hotel_id': self.id,
            }
        }
