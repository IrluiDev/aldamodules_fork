import logging
from datetime import datetime, timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PmsDailyKpi(models.Model):
    _name = "pms.daily.kpi"
    _inherit = "pms.kpi.mixin"
    _description = "Property Daily KPIs"
    _rec_name = "date"

    date = fields.Date(default=fields.Date.today(), required=True)
    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="PMS Property",
        required=True,
        index=True,
        domain=[("room_ids", "!=", False)],
    )

    total_rooms = fields.Integer(
        string="Total of Rooms",
        compute="_compute_kpis",
        store=True,
    )
    occupied_rooms = fields.Integer(
        string="Total Occupied Rooms",
        compute="_compute_kpis",
        store=True,
    )
    blocked_rooms = fields.Integer(
        string="Total Blocked Rooms",
        compute="_compute_kpis",
        store=True,
    )

    available_rooms = fields.Integer(
        string="Total Available Rooms",
        compute="_compute_kpis",
        store=True,
    )

    pax = fields.Integer(
        string="Total Pax",
        compute="_compute_kpis",
        store=True,
    )

    # Calculated KPIs
    available_rate = fields.Float(
        string="Available Rate (%)",
        compute="_compute_kpis",
        digits=(16, 2),
        store=True,
    )

    occupancy_rate = fields.Float(
        string="Occupancy Rate (%)",
        compute="_compute_kpis",
        digits=(16, 2),
        store=True,
    )
    block_rate = fields.Float(
        string="Block Rate (%)",
        compute="_compute_kpis",
        digits=(16, 2),
        store=True,
    )

    # Revenue KPIs
    room_revenue = fields.Float(
        string="Property Room Revenue",
        compute="_compute_kpis",
        store=True,
    )
    adr = fields.Float(
        string="Average Daily Rate",
        compute="_compute_kpis",
        digits=(16, 2),
        store=True,
    )
    revpar = fields.Float(
        string="RevPAR",
        compute="_compute_kpis",
        digits=(16, 2),
        store=True,
    )

    last_updated = fields.Datetime(
        string="Date Last Updated",
    )

    @api.model
    def create_or_update_daily_kpi(self, property_id, kpi_date):
        self.env.cr.execute(
            "SELECT id FROM pms_daily_kpi WHERE date = %s AND pms_property_id = %s FOR UPDATE",
            (kpi_date, property_id),
        )
        existing_kpi = self.search(
            [("date", "=", kpi_date), ("pms_property_id", "=", property_id)], limit=1
        )

        now = datetime.now()
        if existing_kpi:
            existing_kpi._compute_kpis()
            return existing_kpi
        else:
            new_kpi = self.create(
                {
                    "date": kpi_date,
                    "pms_property_id": property_id,
                    "last_updated": now,
                }
            )
            new_kpi._compute_kpis()
            return new_kpi

    @api.depends("date", "pms_property_id")
    def _compute_kpis(self):
        for record in self:
            if not record.pms_property_id:
                continue

            if record.pms_property_id:
                kpi_data = self._calculate_daily_kpis(
                    record.date, record.pms_property_id.id
                )
                record.update(kpi_data)

    def generate_historical_kpis(self, days_back=365):
        pms_property = self.env["pms.property"]
        for prop in pms_property.search([]):

            for i in range(-days_back, 0):
                current_date = fields.Date.today() + timedelta(days=i)

                existing = self.search(
                    [
                        ("date", "=", current_date),
                        ("pms_property_id", "=", prop.id),
                    ],
                    limit=1,
                )

                if not existing:
                    try:
                        kpi_data = self._calculate_daily_kpis(current_date, prop.id)
                        kpi_data.update(
                            {
                                "date": current_date,
                                "pms_property_id": prop.id,
                                "_kpi_calculated": True,
                            }
                        )
                        self.create(kpi_data)
                        _logger.info(
                            "KPI generado para %s - %s", prop.name, current_date
                        )
                    except Exception as e:
                        _logger.error(
                            "Error generando KPI para %s - %s: %s",
                            prop.name,
                            current_date,
                            str(e),
                        )

    _sql_constraints = [
        (
            "property_date_uniq",
            "unique(pms_property_id, date)",
            "Only one property KPI can be taken per day!",
        )
    ]
