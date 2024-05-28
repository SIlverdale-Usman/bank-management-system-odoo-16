# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import re
from odoo.exceptions import ValidationError
from datetime import date


class BankCustomer(models.Model):
    _name = 'bank.customer'
    _description = 'customer model'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Customer Name", tracking=1, required=True)
    address = fields.Char(string="Customer Address", tracking=2, required=True)
    phone_no = fields.Char(string="Customer Phone", tracking=3, required=True)
    image = fields.Image(string="Profile Image", tracking=True)
    age = fields.Integer(string='Customer Age', compute="_compute_age", store=True, tracking=True)

    account_ids = fields.One2many("bank.account", "customer_id", string="Accounts")
    account_count=fields.Integer(string="Accounts", compute='_compute_account_count')

    email = fields.Char(string="Customer E-mail", tracking=5, required=True)
    date_of_birth = fields.Date(string="Date Of Birth", tracking=6)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender', tracking=True)

    @api.model
    def create(self, vals):
        email_pattern = r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
        phone_no_pattern = r"^(\+92|0|92)[0-9]{10}$"

        if not (re.match(email_pattern, vals['email']) and re.match(phone_no_pattern, vals['phone_no'])):
            raise ValidationError(_("Entered email or phone number is not acceptable"))
            return
        res = super(BankCustomer, self).create(vals)
        return res

    @api.constrains('date_of_birth')
    def check_date_of_birth(self):
        for rec in self:
            if rec.date_of_birth and rec.date_of_birth >= fields.Date.today():
                raise ValidationError(_("Entered date of birth is not acceptable"))

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            today = date.today()
            if rec.date_of_birth:
                rec.age = today.year - rec.date_of_birth.year
            else:
                rec.age = 0

    @api.depends('account_ids')
    def _compute_account_count(self):
        for rec in self:
            rec.account_count = self.env['bank.account'].search_count([('customer_id', '=', rec.id)])
