##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2020-2024  CommitSun (<http://www.commitsun.com>)
#                  2018-2024 Jose Luis Algara Toledo <osotranquilo@gmail.com>
#                  2024 Irlui Ramírez <irlui@aldahotels.com>
#                  Consultores hoteleros integrales - Alda Hotels
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "PMS Alda Hotels",
    "version": "16.0.1.0.0",
    "author": "Aldamodules, Commit [Sun], Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "category": "pms",
    "website": "https://github.com/OCA/pms",
    "depends": [
        "pms",
    ],
    "data": [
        "data/confirmation_template.xml",
        "data/exit_template.xml",
        "data/cancelation_template.xml",
        "data/modification_template.xml",
        "security/ir.model.access.csv",
        "views/pms_property_views.xml",
        "views/product_pricelist_views.xml",
        "views/precheckin_portal_templates.xml",
        "views/account_payment_views.xml",
        "views/report_templates.xml",
        "views/account_payment_register_views.xml",
    ],
    "installable": True,
}
