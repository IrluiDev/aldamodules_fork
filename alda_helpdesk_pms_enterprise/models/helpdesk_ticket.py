import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HelpdeskPmsEnterprise(models.Model):
    _inherit = "helpdesk.ticket"

    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        store=True,
        tracking=True,
        domain=lambda self: [("id", "in", self._get_allowed_property_ids())],
        help="The hotel associated with this ticket.",
    )

    pms_room_id = fields.Many2one(
        comodel_name="pms.room",
        string="Room",
        domain="[('pms_property_id', '=', pms_property_id)]",
        tracking=True,
        help="The room associated with this ticket. It must belong to the selected property.",
    )

    @api.model
    def _get_allowed_property_ids(self):
        employee = (
            self.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", self.env.user.id)], limit=1)
        )
        return employee.property_ids.ids if employee else []

    @api.onchange("pms_property_id")
    def _onchange_pms_property(self):
        employee = (
            self.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", self.env.user.id)], limit=1)
        )
        property_domain = (
            [("id", "in", employee.property_ids.ids)]
            if employee
            else [("id", "=", False)]
        )

        room_domain = [("pms_property_id", "=", self.pms_property_id.id)]

        if (
            self.pms_room_id
            and self.pms_room_id.pms_property_id != self.pms_property_id
        ):
            self.pms_room_id = False

        if self._origin and self._origin.id:
            old_property = self._origin.pms_property_id
            new_property = self.pms_property_id

            if (
                old_property
                and old_property.partner_id
                and old_property != new_property
            ):
                try:
                    self.message_unsubscribe(partner_ids=old_property.partner_id.ids)
                except Exception:
                    _logger.warning(
                        "Unsuscribe property was not posible %s for ticket %s from onchange",
                        old_property.partner_id.id,
                        self._origin.id,
                    )

            if (
                new_property
                and new_property.partner_id
                and old_property != new_property
            ):
                try:
                    self.message_subscribe(partner_ids=new_property.partner_id.ids)
                except Exception:
                    _logger.warning(
                        "Subscribe property was not posible %s for ticket %s from onchange",
                        new_property.partner_id.id,
                        self._origin.id,
                    )

        return {
            "domain": {
                "pms_property_id": property_domain,
                "pms_room_id": room_domain,
            }
        }

    @api.constrains("pms_property_id", "pms_room_id")
    def _check_property_assignment(self):
        for ticket in self:
            if ticket.pms_property_id:
                employee = (
                    self.env["hr.employee"]
                    .sudo()
                    .search([("user_id", "=", ticket.env.uid)], limit=1)
                )
                if employee and ticket.pms_property_id not in employee.property_ids:
                    raise ValidationError(
                        _("You do not have permission to assign this property.")
                    )
            if (
                ticket.pms_room_id
                and ticket.pms_room_id.pms_property_id != ticket.pms_property_id
            ):
                raise ValidationError(
                    _("The selected room does not belong to the specified hotel.")
                )

            if ticket.pms_room_id and not ticket.pms_property_id:
                raise ValidationError(
                    _("You must select a hotel before assigning a room.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super().create(vals_list)
        for ticket in tickets:
            res_partner = getattr(ticket.pms_property_id, "partner_id", False)
            if res_partner:
                try:
                    ticket.message_subscribe(partner_ids=res_partner.ids)
                    _logger.info(
                        "Hotel partner %s suscrito automáticamente al ticket %s",
                        res_partner.id,
                        ticket.id,
                    )
                except Exception as e:
                    _logger.error(
                        "Error al suscribir el hotel %s al ticket %s: %s",
                        res_partner.id,
                        ticket.id,
                        e,
                    )
        return tickets

    def write(self, vals):
        res = super().write(vals)
        for ticket in self:
            res_partner = getattr(ticket.pms_property_id, "partner_id", False)
            if res_partner:
                try:
                    ticket.message_subscribe(partner_ids=res_partner.id)
                    _logger.info(
                        "Hotel partner %s sigue suscrito al ticket %s",
                        res_partner.id,
                        ticket.id,
                    )
                except Exception as e:
                    _logger.error(
                        "Error al actualizar la suscripción del hotel %s en ticket %s: %s",
                        res_partner.id,
                        ticket.id,
                        e,
                    )
        return res

    def _unsubscribe_portal_users(self):
        super()._unsubscribe_portal_users()
        for ticket in self:
            res_partner = getattr(ticket.pms_property_id, "partner_id", False)
            if res_partner:
                try:
                    ticket.message_unsubscribe(partner_ids=res_partner.id)
                    _logger.info(
                        "Hotel partner %s desuscrito automáticamente del ticket %s",
                        res_partner.id,
                        ticket.id,
                    )
                except Exception as e:
                    _logger.error(
                        "Error al desuscribir el hotel %s del ticket %s: %s",
                        res_partner.id,
                        ticket.id,
                        e,
                    )
