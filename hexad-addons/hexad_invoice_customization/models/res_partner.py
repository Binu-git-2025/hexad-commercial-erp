from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    tds_applicable = fields.Boolean("Is TDS Applicable?", default=False, tracking=True)
    tds_percent = fields.Float("TDS %", default=0.0, tracking=True)