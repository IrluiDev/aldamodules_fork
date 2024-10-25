##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018-2024 Jose Luis Algara Toledo <osotranquilo@gmail.com>
#                  2024 Irlui Ramírez <irlui@aldahotels.com>
#                  Consultores hoteleros integrales - Alda Hotels
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime, timedelta

from odoo import _, fields, models


class InheritPmsReservation(models.Model):
    _inherit = "pms.reservation"

    door_codes = fields.Html("Entry Codes", compute="_compute_door_codes")
    box_number = fields.Integer("Box number")
    box_code = fields.Char("Box code")

    def doorcode4(self, date, pms_property_id=False):
        # Calculate de Door Code...
        if not pms_property_id:
            pms_property_id = self.pms_property_id
        delay = pms_property_id.seed_code * 100
        if pms_property_id.code_period == "7":
            weekday = date.weekday()
            date = date - timedelta(days=weekday)
        date = datetime(
            year=date.year,
            month=date.month,
            day=date.day,
        )
        code = float(date.strftime("%s.%%06d") % date.microsecond) + delay
        return (
            (pms_property_id.chararters_precode or "")
            + repr(code)[4:8]
            + (pms_property_id.chararters_postcode or "")
        )

    def door_codes_text(self, entry, exit_info, pms_property_id=False):
        if not pms_property_id:
            pms_property_id = self.pms_property_id
        codes = "No data"
        if pms_property_id.code_period == "7":
            if entry.weekday() == 0:
                entry = entry + timedelta(days=1)
            if exit_info.weekday() == 0:
                exit_info = exit_info - timedelta(days=1)
            codes = (
                _("Entry code: ")
                + '<strong><span style="font-size: 1.4em;">'
                + self.doorcode4(entry, pms_property_id)
                + "</span></strong>"
            )
            while entry <= exit_info:
                if entry.weekday() == 0:
                    codes += (
                        "<br>"
                        + _("It will change on monday ")
                        + datetime.strftime(entry, "%d-%m-%Y")
                        + _(" to:")
                        + ' <strong><span style="font-size: 1.4em;">'
                        + self.doorcode4(entry, pms_property_id)
                        + "</span></strong>"
                    )
                entry = entry + timedelta(days=1)
        else:
            codes = (
                _("Entry code: ")
                + '<strong><span style="font-size: 1.4em;">'
                + self.doorcode4(entry, pms_property_id)
                + "</span></strong>"
            )
            entry = entry + timedelta(days=1)
            while entry < exit_info:
                codes += (
                    "<br>"
                    + _("It will change on ")
                    + datetime.strftime(entry, "%d-%m-%Y")
                    + _(" to:")
                    + ' <strong><span style="font-size: 1.4em;">'
                    + self.doorcode4(entry, pms_property_id)
                    + "</span></strong>"
                )
                entry = entry + timedelta(days=1)
        return codes

    def _compute_door_codes(self):
        for record in self:
            record.door_codes = self.door_codes_text(record.checkin, record.checkout)
