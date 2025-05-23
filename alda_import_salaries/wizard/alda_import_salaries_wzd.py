# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
from datetime import datetime

import xlrd

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError


class AldaImportSalariesWzd(models.TransientModel):
    _name = "alda.import.salaries.wzd"
    _description = "Custom import of salaries"

    def _get_default_journal(self):
        return (
            self.env["account.journal"].search([("type", "=", "general")], limit=1).id
        )

    journal_id = fields.Many2one(
        "account.journal",
        "Journal",
        required=True,
        domain=[("type", "=", "general")],
        default=_get_default_journal,
    )

    xlsx_file = fields.Binary(
        "File to import (*.xslx, *.xls)", required=True, attachment=False
    )
    filename = fields.Char()

    def action_file_import(self):
        if not self.xlsx_file or not self.filename.lower().endswith(
            (
                ".xls",
                ".xlsx",
            )
        ):
            raise ValidationError(_("Please Select an .xls or .xlsx file"))

        decoded_data = base64.decodebytes(self.xlsx_file)
        book = xlrd.open_workbook(file_contents=decoded_data)
        account_pool = self.env["account.account"]
        property_pool = self.env["pms.property"]
        sheet = book.sheet_by_index(0)
        last_move_name = False
        move_lines = []
        move_date = False
        moves_to_create = []
        newmove_vals = {}
        tax_template = self.env.ref("l10n_es.account_tax_template_p_irpf21t")
        tax = self.journal_id.company_id.get_taxes_from_templates(tax_template)
        for rownum in range(sheet.nrows):
            row = sheet.row_values(rownum)
            if not move_date:
                move_date = datetime(*xlrd.xldate_as_tuple(row[1], book.datemode))

            if last_move_name != row[0]:
                if last_move_name:
                    newmove_vals["line_ids"] = move_lines
                    moves_to_create.append(newmove_vals)
                    move_lines = []

                newmove_vals = {
                    "move_type": "entry",
                    "date": move_date,
                    "journal_id": self.journal_id.id,
                }
                last_move_name = row[0]
            if type(row[2]) == float:
                row[2] = str(int(row[2]))
            account = account_pool.search([("code", "=", row[2])])
            if not account:
                raise UserError(_("Any account with %s code") % row[2])
            pms_property = property_pool.search([("pms_property_code", "=", row[8])])
            if not pms_property:
                raise UserError(_("Any property with code %s") % row[8])

            move_lines.append(
                (
                    0,
                    0,
                    {
                        "account_id": account.id,
                        "name": row[4],
                        "debit": row[5] or 0.0,
                        "credit": row[6] or 0.0,
                        "tax_ids": row[2][:3] == "640" and [(6, 0, [tax.id])] or False,
                        "tax_repartition_line_id": row[2][:3] == "475"
                        and tax.invoice_repartition_line_ids.filtered(
                            lambda x: x.repartition_type == "tax"
                        ).id
                        or False,
                        "pms_property_id": pms_property.id,
                        "analytic_distribution": row[2][:1] == "6"
                        and {pms_property.analytic_account_id.id: 100}
                        or False,
                    },
                )
            )

            if rownum == sheet.nrows - 1:
                newmove_vals["line_ids"] = move_lines
                moves_to_create.append(newmove_vals)

        if moves_to_create:
            moves = (
                self.env["account.move"]
                .with_context(skip_invoice_sync=True)
                .create(moves_to_create)
            )
            result = self.env["ir.actions.act_window"]._for_xml_id(
                "account.action_move_journal_line"
            )
            result["domain"] = [("id", "in", moves.ids)]
            result["context"] = {"create": False}

            return result
