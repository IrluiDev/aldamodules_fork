import logging
from datetime import datetime

from odoo.http import request

from odoo.addons.alda_helpdesk_pms.controllers.main import HelpdeskFormController

_logger = logging.getLogger(__name__)


class HelpdeskPriorityController(HelpdeskFormController):
    def _prepare_ticket_vals(self, post):
        vals = super(HelpdeskPriorityController, self)._prepare_ticket_vals(post)

        team_id = post.get("team_id")
        if team_id:
            team = request.env["helpdesk.team"].sudo().browse(int(team_id))
            _logger.info("Equipo encontrado: %s", team.name)
            if team.is_location_required:
                if "priority" in vals:
                    del vals["priority"]

                if "priority_disabled" in post:
                    _logger.info("Se encontró priority_disabled en el POST, ignorando")

                room_id = post.get("room_ids", "")
                pms_property = post.get("property_id", "")
                is_property_operated_normaly = (
                    post.get("is_property_operated_normaly") == "on"
                )
                pms_room_id = int(room_id) if room_id else False
                pms_property_id = int(pms_property) if pms_property else False
                date = datetime.now()

                is_room_operated_normaly = True
                if pms_room_id:
                    room = request.env["pms.room"].browse(pms_room_id)
                    is_room_operated_normaly = (
                        not request.env["helpdesk.ticket"].sudo()._is_room_blocked(room)
                    )

                result = (
                    request.env["helpdesk.ticket"]
                    .sudo()
                    ._get_priority_estimated(
                        pms_property_id,
                        pms_room_id,
                        date,
                        is_room_operated_normaly,
                        is_property_operated_normaly,
                    )
                )

                _logger.info("Resultado de prioridad: %s", result)

                if result:
                    priority_rule_id = result[0] if result else "0"
                    priority_estimated = result[1] if result else "0"
                    is_room_operated_normaly = (
                        result[3] if result else is_room_operated_normaly
                    )
                    is_property_operated_normaly = (
                        result[4] if result else is_property_operated_normaly
                    )

                    vals.update(
                        {
                            "priority_rule_id": priority_rule_id,
                            "priority": priority_estimated,
                            "is_room_operated_normaly": is_room_operated_normaly,
                            "is_property_operated_normaly": is_property_operated_normaly,
                        }
                    )
        else:
            _logger.warning("No se encontró team_id en el formulario")

        return vals
