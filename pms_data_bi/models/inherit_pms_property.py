# Copyright 2019-2021 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class InheritResCompany(models.Model):
    _inherit = "pms.property"

    expedia_rate = fields.Integer(
        "Expedia Rate DataBI",
        default=18,
        required=True,
        help="It is the commission percentage negotiated with the \
        Expedia company, expressed with two digits. \
        Example: 18 = 18% commission.",
    )

    status_send_property = fields.Boolean(
        "Send property DataBi",
        default=True,
        help="the condition of property that must be met \
            for it to be shared.",
    )
