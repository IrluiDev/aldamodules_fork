from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    is_pms_form = fields.Boolean(
        string="Show team in PMS-Romdoo form",
        store=True,
        default=False,
        help="Indicates if the team will use the PMS-Roomdoo form.",
    )

    is_location_required = fields.Boolean(
        string="Location Required in form",
        store=True,
        default=False,
        help="Indicates if location will be required in the form.",
    )

    @api.onchange("is_pms_form")
    def _onchange_is_pms_form(self):
        if not self.is_pms_form:
            self.is_location_required = False

    @api.onchange("is_location_required")
    def _onchange_is_location_required(self):
        if not self.is_pms_form and self.is_location_required:
            self.is_pms_form = True

    @api.constrains("is_pms_form", "is_location_required")
    def _check_location_requires_pms_form(self):
        for record in self:
            if record.is_location_required and not record.is_pms_form:
                raise ValidationError(
                    _(
                        "Location Required can only be enabled if PMS Form is also enabled."
                    )
                )
