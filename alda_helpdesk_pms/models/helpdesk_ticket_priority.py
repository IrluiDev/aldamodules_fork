import logging
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    priority_rule_id = fields.Many2one(
        "helpdesk.ticket.priority.rule",
        string="Applied Priority Rule",
        compute="_compute_priority_recomended_rule",
        ondelete="restrict",
        search="_search_priority_rule_id",
        help="Priority rule that was applied to this ticket",
    )

    priority_suggestion_action = fields.Html(
        string="Suggested Action",
        compute="_compute_priority_recomended_rule",
        help="Displays recommended actions based on the calculated,"
        " priority and business rules.",
    )

    priority_estimated = fields.Selection(
        related="priority_rule_id.priority_estimated",
        string="Estimated Priority",
        store=True,
        help="Automatically calculated priority based on business rules,"
        " and ticket characteristics.",
    )

    alert_level = fields.Selection(
        [
            ("none", "No Alert"),
            ("low", "Low Occupation"),
            ("medium", "Medium Occupation"),
            ("high", "High Occupation"),
            ("critical", "Critical Alert"),
        ],
        compute="_compute_alert_level",
        store=True,
        help="Indicates the occupancy level alert status based on room,"
        " availability and booking patterns.",
    )

    @api.onchange("priority_rule_id")
    def _onchange_priority_rule(self):
        if not self.priority_rule_id:
            self.alert_level = "none"

    @api.depends("priority_rule_id")
    def _compute_alert_level(self):
        for ticket in self:
            if not ticket.pms_property_id or not ticket.priority_rule_id:
                ticket.alert_level = "none"
                continue

            occ = ticket.occupancy_rate or 0.0

            if 0.0 < occ <= 0.30:
                ticket.alert_level = "low"
            elif 0.30 < occ <= 0.70:
                ticket.alert_level = "medium"
            elif occ > 0.70:
                ticket.alert_level = "critical"
            else:
                ticket.alert_level = "none"

    def _get_about_room(self, is_room, is_room_blocked):
        if is_room_blocked == "30":
            type_rule = "blocked_room"
        elif is_room == "20":
            type_rule = "unblocked"
        else:
            type_rule = "no_room"
        return type_rule

    def _get_days_blocked(self, total_days_blocked):
        if not total_days_blocked or total_days_blocked == 0:
            pass
        elif 1 <= total_days_blocked <= 15:
            return "300"
        elif 16 <= total_days_blocked <= 30:
            return "400"
        else:
            return "500"

    def _get_occupancy_rate(self, occupancy_rate):
        if 0.0 <= occupancy_rate <= 0.3:
            return "5"
        elif 0.31 <= occupancy_rate <= 0.7:
            return "15"
        else:
            return "30"

    def _get_block_rate(self, block_rate=0.0):
        if 0.0 <= block_rate <= 0.3:
            return "100"
        elif 0.31 <= block_rate <= 0.70:
            return "1000"
        else:
            return "10000"

    def _get_season(self, season_type):
        return "5" if (not season_type or season_type == "low") else "20"

    @api.model
    def _get_priority_estimated(
        self,
        pms_property_id,
        pms_room_id,
        create_date,
        is_room_operated_normaly,
        is_property_operated_normaly,
    ):
        date = datetime.now()
        is_pms_property_rule = "30" if pms_property_id else "0"
        is_room_operated_normaly_rule = "20" if is_room_operated_normaly else "0"
        is_property_operated_normaly_rule = (
            "20" if is_property_operated_normaly else "0"
        )
        is_room_blocked_rule = "0"
        days_blocked_rule = "0"
        is_room_related_rule = "0"
        if pms_room_id:
            is_room_operated_normaly = True
            is_property_operated_normaly = True
            is_room_operated_normaly_rule = "20"
            is_property_operated_normaly_rule = "20"
            is_room_related_rule = "20"
            room_record = self.env["pms.room"].sudo().browse(pms_room_id)
            is_room_blocked = (
                self.env["helpdesk.ticket"].sudo()._is_room_blocked(room_record)
            )
            if is_room_blocked:
                if not create_date:
                    start_date = date
                else:
                    start_date = create_date
                is_room_blocked_rule = "30"
                is_room_operated_normaly_rule = "0"
                total_days_blocked = self._calculate_blocked_room_adr(
                    pms_property_id, pms_room_id, start_date
                )
                total_days_blocked = total_days_blocked["total_days_blocked"]
                days_blocked_rule = (
                    self._get_days_blocked(total_days_blocked)
                    if total_days_blocked
                    else "0"
                )
                is_room_operated_normaly = False

        kpi_property = (
            self.env["pms.daily.kpi"]
            .sudo()
            .create_or_update_daily_kpi(pms_property_id, date)
        )

        occupancy_rate = kpi_property.occupancy_rate if kpi_property else 0.0
        block_rate = kpi_property.block_rate if kpi_property else 0.0

        type_rule = self._get_about_room(is_room_related_rule, is_room_blocked_rule)
        occupancy_rate_rule = self._get_occupancy_rate(occupancy_rate)
        block_rate_rule = self._get_block_rate(block_rate)
        season = self._get_season_type(date)
        self._get_season(season)

        domain = [
            ("type_rule", "=", type_rule or "0"),
            ("is_pms_property", "=", is_pms_property_rule or "0"),
            ("is_room_related", "=", is_room_related_rule),
            ("is_room_blocked", "=", is_room_blocked_rule or "0"),
            ("days_blocked", "=", days_blocked_rule or "0"),
            ("occupancy_rate", "=", occupancy_rate_rule or "5"),
            ("block_rate", "=", block_rate_rule or "100"),
            ("is_room_operated_normaly", "=", is_room_operated_normaly_rule),
            (
                "is_property_operated_normaly",
                "=",
                is_property_operated_normaly_rule or "20",
            ),
        ]
        priority_rule_record = (
            self.env["helpdesk.ticket.priority.rule"].sudo().search(domain, limit=1)
        )
        if not priority_rule_record:
            return (
                False,
                False,
                False,
                is_room_operated_normaly,
                is_property_operated_normaly,
            )

        return (
            priority_rule_record.id if priority_rule_record else False,
            priority_rule_record.priority_estimated if priority_rule_record else "0",
            priority_rule_record.priority_suggestion_action
            if priority_rule_record
            else False,
            is_room_operated_normaly if is_room_operated_normaly else False,
            is_property_operated_normaly if is_property_operated_normaly else False,
        )

    @api.depends(
        "pms_property_id",
        "pms_room_id",
        "is_bathroom",
        "is_room_blocked",
        "total_days_blocked",
        "occupancy_rate",
        "blocked_rooms",
        "season_type",
        "is_room_operated_normaly",
        "is_property_operated_normaly",
    )
    def _compute_priority_recomended_rule(self):
        for ticket in self:

            if ticket.env.context.get("from_web_create"):
                ticket.priority_rule_id = False
                ticket.priority_estimated = False
                ticket.priority_suggestion_action = False
                continue

            if not ticket.pms_property_id:
                ticket.priority_rule_id = False
                ticket.priority_estimated = False
                ticket.priority_suggestion_action = False
                continue

            (
                rule_id,
                priority_estimated,
                action_suggestion,
                room_operated,
                property_operated,
            ) = self._get_priority_estimated(
                ticket.pms_property_id.id,
                ticket.pms_room_id.id or False,
                ticket.create_date,
                ticket.is_room_operated_normaly,
                ticket.is_property_operated_normaly,
            )

            ticket.priority_rule_id = rule_id if rule_id else False
            ticket.priority_estimated = (
                priority_estimated if priority_estimated else "0"
            )
            ticket.priority_suggestion_action = (
                action_suggestion if action_suggestion else False
            )
            ticket.is_room_operated_normaly = room_operated if room_operated else False
            ticket.is_property_operated_normaly = (
                property_operated
                if property_operated
                else ticket.is_property_operated_normaly
            )

    def _search_priority_rule_id(self, operator, value):
        return [("priority_rule_id", operator, value)]
