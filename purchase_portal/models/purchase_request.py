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

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _inherit = ['purchase.request', 'portal.mixin']

    property_id = fields.Many2one('pms.property', string='Property')

    @api.depends('state', 'review_ids')
    def _compute_access_url(self):
        super(PurchaseRequest, self)._compute_access_url()
        for purchase_request in self:
            if purchase_request.state in ["to_approve", "draft"] and not purchase_request.review_ids.filtered(lambda r: r.status == 'approved'):
                purchase_request.access_url = '/my/new_purchase_request/%s' % (purchase_request.id)
            else:
                purchase_request.access_url = '/my/purchase_requests/%s' % (purchase_request.id)

    def request_validation(self):
        res = super(PurchaseRequest, self).request_validation()
        if res.reviewer_ids:
            mt_comment = self.env.ref("mail.mt_comment")
            tpl = self.env.ref("purchase_portal.alda_purchase_request_validation")
            self.message_post_with_template(
                tpl.id,
                composition_mode="mass_post",
                subtype_id=mt_comment.id,
                notify=True,
            )
        return res

    def validate_tier(self):
        res = super(PurchaseRequest, self).validate_tier()
        self.button_approved()
        return res

    def button_approved(self):
        res = super(PurchaseRequest, self).button_approved()
        for pr in self:
            pr.message_subscribe(partner_ids=pr.property_id.partner_id.ids)
        return res

    def _check_completed_pr(self):
        pr_to_check = self.env['purchase.request'].search([
            ('state', '=', 'in_progress'),
        ])
        for pr in pr_to_check:
            if all(line.pending_qty_to_receive == 0 for line in pr.line_ids):
                pr.button_done()


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    property_id = fields.Many2one('pms.property', related="request_id.property_id", string='Property', store=True)
    suggested_supplier_id = fields.Many2one('res.partner', string='Suggested Supplier')

    @api.model
    def create(self, values):
        ctx = self.env.context.copy()
        portal = ctx.get('portal', False)
        if portal:
            request_id = values.get('request_id', False)
            product_id = values.get('product_id', False)
            product_qty = values.get('product_qty', False)

            request = self.env['purchase.request'].browse(request_id)
            product = self.env['product.product'].browse(product_id)
            if not product.sudo().seller_ids:
                raise UserError(_('There are no sellers for this product in the current company.'))

            pms_seller_ids = self.env['res.partner'].sudo().search([
                ('id', 'in', request.property_id.seller_ids.ids + request.property_id.seller_commercial_ids.ids)
            ])

            min_cost_productinfo = self.env["product.supplierinfo"].sudo().search([
                '&',
                ('partner_id', 'in', pms_seller_ids.ids),
                '|',
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('product_id', '=', product.id),
            ]).sorted(key=lambda r: r.price)
            if not min_cost_productinfo:
                raise UserError(_('There are no sellers allowed for this request.'))
            min_cost_productinfo = min_cost_productinfo[0]
            if min_cost_productinfo.partner_id.id not in request.property_id.seller_ids.ids:
                partner_id = request.property_id.seller_ids.filtered(
                    lambda x: x.commercial_partner_id.id == min_cost_productinfo.partner_id.id
                )
                values['supplier_id'] = partner_id.id
                values['suggested_supplier_id'] = partner_id.id
            else:
                values['suggested_supplier_id'] = min_cost_productinfo.partner_id.id
            # min_qty = product.seller_ids.filtered(lambda x: x.partner_id.id == request.property_id.seller_id.id).min_qty
            min_qty = min_cost_productinfo.min_qty

            if product_qty < min_qty:
                raise UserError(_('The minimum quantity for this product is %s') % min_qty)
            if request.review_ids:
                request.message_post(
                    body=_(
                        'New line added by {user}: <strong> {product} ({quantity})</strong>'
                    ).format(user=self.env.user.name, product=product.name, quantity=product_qty),
                    message_type='comment'
                )

        return super().create(values)

    def write(self, vals):
        ctx = self.env.context.copy()
        portal = ctx.get('portal', False)
        product_qty = vals.get('product_qty', False)
        no_msg = ctx.get('no_msg', False)
        if portal and product_qty:
            request = self.request_id
            product = self.product_id
            pms_seller_ids = self.env['res.partner'].sudo().search([
                ('id', 'in', self.request_id.property_id.seller_ids.ids + self.request_id.property_id.seller_commercial_ids.ids)
            ])

            min_cost_productinfo = self.env["product.supplierinfo"].sudo().search([
                '&',
                ('partner_id', 'in', pms_seller_ids.ids),
                '|',
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('product_id', '=', product.id),
            ]).sorted(key=lambda r: r.price)
            if not min_cost_productinfo:
                raise UserError(_('There are no sellers allowed for this request.'))
            min_cost_productinfo = min_cost_productinfo[0]

            if min_cost_productinfo.partner_id not in request.property_id.seller_ids:
                partner_id = request.property_id.seller_ids.filtered(
                    lambda x: x.commercial_partner_id.id == min_cost_productinfo.partner_id.id
                )

                vals['supplier_id'] = partner_id.id
                vals['suggested_supplier_id'] = partner_id.id
            else:
                vals['suggested_supplier_id'] = min_cost_productinfo.partner_id.id
            # min_qty = self.product_id.seller_ids.filtered(lambda x: x.partner_id.id == self.request_id.property_id.seller_id.id).min_qty
            min_qty = min_cost_productinfo.min_qty
            if product_qty < min_qty:
                raise UserError(_('The minimum quantity for this product is %s') % min_qty)
            if self.request_id.review_ids and not no_msg:
                self.request_id.message_post(
                    body=_('Line edited by {user}: <strong>{product} ({old_quantity} -> {quantity})</strong>').format(user=self.env.user.name, product=self.product_id.name, old_quantity=self.product_qty, quantity=product_qty),
                    message_type='comment'
                )
        return super().write(vals)

    def unlink(self):
        if self.request_id.review_ids:
            self.request_id.message_post(
                body=_('Line deleted by {user}: <strong> {product}</strong>').format(user=self.env.user.name, product=self.product_id.name),
                message_type='comment',
            )
        return super().unlink()

    def _autocreate_purchase_orders_from_lines(self):
        lines = self.env['purchase.request.line'].sudo().search([
            ('request_state', '=', 'approved'),
            ('purchase_state', '=', False),
        ])

        if lines:
            for hotel in lines.mapped('property_id'):
                ctx = self.env.context.copy()
                ctx['active_model'] = 'purchase.request.line'
                ctx['active_ids'] = lines.filtered(lambda r: r.property_id == hotel).ids
                supplier_id = lines.mapped('suggested_supplier_id')[0].id if lines.mapped('suggested_supplier_id') else \
                    lines.mapped('supplier_id')[0].id if lines.mapped('supplier_id') else False
                if not supplier_id:
                    _logger.error(_('No supplier found for purchase request lines %s') % lines.ids)
                    continue
                wiz = self.env['purchase.request.line.make.purchase.order'].with_context(ctx).create({
                    'supplier_id': supplier_id,
                    'multiple_suppliers': True if len(hotel.seller_ids) > 1 else False,
                    'property_id': hotel.id,
                    'sync_data_planned': True,
                })
                try:
                    res = wiz.make_purchase_order()
                    orders = res['domain'][0][2]
                    orno_duplicates = []
                    [orno_duplicates.append(item) for item in orders if item not in orno_duplicates]
                    order_ids = self.env['purchase.order'].browse(orno_duplicates)
                    for order in order_ids:
                        order.button_confirm()

                        ir_model_data = self.env['ir.model.data']
                        template_id = ir_model_data.check_object_reference('purchase', 'email_template_edi_purchase_done')[1]
                        mail_wiz = self.env['mail.compose.message'].create({
                            'res_id': order.id,
                            'template_id': template_id or False,
                            'model': 'purchase.order',
                            'composition_mode': 'comment'}
                        )
                        mail_wiz._onchange_template_id_wrapper()
                        mail_wiz.action_send_mail()
                except UserError as e:
                    _logger.warning(e)
                    continue
