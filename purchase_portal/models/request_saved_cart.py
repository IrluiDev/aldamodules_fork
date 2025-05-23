# © 2023 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class WebsiteSavedCart(models.Model):

    _name = "purchase.request.saved.cart"
    _inherit = "portal.mixin"

    name = fields.Char()
    partner_id = fields.Many2one(
        'res.partner',
    )
    user_id = fields.Many2one(
        'res.users',
    )
    item_ids = fields.One2many('purchase.request.saved.cart.item', 'cart_id', string='Items')
    add_to_cart_url = fields.Char('Add to cart URL', compute='_compute_add_to_cart_url')
    add_to_cart_and_delete_url = fields.Char('Add to cart and delete URL', compute='_compute_add_to_cart_and_delete_url')
    delete_url = fields.Char('Delete URL', compute='_compute_delete_url')
    property_id = fields.Many2one('pms.property', string='Property')

    def _compute_access_url(self):
        for cart in self:
            cart.access_url = '/my/saved_carts/{}'.format(cart.id)

    def _compute_add_to_cart_url(self):
        for cart in self:
            cart.add_to_cart_url = '/shop/add_saved_cart/{}'.format(cart.id)

    def _compute_add_to_cart_and_delete_url(self):
        for cart in self:
            cart.add_to_cart_and_delete_url = '/shop/add_and_delete_saved_cart/{}'.format(cart.id)

    def _compute_delete_url(self):
        for cart in self:
            cart.delete_url = '/shop/delete_saved_cart/{}'.format(cart.id)


class WebsiteSavedCartItems(models.Model):

    _name = "purchase.request.saved.cart.item"

    cart_id = fields.Many2one(
        'purchase.request.saved.cart',
    )
    product_id = fields.Many2one(
        'product.product',
    )
    description = fields.Char(string='Description')
    product_qty = fields.Integer(string='Product Quantity', default=1, required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Product Unit of Measure')
    delete_url = fields.Char('Delete URL', compute='_compute_delete_url')

    def _compute_delete_url(self):
        for cart in self:
            cart.delete_url = '/shop/delete_saved_cart_item/{}'.format(cart.id)
