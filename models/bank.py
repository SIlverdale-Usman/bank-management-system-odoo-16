# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import re
from odoo.exceptions import ValidationError


class Bank(models.Model):
    _name = 'bank.bank'
    _description = 'bank model'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string=" Bank Name", tracking=1, required=True, )
    email = fields.Char(string="Bank email", tracking=2, required=True, )
    phone_no = fields.Char(string="Phone", tracking=3, required=True, )
    website = fields.Char(string="Bank's Website", tracking=4)
    branch_ids = fields.One2many("bank.branch", "bank_id", string="Branches")
    branch_count = fields.Integer(string="No Of Branches", compute='_compute_branch_count', store=True)
    bank_acronym = fields.Char(string="Bank Acronym", tracking=True, required=True)

    _sql_constraints = [
        (
            'bank_acronym_len_check',
            'check (LENGTH(bank_acronym) = 3)',
            'Bank Acronym should be 3 symbols'
        ),
    ]

    @api.depends('branch_ids')
    def _compute_branch_count(self):
        for rec in self:
            rec.branch_count = self.env['bank.branch'].search_count([('bank_id', '=', rec.id)])

    @api.model
    def create(self, vals):
        email_pattern = r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
        phone_no_pattern = r"^(\+92|0|92)[0-9]{10}$"
        print(re.match(email_pattern, vals['email']))
        print(re.match(phone_no_pattern, vals['phone_no']))
        if not (re.match(email_pattern, vals['email']) and re.match(phone_no_pattern, vals['phone_no'])):
            raise ValidationError(_("Entered email or phone number is not acceptable"))
            return
        res = super(Bank, self).create(vals)
        return res
