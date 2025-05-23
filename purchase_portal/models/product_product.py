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
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    purchase_property_ids = fields.Many2many(
        'pms.property',
        string='Allowed in properties',
        relation="pms_property_product_product_rel",
        column1="property_id",
        column2="product_id",
    )

    def get_supplier_stock(self, purchase_request):
        self.ensure_one()
        supplier_stock = 0.0
        if self.seller_ids:
            seller = self.seller_ids.filtered(lambda x: x.partner_id.id in purchase_request.property_id.seller_ids.ids).sorted(key=lambda r: r.price)[0]
            if seller:
                supplier_stock = seller.supplier_stock
        return supplier_stock

    def get_supplier_lowest_price(self):
        self.ensure_one()
        lowest_price = self.standard_price
        if self.seller_ids:
            lowest_price = self.seller_ids.sorted(key=lambda r: r.price)[0].price
        return lowest_price

    def get_first_attachment(self):
        self.ensure_one()
        return self.env['ir.attachment'].search([('res_model', '=', 'product.template'), ('res_id', '=', self.product_tmpl_id.id)], limit=1)
