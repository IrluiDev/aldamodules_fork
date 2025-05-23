from odoo import fields, models


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    commercial_partner_id = fields.Many2one(
        "res.partner",
        string="Comercial Partner",
        readonly=True,
        help="Comercial partner of the supplier",
        related='partner_id.commercial_partner_id',
        store=True,
    )
