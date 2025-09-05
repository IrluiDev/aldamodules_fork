import base64
import logging
from datetime import datetime

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.utils import ensure_db

_logger = logging.getLogger(__name__)


class HelpdeskFormController(http.Controller):
    @http.route("/helpdesk/ticket/new", type="http", auth="public", website=True)
    def helpdesk_ticket_form(self, **kwargs):
        ensure_db()
        if not (
            request.env.user.has_group("base.group_user")
            or request.env.user.has_group("base.group_portal")
        ):
            _logger.warning("Acceso denegado para usuario %s", request.env.user.name)
            return request.redirect("/web/login")

        user_id = request.env.user
        partner_id = request.env.user.partner_id
        property_id = int(kwargs.get("property_id", 0))

        pms_property_ids = request.env["pms.property"].sudo().browse(property_id)

        visibility_filter = []
        if user_id.has_group("base.group_portal"):
            visibility_filter = ["portal"]
        else:
            visibility_filter = ["portal", "internal", "public"]
        team_ids = (
            request.env["helpdesk.team"]
            .sudo()
            .search([("privacy_visibility", "in", visibility_filter)])
        )

        ticket_type_ids = (
            request.env["helpdesk.ticket.type"]
            .sudo()
            .search([("team_id", "in", team_ids.ids)])
        )
        is_overnight_room = (
            request.env["pms.room.type"]
            .sudo()
            .search([("overnight_room", "=", True)])
            .ids
        )
        room_ids = (
            request.env["pms.room"]
            .sudo()
            .search(
                [
                    ("pms_property_id", "=", pms_property_ids.id),
                    ("room_type_id", "in", is_overnight_room),
                    ("active", "=", True),
                ]
            )
        )

        location_type_options = request.env["helpdesk.ticket"]._get_location_selection()
        room_state_ids = {}
        for room in room_ids:
            room_state_ids[room.id] = (
                request.env["helpdesk.ticket"].sudo()._is_room_blocked(room)
            )

        company_external_id = False
        is_property_operated_normaly = True

        return request.render(
            "alda_helpdesk_pms.create_ticket_form",
            {
                "portal_user_id": user_id.id,
                "user_name": user_id.name,
                "team_ids": team_ids,
                "ticket_type_ids": ticket_type_ids,
                "partner_name": partner_id.company_name if partner_id else "",
                "partner_id": partner_id.id if partner_id else None,
                "property_id": pms_property_ids.id,
                "property_name": pms_property_ids.name,
                "room_ids": room_ids,
                "is_room": False,
                "location_type_options": location_type_options,
                "is_room_blocked_ids": room_state_ids,
                "company_external_id": company_external_id,
                "is_property_operated_normaly": is_property_operated_normaly,
            },
        )

    @http.route(
        "/helpdesk/ticket/submit",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=False,
    )
    def helpdesk_ticket_submit(self, **post):
        ensure_db()
        room_id = post.get("room_ids", "")
        pms_property = post.get("property_id", "")
        ticket_type_id = post.get("ticket_type_id", "")
        is_property_operated_normaly = post.get("is_property_operated_normaly") == "on"
        pms_room_id = int(room_id) if room_id else False
        pms_property_id = int(pms_property) if pms_property else False
        date = datetime.now()
        is_room_operated_normaly = True

        if pms_room_id:
            room = request.env["pms.room"].browse(pms_room_id)
            is_room_operated_normaly = (
                False
                if request.env["helpdesk.ticket"].sudo()._is_room_blocked(room)
                else True
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
        priority_rule_id = result[0] if result else "0"
        priority_estimated = result[1] if result else "0"
        is_room_operated_normaly = result[3] if result else is_room_operated_normaly
        is_property_operated_normaly = (
            result[4] if result else is_property_operated_normaly
        )

        ticket = (
            request.env["helpdesk.ticket"]
            .with_context(from_web_create=True)
            .sudo()
            .create(
                {
                    "name": post.get("subject"),
                    "partner_id": int(post.get("partner_id")),
                    "partner_name": post.get("partner_name"),
                    "pms_property_id": int(post.get("property_id")),
                    "team_id": int(post.get("team_id")),
                    "ticket_type_id": ticket_type_id,
                    "location_type": post.get("location_type"),
                    "pms_room_id": pms_room_id,
                    "company_external_id": post.get("company_external_id"),
                    "description": post.get("description"),
                    "priority_rule_id": priority_rule_id,
                    "priority": priority_estimated,
                    "is_property_operated_normaly": is_property_operated_normaly,
                    "is_room_operated_normaly": is_room_operated_normaly,
                }
            )
        )
        _logger.info(
            "Ticket creado: %s %s %s",
            ticket.id,
            ticket.is_property_operated_normaly,
            ticket.is_room_operated_normaly,
        )

        attachment = request.httprequest.files.get("attachment")
        if post.get("attachment", False):
            attachments = request.httprequest.files.getlist("attachment")
            attachment_ids = []

            for attachment in attachments:
                if attachment and attachment.filename:
                    try:
                        attachment_data = base64.b64encode(attachment.read()).decode(
                            "utf-8"
                        )
                        att = (
                            request.env["ir.attachment"]
                            .sudo()
                            .create(
                                {
                                    "name": attachment.filename,
                                    "type": "binary",
                                    "datas": attachment_data,
                                    "res_model": "helpdesk.ticket",
                                    "res_id": ticket.id,
                                    "public": True,
                                    "mimetype": attachment.content_type,
                                }
                            )
                        )
                        attachment_ids.append(att.id)
                    except Exception as e:
                        _logger.error("Upload file failed %s: %s", ticket.id, str(e))

            if attachment_ids:
                message_body = post.get("description", "")
                message = ticket.message_post(
                    body=message_body,
                    attachment_ids=attachment_ids,
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                )

        return request.redirect(f"/helpdesk/ticket/confirmation/{ticket.id}")

    @http.route(
        "/helpdesk/ticket/confirmation/<int:ticket_id>",
        type="http",
        auth="public",
        website=True,
    )
    def helpdesk_ticket_thankyou(self, ticket_id=None, **kwargs):
        values = {
            "ticket": None,
            "ticket_url": None,
        }
        if ticket_id:
            try:
                ticket = request.env["helpdesk.ticket"].sudo().browse(int(ticket_id))
                if ticket.exists():
                    ticket_url = f"/my/ticket/{ticket.id}/{ticket.access_token}"
                    values.update(
                        {
                            "ticket": ticket,
                            "ticket_url": ticket_url,
                        }
                    )
            except Exception as e:
                _logger.error("Error processing ticket confirmation: %s", str(e))

        return request.render("alda_helpdesk_pms.confirmation_ticket", values)
