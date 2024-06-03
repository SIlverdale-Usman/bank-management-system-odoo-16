# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import ccard
from datetime import date, timedelta
from odoo.exceptions import ValidationError


class BankCard(models.Model):
    _name = 'bank.card'
    _description = 'card model'
    _rec_name = "title"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    title = fields.Char(related="customer_id.name", string="Card Title", tracking=1, required=True)
    card_type = fields.Selection(
        [('master', 'MASTER'), ('visa', 'VISA')], string='Card Type',
        tracking=2, default="master", required=True)
    expiry_date = fields.Date(string="Expiry Date", tracking=4)

    account_id = fields.Many2one("bank.account", string="Related Account", required=True)

    card_number = fields.Char(string="Card Number")
    card_number_formatted = fields.Char(string="Formatted Card Number", compute="_compute_card_number_formatted")

    card_limit = fields.Float(string="Card Limit")

    customer_id = fields.Many2one(related="account_id.customer_id", string="Related Customer", store=True)
    branch_id = fields.Many2one(related="account_id.branch_id", string="Account Branch", store=True)
    bank_id = fields.Many2one(related="branch_id.bank_id", string="Related Bank", store=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('block', 'Blocked'),
    ], string='Status', copy=False, tracking=True, default='active')

    def _get_default_expiry_date(self):
        today = date.today()
        five_years_from_now = today + timedelta(days=365 * 5)
        return five_years_from_now

    @api.model
    def create(self, vals):
        print(vals)

        if vals['card_type'] == 'master':
            vals['card_number'] = ccard.mastercard()
            vals['card_limit'] = 50000
        elif vals['card_type'] == 'visa':
            vals['card_number'] = ccard.visa()
            vals['card_limit'] = 25000

        vals['expiry_date'] = self._get_default_expiry_date()
        res = super(BankCard, self).create(vals)

        print(vals)
        return res

    @api.depends('card_number')
    def _compute_card_number_formatted(self):
        for record in self:
            if record.card_number:
                # Format the card number with spaces
                formatted_number = ' '.join(
                    [record.card_number[i:i + 4] for i in range(0, len(record.card_number), 4)])
                record.card_number_formatted = formatted_number
            else:
                record.card_number_formatted = ' '

    def action_block(self):
        template = self.env.ref("bank.card_template_mail_template")

        for rec in self:
            if rec.state == "active":
                print(template)
                template.send_mail(rec.id, force_send=True)
                rec.state = 'block'
            else:
                raise ValidationError(_("Card already blocked"))
