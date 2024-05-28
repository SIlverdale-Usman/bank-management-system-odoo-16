# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class BankEmployee(models.Model):
    _inherit = "hr.employee"

    branch_id = fields.Many2one("bank.branch", string="Branch", tracking=True, required=True)
    bank_id = fields.Many2one("bank.bank", string="Bank", tracking=True, required=True)
    branch_city = fields.Char(related="branch_id.city", string="Branch City")
