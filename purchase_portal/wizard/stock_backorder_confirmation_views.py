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

from odoo import _, api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    @api.model
    def default_get(self, fields):
        res = super(StockBackorderConfirmation, self).default_get(fields)
        res['backorder_message'] = _("The following products didn't arrive:")
        return res

    send_mail_to_seller = fields.Boolean('Mail to seller', default=False)
    backorder_message = fields.Html('Mail to seller content', help='A line will be added for each product not received')

    def process(self):
        ctx = self.env.context.copy()
        if self.send_mail_to_seller:
            ctx['backorder_message'] = self.backorder_message
        super(StockBackorderConfirmation, self.with_context(ctx)).process()
        return True
