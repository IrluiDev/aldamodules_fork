from datetime import date, timedelta

from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    daily_kpi_ids = fields.One2many(
        comodel_name="pms.daily.kpi",
        inverse_name="pms_property_id",
        string="Daily KPIs",
    )

    kpi_count = fields.Integer(string="KPIs", compute="_compute_kpi_count")

    occupancy_rate = fields.Float(
        string="Occupancy Rate (%)",
        compute="_compute_daily_kpi",
        digits=(16, 2),
    )

    @api.depends("daily_kpi_ids")
    def _compute_kpi_count(self):
        for record in self:
            if record.daily_kpi_ids:
                record.kpi_count = len(record.daily_kpi_ids)
            else:
                record.kpi_count = False

    def action_open_kpis(self):
        action = self.env.ref("alda_pms_kpi.pms_property_daily_kpi_action").read()[0]
        action["domain"] = [("pms_property_id", "=", self.id)]
        action["context"] = {"default_pms_property_id": self.id}
        return action

    @api.model
    def create_or_update_daily_kpi(self, property_id, kpi_date):
        existing_kpi = self.search(
            [("date", "=", kpi_date), ("pms_property_id", "=", property_id)], limit=1
        )

        if existing_kpi:
            existing_kpi._compute_kpis()
            return existing_kpi

        new_kpi = self.create({"date": kpi_date, "pms_property_id": property_id})
        new_kpi._compute_kpis()
        return new_kpi

    def _create_kpi(self, date, property_id):
        return self.env["pms.daily.kpi"].create(
            {
                "date": date,
                "pms_property_id": property_id,
            }
        )

    @api.depends("daily_kpi_ids")
    def _compute_daily_kpi(self):
        today = fields.Date.today()

        for record in self:
            if not record.id:
                record.occupancy_rate = 0.0
                continue

            if record.daily_kpi_ids:
                record.kpi_count = len(record.daily_kpi_ids)
            else:
                record.kpi_count = False

            kpi = self.env["pms.daily.kpi"].create_or_update_daily_kpi(
                record.id,
                today,
            )

            record.update(
                {
                    "occupancy_rate": kpi.occupancy_rate or 0.0,
                }
            )

    def update_closed_day_kpis(self):
        closed_day = date.today() - timedelta(days=1)
        daily_kpi_model = self.env["pms.daily.kpi"]
        pms_properties = self.env["pms.property"].search([])

        for prop in pms_properties:
            kpi = daily_kpi_model.search(
                [("date", "=", closed_day), ("pms_property_id", "=", prop.id)],
                limit=1,
            )

            if not kpi:
                kpi = self._create_kpi(closed_day, prop.id)

            kpi._compute_kpis()
