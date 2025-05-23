# Copyright 2019 2023 Pablo Quesada, Jose Luis Algara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import ftplib
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    # Fields declaration
    data_bi_days = fields.Integer(
        string="Days to download data", required=False, default=60
    )
    url_ftp_bi = fields.Char("Server FTP DataBi", required=False)
    user_ftp_bi = fields.Char("User FTP DataBi", required=False)
    pass_ftp_bi = fields.Char("Password FTP DataBi", required=False)
    valid_ftp_bi = fields.Boolean("Valid FTP DataBi", default=False)
    maestro_ftp_bi = fields.Char("Maestro name FTP DataBi")

    def ftp_bi_test(self):
        _logger.info("Try FPT conection")
        notification = {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": ("Error"),
                "message": "The connection has not been possible. Check the parameters.",
                "type": "danger",
                "sticky": True,
            },
        }
        try:
            with ftplib.FTP(
                host=self.url_ftp_bi, user=self.user_ftp_bi, passwd=self.pass_ftp_bi
            ) as ftp:
                if ftp.getwelcome() is None:
                    self.valid_ftp_bi = False
                else:
                    notification["params"]["title"] = "TFP OK"
                    notification["params"]["message"] = ftp.getwelcome()
                    notification["params"]["type"] = "success"
                    self.valid_ftp_bi = True
        except ftplib.all_errors as e:
            _logger.error("%s" % e)
            notification["params"]["message"] = "%s" % e
            self.valid_ftp_bi = False
        return notification
