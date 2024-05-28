# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import re
from odoo.exceptions import ValidationError


class BankBranch(models.Model):
    _name = 'bank.branch'
    _description = 'branch model'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Branch Name", tracking=1, required=True)
    address = fields.Char(string="Branch Address", tracking=2, required=True)
    phone_no = fields.Char(string="Branch Phone", tracking=3, required=True)
    bank_id = fields.Many2one("bank.bank", string="Bank", tracking=4, required=True)
    city = fields.Char(string="City", tracking=True, required=True)
    branch_code = fields.Char(string="Branch Code")

    @api.model
    def create(self, vals):
        phone_no_pattern = r"^(\+92|0|92)[0-9]{10}$"
        if not (re.match(phone_no_pattern, vals['phone_no'])):
            raise ValidationError(_("Entered phone number is not acceptable"))
            return
        vals['branch_code'] = self.env['ir.sequence'].next_by_code('bank.branch')
        print(vals['branch_code'])
        res = super(BankBranch, self).create(vals)
        return res
