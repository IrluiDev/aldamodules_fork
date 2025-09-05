from odoo import api, fields, models


class PmsKpiMixin(models.AbstractModel):
    _name = "pms.kpi.mixin"
    _description = "Mixin calculate KPIs"

    @api.model
    def _calculate_daily_kpis(self, date=None, property_id=None):
        date = date or fields.Date.today()

        is_overnight_room = (
            self.env["pms.room.type"].sudo().search([("overnight_room", "=", True)]).ids
        )

        total_rooms = (
            self.env["pms.room"]
            .sudo()
            .search_count(
                [
                    ("room_type_id", "in", is_overnight_room),
                    ("active", "=", True),
                    ("pms_property_id", "=", property_id),
                ]
            )
        )
        if total_rooms == 0:
            return {
                "total_rooms": 0,
                "occupied_rooms": 0,
                "blocked_rooms": 0,
                "available_rooms": 0,
                "pax": 0,
                "available_rate": 0,
                "occupancy_rate": 0,
                "block_rate": 0,
                "room_revenue": 0,
                "adr": 0,
                "revpar": 0,
                "last_updated": fields.Datetime.now(),
            }

        reservation_lines = (
            self.env["pms.reservation.line"]
            .sudo()
            .search(
                [
                    ("date", "=", date),
                    ("pms_property_id", "=", property_id),
                    ("room_id.room_type_id", "in", is_overnight_room),
                    ("room_id.active", "=", True),
                ]
            )
        )

        occupied_rooms = sum(
            1
            for line in reservation_lines
            if line.reservation_id.reservation_type in ["normal", "staff"]
            and line.state not in ["draft", "cancel"]
        )

        blocked_rooms = sum(
            1
            for line in reservation_lines
            if line.reservation_id.reservation_type == "out"
            and line.state not in ["draft", "cancel"]
        )

        room_revenue = sum(
            line.price_day_total
            for line in reservation_lines
            if line.reservation_id.reservation_type == "normal"
            and line.state not in ["draft", "cancel"]
        )

        pax = sum(
            (line.reservation_id.adults or 0) + (line.reservation_id.children or 0)
            for line in reservation_lines
            if line.reservation_id.reservation_type in ["normal", "staff"]
            and line.state not in ["draft", "cancel"]
        )

        avalaible_rooms = total_rooms - occupied_rooms - blocked_rooms

        last_updated = fields.Datetime.now()

        return {
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_rooms,
            "blocked_rooms": blocked_rooms,
            "available_rooms": avalaible_rooms,
            "pax": pax,
            "available_rate": (avalaible_rooms / total_rooms),
            "occupancy_rate": (occupied_rooms / total_rooms) if total_rooms else 0,
            "block_rate": (blocked_rooms / total_rooms) if total_rooms else 0,
            "room_revenue": room_revenue,
            "adr": (room_revenue / occupied_rooms) if occupied_rooms else 0,
            "revpar": (room_revenue / total_rooms) if total_rooms else 0,
            "last_updated": last_updated,
        }
