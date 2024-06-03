# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BankAccount(models.Model):
    _name = 'bank.account'
    _description = 'account model'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    title = fields.Char(related="customer_id.name", string="Account Title")
    account_type = fields.Selection(
        [('current', 'Current'), ('savings', 'Savings'), ('student', 'Student')], string='Account Type',
        tracking=1, default="current", required=True)
    account_number = fields.Char(string="Account Number", index=True)

    customer_id = fields.Many2one("bank.customer", string="Account Holder", tracking=2,
                                  required=True)
    branch_id = fields.Many2one("bank.branch", string="Branch", tracking=3, required=True)
    bank_id = fields.Many2one("bank.bank", string="Bank", tracking=4, required=True)

    opening_date = fields.Date(string="Account Opening Date", tracking=5, required=True)

    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)

    balance = fields.Float(string="Account Balance", tracking=True, required=True, default=0.00)

    card_ids = fields.One2many("bank.card", "account_id", string="Cards")
    card_count = fields.Integer(string="Card Count", compute='_compute_card_count', store=True)

    transaction_ids = fields.One2many("bank.transaction", "account_id", string="Transactions")

    @api.depends('card_ids')
    def _compute_card_count(self):
        card_group = self.env['bank.card'].read_group(domain=[],
                                                      fields=['account_id'],
                                                      groupby=['account_id'])
        for card in card_group:
            account_id = card.get('account_id')[0]
            account_rec = self.browse(account_id)
            account_rec.card_count = card['account_id_count']
            self -= account_rec
        self.card_count = 0

    @api.constrains('balance')
    def check_account_limit(self):
        for rec in self:
            if rec.account_type == 'student':
                if rec.balance > 50000:
                    raise ValidationError(_("Account limit reached"))

    @api.model
    def create(self, vals):
        acc_no = self.env['ir.sequence'].next_by_code('bank.account')
        branch = self.env['bank.branch'].browse(vals['branch_id'])
        vals['account_number'] = branch.branch_code + acc_no
        return super(BankAccount, self).create(vals)

    def name_get(self):
        return [(record.id, "%s, %s" % (record.account_number, record.title)) for record in self]

    def action_view_customer(self):
        print("customer action")
        print(self.id)
        return {
            'name': _('Account Holder'),
            'type': 'ir.actions.act_window',
            'res_model': 'bank.customer',
            'view_mode': 'tree,form',
            'domain': [("account_ids", "=", self.id)],
            'target': 'current'
        }

    def action_view_card(self):
        print("card action")
        return {
            'name': _('Related Card'),
            'type': 'ir.actions.act_window',
            'res_model': 'bank.card',
            'view_mode': 'tree,form',
            'domain': [("account_id", "=", self.id)],
            'target': 'current'
        }


class PartnerXlsx(models.AbstractModel):
    _name = 'report.bank.customer_bank_statement_report_template_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, account):
        for rec in account:
            row = 1
            col = 0
            report_name = rec.title
            sheet = workbook.add_worksheet(report_name[:31])

            for transaction in rec.transaction_ids:
                # style

                sheet.set_column('A:A', 15)
                sheet.set_column('B:B', 20)
                sheet.set_column('C:D', 25)
                sheet.set_column('E:F', 20)

                date_format = workbook.add_format({'num_format': 'd mmmm yyyy', 'align': 'center'})
                heading_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': 'yellow'})
                data_format = workbook.add_format({'align': 'center'})
                # headings
                sheet.write(0, 0, "Transaction No", heading_format)
                sheet.write(0, 1, "Date", heading_format)
                sheet.write(0, 2, "Description", heading_format)
                sheet.write(0, 3, "Transaction Type", heading_format)
                sheet.write(0, 4, "Transaction Method", heading_format)
                sheet.write(0, 5, "Amount", heading_format)

                # data
                sheet.write(row, col, transaction.transaction_no, data_format)
                col += 1
                sheet.write(row, col, transaction.date, date_format)
                col += 1
                sheet.write(row, col, transaction.title, data_format)
                col += 1
                sheet.write(row, col, transaction.transaction_type, data_format)
                col += 1
                sheet.write(row, col, transaction.transaction_method, data_format)
                col += 1
                sheet.write(row, col, transaction.amount, data_format)

                row += 1
                col = 0
