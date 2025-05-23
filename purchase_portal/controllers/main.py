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

import werkzeug
from odoo.http import request
from werkzeug.exceptions import Unauthorized
from odoo.osv.expression import OR
from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.web.controllers.main import ensure_db
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.exceptions import UserError


class PortalAccount(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'purchase_request_count' in counters:
            purchase_request_count = request.env['purchase.request'].search_count(self._get_purchase_requests_domain()) \
                if request.env['purchase.request'].check_access_rights('read', raise_exception=False) else 0
            values['purchase_request_count'] = purchase_request_count

        # stock.picking
        if 'stock_picking_count' in counters:
            stock_picking_count = request.env['stock.picking'].search_count(self._get_stock_pickings_domain()) \
                if request.env['stock.picking'].check_access_rights('read', raise_exception=False) else 0
            values['stock_picking_count'] = stock_picking_count

        # product.product
        if 'product_product_count' in counters:
            product_product_count = request.env['product.product'].search_count(self._get_product_product_domain()) \
                if request.env['product.product'].check_access_rights('read', raise_exception=False) else 0
            values['product_product_count'] = product_product_count

        # purchase.request.saved.cart
        values['saved_carts_count'] = request.env['purchase.request.saved.cart'].search_count(self._get_filter_domain())
        return values

    # ------------------------------------------------------------
    # My purchase requests
    # ------------------------------------------------------------

    def _purchase_request_get_page_view_values(self, purchase_request, access_token, **kwargs):
        values = {
            'page_name': 'purchase_request',
            'purchase_request': purchase_request,
        }
        return self._get_page_view_values(purchase_request, access_token, values, 'my_purchase_request_history', False, **kwargs)

    def _get_purchase_requests_domain(self):
        user = request.env['res.users'].sudo().browse(request.uid)

        return [('property_id', 'in', user.pms_property_ids.ids)]

    @http.route(['/my/purchase_requests', '/my/purchase_requests/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_purchase_request(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        PurchaseRequest = request.env['purchase.request']

        domain = self._get_purchase_requests_domain()

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date_start desc, name desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state, name desc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            '00-all': {'label': _('All'), 'domain': []},
            '01-draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            '02-approved': {'label': _('Approved'), 'domain': [('state', '=', 'approved')]},
            '03-in_progress': {'label': _('In Progress'), 'domain': [('state', '=', 'in_progress')]},
            '04-done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
            '05-cancelled': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancelled')]},
        }
        user = request.env['res.users'].sudo().browse(request.uid)
        count = len(searchbar_filters)
        for property_id in user.pms_property_ids:
            key = str(count) + "-" + property_id.name
            if count < 10:
                key = "0" + key
            searchbar_filters[key] = {
                'label': property_id.name,
                'domain': [('property_id', '=', property_id.id)]
            }
            count += 1
        # default filter by value
        if not filterby:
            filterby = '00-all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('date_start', '>', date_begin), ('date_start', '<=', date_end)]

        # count for pager
        purchase_request_count = PurchaseRequest.sudo().search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/purchase_requests",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=purchase_request_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        purchase_requests = PurchaseRequest.sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_purchase_request_history'] = purchase_requests.ids[:100]

        values.update({
            'date': date_begin,
            'purchase_requests': purchase_requests,
            'page_name': 'purchase_request',
            'pager': pager,
            'default_url': '/my/purchase_requests',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("purchase_portal.portal_my_purchase_requests", values)

    @http.route(['/my/purchase_requests/<int:purchase_request>'], type='http', auth="public", website=True)
    def portal_my_purchase_requests_detail(self, purchase_request, access_token=None, report_type=None, download=False, **kw):
        try:
            purchase_request_sudo = self._document_check_access('purchase.request', purchase_request, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._purchase_request_get_page_view_values(purchase_request_sudo, access_token, **kw)

        return request.render("purchase_portal.portal_purchase_request_page", values)

    @http.route(['/my/new_purchase_request', '/my/new_purchase_request/<int:purchase_request>'], type='http', auth="public", website=True)
    def portal_my_new_purchase_requests_detail(self, purchase_request=None, access_token=None, report_type=None, download=False, **kw):
        if not purchase_request and kw and kw.get('property_id', False):
            property_id = kw.get('property_id', False)
            purchase_request = request.env['purchase.request'].create({
                'property_id': int(property_id),
            })
            return request.redirect('/my/new_purchase_request/%s' % purchase_request.id)
        if not purchase_request:
            values = values = {
                'page_name': 'purchase_request',
                'purchase_request': False,
            }
        else:
            try:
                purchase_request_sudo = self._document_check_access('purchase.request', purchase_request, access_token)
            except (AccessError, MissingError):
                return request.redirect('/my')

            if purchase_request_sudo.state not in ["to_approve", "draft"] or purchase_request_sudo.review_ids.filtered(lambda r: r.status == 'approved'):
                return request.redirect('/my/purchase_requests/%s' % purchase_request_sudo.id)

            values = self._purchase_request_get_page_view_values(purchase_request_sudo, access_token, **kw)

        allowed_pms_property_ids = request.env.user.pms_property_ids.ids
        if allowed_pms_property_ids:
            allowed_pms_property_ids = request.env['pms.property'].browse(allowed_pms_property_ids).filtered(lambda x: x.company_id == request.env.company)

        if values['purchase_request'] and values['purchase_request'].property_id:
            values['current_property_id'] = values['purchase_request'].property_id
        else:
            values['current_property_id'] = allowed_pms_property_ids[0] if allowed_pms_property_ids else False
        values['allowed_property_ids'] = allowed_pms_property_ids if allowed_pms_property_ids else False

        return request.render("purchase_portal.portal_new_purchase_request_page", values)

    # ------------------------------------------------------------
    # My stock pickings
    # ------------------------------------------------------------

    def _stock_picking_get_page_view_values(self, stock_picking, access_token, **kwargs):
        values = {
            'page_name': 'stock_picking',
            'stock_picking': stock_picking,
        }
        return self._get_page_view_values(stock_picking, access_token, values, 'my_stock_picking_history', False, **kwargs)

    def _get_stock_pickings_domain(self):
        user = request.env['res.users'].sudo().browse(request.uid)

        return [
            ('picking_type_id.code', '=', 'incoming'),
            ('property_id', 'in', user.pms_property_ids.ids),
        ]

    @http.route(['/my/stock_pickings', '/my/stock_pickings/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_stock_pickings(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        StockPicking = request.env['stock.picking']

        domain = self._get_stock_pickings_domain()

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'scheduled_date desc, name desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'origin': {'label': _('Origin'), 'order': 'origin desc, name desc'},
            'state': {'label': _('Status'), 'order': 'state, name desc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            '00-all': {'label': _('All'), 'domain': []},
            '01-draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            '02-waiting': {'label': _('Waiting for other operation'), 'domain': [('state', '=', 'waiting')]},
            '03-confirmed': {'label': _('On Wait'), 'domain': [('state', '=', 'confirmed')]},
            '04-assigned': {'label': _('Assigned'), 'domain': [('state', '=', 'assigned')]},
            '05-done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
            '06-cancel': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancel')]},
        }

        user = request.env['res.users'].sudo().browse(request.uid)
        count = len(searchbar_filters)
        for property_id in user.pms_property_ids:
            key = str(count) + "-" + property_id.name
            if count < 10:
                key = "0" + key
            searchbar_filters[key] = {
                'label': property_id.name,
                'domain': [('property_id', '=', property_id.id)]
            }
            count += 1

        # default filter by value
        if not filterby:
            filterby = '00-all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('scheduled_date', '>', date_begin), ('scheduled_date', '<=', date_end)]

        # count for pager
        stock_picking_count = StockPicking.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/stock_pickings",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=stock_picking_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        stock_pickings = StockPicking.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_stock_picking_history'] = stock_pickings.ids[:100]

        values.update({
            'date': date_begin,
            'stock_pickings': stock_pickings,
            'page_name': 'stock_picking',
            'pager': pager,
            'default_url': '/my/stock_pickings',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("purchase_portal.portal_my_stock_pickings", values)

    @http.route(['/my/stock_pickings/<int:stock_picking>'], type='http', auth="public", website=True)
    def portal_my_stock_pickings_detail(self, stock_picking=None, access_token=None, **kw):
        try:
            stock_picking_sudo = self._document_check_access('stock.picking', stock_picking, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._stock_picking_get_page_view_values(stock_picking_sudo, access_token, **kw)

        if stock_picking_sudo.company_id:
            values['res_company'] = stock_picking_sudo.company_id

        return request.render("purchase_portal.portal_stock_picking_page", values)

    @http.route(['/portal_purchase_login_by_token/<int:user_id>'], type='http', auth="public", website=True)
    def portal_purchase_login_by_token(self, user_id=None, access_token=None, **kw):
        # localhost:14069/portal_purchase_login_by_token/381?signup_token=1LCzJ80sGoNu4ODEBl5C
        ensure_db()
        signup_token = kw.get('signup_token', False)
        # config_id = kw.get('config_id', False)

        if not user_id or not signup_token:
            raise Unauthorized("Wrong authentication")

        portal_user = request.env['res.users'].sudo().browse(user_id)

        if portal_user:
            cur_user = request.env['res.users'].browse(request.env.uid)
            is_public = cur_user._is_public()
            if (is_public or cur_user.id != portal_user.id) and signup_token == portal_user.signup_token:
                request.session.logout(keep_db=True)
                request.session.authenticate(request.db, portal_user.login, signup_token)
        url = "/my/new_purchase_request"
        return werkzeug.utils.redirect(url)

    # ------------------------------------------------------------
    # My product product
    # ------------------------------------------------------------

    def _get_product_product_domain(self):
        user = request.env['res.users'].sudo().browse(request.uid)
        return [('id', 'in', user.mapped('pms_property_ids.product_ids').ids)]

    def _get_product_searchbar_inputs(self):
        return {
            'all': {'input': 'all', 'label': _('Search in All')},
            'name': {'input': 'name', 'label': _('Search in Name')},
            'default_code': {'input': 'default_code', 'label': _('Search in reference')},
        }

    def _get_product_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ('default_code', 'all'):
            search_domain = OR([search_domain, [('default_code', 'ilike', search)]])
        if search_in in ('name', 'all'):
            search_domain = OR([search_domain, [('name', 'ilike', search)]])
        return search_domain

    @http.route(['/my/product_list', '/my/product_list/page/<int:page>'], type='http', auth="user", website=True)
    def portal_product_list(self, page=1, sortby=None, search=None, search_in='all', filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        ProductProduct = request.env['product.product']

        domain = self._get_product_product_domain()

        searchbar_inputs = self._get_product_searchbar_inputs()

        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name desc'},
            'default_code': {'label': _('Reference'), 'order': 'default_code desc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'active': {'label': _('Active'), 'domain': [('active', '=', True)]},
            'inactive': {'label': _('Inactive'), 'domain': [('active', '=', False)]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if search and search_in:
            domain += self._get_product_search_domain(search_in, search)

        # count for pager
        product_product_count = ProductProduct.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/product_list",
            url_args={'sortby': sortby, 'search_in': search_in, 'search': search, 'filterby': filterby},
            total=product_product_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        product_products = ProductProduct.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_stock_picking_history'] = product_products.ids[:100]

        values.update({
            'product_products': product_products,
            'page_name': 'product_product',
            'pager': pager,
            'default_url': '/my/product_list',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'search_in': search_in,
            'search': search,
            'searchbar_inputs': searchbar_inputs,
        })
        return request.render("purchase_portal.portal_product_product", values)

    # ------------------------------------------------------------
    # My purchase requests saved carts
    # ------------------------------------------------------------

    def _saved_cart_get_page_view_values(self, saved_cart, access_token, **kwargs):
        values = {
            'page_name': 'Saved cart',
            'saved_cart': saved_cart,
        }
        return self._get_page_view_values(
            saved_cart, access_token, values, 'my_saved_carts_history', False, **kwargs)

    def _get_filter_domain(self):
        return [('user_id', '=', request.env.user.id)]

    @http.route(['/my/saved_carts', '/my/saved_carts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_saved_carts(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        saved_cart_obj = request.env['purchase.request.saved.cart']
        domain = self._get_filter_domain()
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name desc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        # count for pager
        saved_cart_count = saved_cart_obj.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/saved_carts",
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
            },
            total=saved_cart_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        saved_carts = saved_cart_obj.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_saved_carts_history'] = saved_carts.ids[:100]
        values.update({
            'date': date_begin,
            'saved_carts': saved_carts,
            'page_name': 'Saved Carts',
            'pager': pager,
            'default_url': '/my/saved_carts',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("purchase_portal.portal_my_saved_carts", values)

    @http.route(['/my/saved_carts/<int:saved_cart_id>'], type='http', auth="public", website=True)
    def portal_my_saved_cart_detail(self, saved_cart_id, access_token=None, report_type=None, download=False, **kw):
        try:
            saved_cart_sudo = self._document_check_access('purchase.request.saved.cart', saved_cart_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(
                model=saved_cart_sudo,
                report_type=report_type,
                report_ref='purchase_portal.report_saved_cart_action',
                download=download,
            )

        values = self._saved_cart_get_page_view_values(saved_cart_sudo, access_token, **kw)
        return request.render("purchase_portal.portal_saved_cart_page", values)

    @http.route(['/save_purchase_request/<int:purchase_request>'], type='http', auth="public", website=True)
    def portal_save_current_cart(self, purchase_request=None, access_token=None, **kw):
        if purchase_request:
            order_id = request.env['purchase.request'].browse(purchase_request)
            item_ids = []
            for line in order_id.sudo().line_ids:
                item_ids.append({
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'product_uom_id': line.product_uom_id.id,
                    'description': line.name,
                })
            saved_cart = request.env['purchase.request.saved.cart'].create({
                'name': order_id.display_name,
                'user_id': order_id.requested_by.id,
                'partner_id': order_id.requested_by.partner_id.id,
                'property_id': order_id.property_id.id,
                'item_ids': [(0, 0, x) for x in item_ids],
            })
            return request.redirect('/my/saved_carts/{}'.format(saved_cart.id))

        return request.redirect('/my')

    @http.route(['/delete_purchase_request/<int:purchase_request>'], type='http', auth="public", website=True)
    def portal_delete_current_cart(self, purchase_request=None, access_token=None, **kw):
        if purchase_request:
            order_id = request.env['purchase.request'].browse(purchase_request)
            if order_id.state in ['draft']:
                order_id.sudo().unlink()
            else:
                raise UserError(_('You can only delete draft purchase requests.'))

        return request.redirect('/my')

    def _add_saved_cart(self, saved_cart):
        purchase_r = request.env['purchase.request'].create({
            'requested_by': saved_cart.user_id.id,
            'property_id': saved_cart.property_id.id,
        })
        for line in saved_cart.item_ids:
            product_info = request.env['product.supplierinfo'].sudo().search([
                '|',
                ('partner_id', 'in', purchase_r.property_id.seller_ids.ids),
                ('partner_id', 'in', purchase_r.property_id.seller_commercial_ids.ids),
                '|',
                ('product_id', '=', line.product_id.id),
                ('product_tmpl_id.product_variant_ids', '=', line.product_id.id),
            ], order='price asc', limit=1)

            supplier_id = False
            if product_info:
                if product_info.partner_id.id in purchase_r.property_id.seller_ids.ids:
                    supplier_id = product_info.partner_id.id
                elif product_info.partner_id.id in purchase_r.property_id.seller_commercial_ids.ids:
                    supplier_id = purchase_r.sudo().property_id.seller_ids.filtered(
                        lambda x: x.commercial_partner_id.id == product_info.partner_id.id
                    )[0].id

            request.env['purchase.request.line'].create({
                'request_id': purchase_r.id,
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'product_uom_id': line.product_uom_id.id,
                'estimated_cost': (product_info.price * line.product_qty) if product_info else 0,
                'suggested_supplier_id': supplier_id,
                'supplier_id': supplier_id,
                'name': line.description,
            })

        return purchase_r

    def _delete_saved_cart(self, saved_cart):
        saved_cart.unlink()

    @http.route(['/shop/add_saved_cart/<int:saved_cart_id>'], type='http', auth="public", website=True)
    def portal_add_saved_cart(self, saved_cart_id, access_token=None, report_type=None, download=False, **kw):
        try:
            saved_cart = self._document_check_access('purchase.request.saved.cart', saved_cart_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        saved_cart = request.env['purchase.request.saved.cart'].browse(saved_cart_id)
        if saved_cart:
            purchase_r = self._add_saved_cart(saved_cart)

            if purchase_r:
                return request.redirect('/my/new_purchase_request/' + str(purchase_r.id))

        return request.redirect('/my')

    @http.route(['/shop/delete_saved_cart/<int:saved_cart_id>'], type='http', auth="public", website=True)
    def portal_delete_saved_cart(self, saved_cart_id, access_token=None, report_type=None, download=False, **kw):
        try:
            saved_cart = self._document_check_access('purchase.request.saved.cart', saved_cart_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        saved_cart = request.env['purchase.request.saved.cart'].browse(saved_cart_id)
        if saved_cart:
            self._delete_saved_cart(saved_cart)
        return request.redirect('/my/saved_carts')

    @http.route(['/shop/add_and_delete_saved_cart/<int:saved_cart_id>'], type='http', auth="public", website=True)
    def portal_add_and_delete_saved_cart(self, saved_cart_id, access_token=None, report_type=None, download=False, **kw):
        try:
            saved_cart = self._document_check_access('purchase.request.saved.cart', saved_cart_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        saved_cart = request.env['purchase.request.saved.cart'].browse(saved_cart_id)
        if saved_cart:
            purchase_r = self._add_saved_cart(saved_cart)
            self._delete_saved_cart(saved_cart)

            if purchase_r:
                return request.redirect('/my/new_purchase_request/' + str(purchase_r.id))

        return request.redirect('/my')

    @http.route(['/shop/delete_saved_cart_item/<int:item_id>'], type='http', auth="public", website=True)
    def portal_delete_saved_cart_item(self, item_id, access_token=None, report_type=None, download=False, **kw):
        try:
            saved_cart_sudo = self._document_check_access('purchase.request.saved.cart.item', item_id, access_token)
            saved_cart_sudo
        except (AccessError, MissingError):
            return request.redirect('/my')
        item = request.env['purchase.request.saved.cart.item'].browse(item_id)
        if item:
            return_url = item.cart_id.get_portal_url()
            item.unlink()
            return request.redirect(return_url)
        return request.redirect('/my/saved_carts')
