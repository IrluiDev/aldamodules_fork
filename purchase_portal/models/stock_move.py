from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_original_qty = fields.Float(
        'Original quantity',
        related='purchase_line_id.product_qty',
    )

    product_original_qty_uom = fields.Many2one(
        'uom.uom',
        'Original quantity uom',
        related='purchase_line_id.product_uom',
    )
