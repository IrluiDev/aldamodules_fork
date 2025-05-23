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
from odoo import models, fields


class ResPartner(models.Model):

    _inherit = "res.partner"

    min_purchase_amount = fields.Float('Minimum purchase amount')
    saved_cart_count = fields.Integer(compute='_compute_saved_cart_count', string='Saved Cart Count')
    saved_cart_ids = fields.One2many('purchase.request.saved.cart', 'partner_id', string='Saved carts')

    def _compute_saved_cart_count(self):
        for partner in self:
            partner.saved_cart_count = len(partner.saved_cart_ids)
