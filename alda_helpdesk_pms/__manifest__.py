##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2025 Consultores Hoteleros Integrales Alda Hotels All Rights Reserved
#    Jose Luis Algara Toledo <informatica@aldahotels.com>
#    Irlui Tupac Ramírez Hernández <irlui@aldahotels.com>
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

{
    "name": "Helpdesk PMS Alda",
    "summary": "Create tickets related with the property",
    "version": "16.0.1.0.0",
    "author": "Odoo Community Association (OCA),"
    "Irlui Ramirez (Alda Hotels), Jose Luis Algara (Alda Hotels)",
    "website": "https://github.com/OCA/pms",
    "license": "LGPL-3",
    "depends": ["website", "helpdesk", "alda_helpdesk_pms_enterprise", "alda_pms_kpi"],
    "category": "PMS",
    "data": [
        "security/ir.model.access.csv",
        "report/helpdesk_analysis_views.xml",
        "views/menu_item.xml",
        "views/helpdesk_ticket_type_views.xml",
        "views/helpdesk_ticket_views.xml",
        "views/helpdesk_pms_form_template.xml",
        "views/helpdesk_ticket_priority_rule_views.xml",
        "views/helpdesk_team_views.xml",
        "data/ir_cron.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "alda_helpdesk_pms/static/src/js/ticket_form.js",
        ],
    },
    "installable": True,
    "application": True,
}
