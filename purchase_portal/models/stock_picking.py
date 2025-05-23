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

from odoo import models, fields, _


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'portal.mixin']

    property_id = fields.Many2one(
        'pms.property',
        string='Hotel',
        related='purchase_id.property_id',
        store=True,
        readonly=True,
    )

    def _compute_access_url(self):
        super(StockPicking, self)._compute_access_url()
        for picking in self:
            picking.access_url = '/my/stock_pickings/%s' % (picking.id)

    def _create_backorder(self):
        res = super(StockPicking, self)._create_backorder()
        text = self.env.context.get('backorder_message', False)
        if text:
            text = str(text)
            lines = ""

            for line in res.move_ids:
                lines += _("Product: <b>{}</b>, quantity: <b>{}</b><br/>").format(
                    line.product_id.display_name,
                    "{} {}".format(
                        line.purchase_line_id.product_qty if line.purchase_line_id else line.product_qty,
                        line.purchase_line_id.product_uom.display_name if line.purchase_line_id else line.product_uom_id.name,
                    )
                )
            message = _("Hi {}, <br/> {} {}").format(res.partner_id.name, text, lines)

            res.message_post(
                body=message, subtype_id=self.env.ref("mail.mt_comment").id
            )
        return res

    def picking_reception_status_mail(self):
        mt_comment = self.env.ref("mail.mt_comment")
        tpl = self.env.ref("purchase_portal.alda_picking_reception_status_email_template")
        self.message_post_with_template(
            tpl.id,
            composition_mode="mass_post",
            subtype_id=mt_comment.id,
            notify=True,
        )
