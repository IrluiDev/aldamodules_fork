from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    image1 = fields.Char(string="Image City", attachment=True, store=True)
    image2 = fields.Char(string="Image Property", attachment=True, store=True)
    text_image1 = fields.Html(
        string="Text Image City",
    )
    text_image2 = fields.Html(string="Text Image Property")
    web_city_information_url = fields.Html(string="Web City Info URL")
    quiz_url = fields.Char(string="Quiz URL")
    is_exit_auto_mail = fields.Boolean(string="Auto send mail")
    property_service_information = fields.Html(string="About Alda Services")
    property_web_url = fields.Char(string="Link to Alda property information")
