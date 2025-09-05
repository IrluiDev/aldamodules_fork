from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class PmsWizardGenerateBatchKpi(models.TransientModel):
    _name = "pms.wizard.generate.batch.kpi"
    _description = "Wizard to generate KPIs for multiple properties"

    date_start = fields.Date(
        string="Start Date Kpis",
        required=True,
        default=fields.Date.today,
    )
    date_end = fields.Date(
        string="End Date Kpis",
        required=True,
        default=lambda self: fields.Date.to_string(
            fields.Date.today() + timedelta(days=7)
        ),
    )
    property_ids = fields.Many2many(
        comodel_name="pms.property",
        relation="pms_wizard_property_rel",
        column1="wizard_id",
        column2="property_id",
        string="Propiedades",
        required=True,
        domain=[("room_ids", "!=", False)],
    )

    def action_generate_kpis(self):
        daily_kpi_model = self.env["pms.daily.kpi"]
        created_kpis = self.env["pms.daily.kpi"].sudo().browse([])
        today = fields.Date.today()
        current_date = self.date_start
        if current_date > today:
            raise ValidationError(_("KPIs can only be created no later than today."))

        for prop in self.property_ids:
            current_date = self.date_start
            while current_date <= self.date_end and current_date <= today:
                kpi = daily_kpi_model.create_or_update_daily_kpi(prop.id, current_date)
                created_kpis |= kpi
                current_date += timedelta(days=1)

        return {
            "type": "ir.actions.act_window",
            "name": "KPIs Generados",
            "res_model": "pms.daily.kpi",
            "view_mode": "tree,form",
            "domain": [("id", "in", created_kpis.ids)],
            "target": "current",
        }
