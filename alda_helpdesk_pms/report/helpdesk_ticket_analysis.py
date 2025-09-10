from odoo import fields, models


class HelpdeskTicketReport(models.Model):
    _inherit = "helpdesk.ticket.report.analysis"

    pms_property_id = fields.Many2one("pms.property", string="Property", readonly=True)
    pms_room_id = fields.Many2one("pms.room", string="Room", readonly=True)
    reservation_id = fields.Char(string="Reservation Number", readonly=True)
    is_room_blocked = fields.Boolean(string="Blocked", readonly=True)
    blocked_room_status_label = fields.Char(string="Room state", readonly=True)
    blocked_room_count = fields.Integer(string="Count Rooms Blocked", readonly=True)

    def _select(self):
        select_str = super()._select()

        select_str += """,
            T.pms_property_id as pms_property_id,
            T.pms_room_id as pms_room_id,
            T.reservation_id as reservation_id,
            T.is_room_blocked as is_room_blocked,
            CASE
                WHEN T.is_room_blocked THEN 'Is Blocked'
                ELSE 'No Blocked'
            END as blocked_room_status_label,
            CASE WHEN T.is_room_blocked THEN 1 ELSE 0 END as blocked_room_count
        """
        return select_str
