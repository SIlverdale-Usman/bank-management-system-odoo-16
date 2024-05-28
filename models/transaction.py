# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError


class BankTransaction(models.Model):
    _name = 'bank.transaction'
    _description = 'Transaction model'
    _rec_name = "title"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    title = fields.Char(string="Description", required=True, tracking=1)
    date = fields.Date(string="Date", tracking=2)

    account_id = fields.Many2one("bank.account", string="Account No.", tracking=4)
    account_title = fields.Char(related="account_id.title")

    transaction_type = fields.Selection(
        [('withdrawal', 'Withdrawal'), ('deposit', 'Deposit'), ('bill_payment', 'Bill Payment'),
         ('bank_transfer', 'Bank Transfer')],
        string='Transaction Type', tracking=3, required=True)
    transaction_method = fields.Selection([('card', 'Card'), ('cheque', 'Cheque'), ('cash', 'Cash')],
                                          string='Transaction Method', tracking=5)

    transaction_no = fields.Char(string="Transaction No")

    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)

    balance = fields.Float(related="account_id.balance", string="Account Balance")
    amount = fields.Integer(string="Amount")

    cheque_no = fields.Char(string="Cheque Number", tracking=True)
    card_number = fields.Char(string="Card Number", tracking=True)

    customer_id = fields.Many2one(related="account_id.customer_id", string="Related Customer", store=True)
    branch_id = fields.Many2one(related="account_id.branch_id", string="Account Branch", store=True)
    bank_id = fields.Many2one(related="branch_id.bank_id", string="Related Bank", store=True)

    payment_account_id = fields.Many2one("bank.account", string="To Account No.", tracking=True)

    def _match_card(self, card_no, account_id, amount):
        card_data = self.env['bank.card'].search([('card_number', '=', card_no), ('account_id', '=', account_id)])
        if not card_data:
            raise ValidationError(_("Mismatched account and card"))
            return
        elif card_data.state == 'block':
            raise ValidationError(_("Card is blocked, transaction is not possible"))
            return
        elif card_data and amount < card_data.card_limit:
            return card_data
        elif amount > card_data.card_limit:
            raise ValidationError(_("Withdrawal amount exceeds card limit: %.2f" % card_data.card_limit))
            return

    def _check_balance(self, amount, account_id):
        if amount > account_id.balance:
            raise ValidationError(_("Insufficient balance"))
        return True

    def _deposit(self, amount, account_id):
        account = self.env['bank.account'].browse(account_id)

        if account:
            update_balance = account.balance + amount
            account.write({'balance': update_balance})
            return True
        raise ValidationError(_("Account not found"))

    def _withdraw(self, amount, method, account_id, card_no=None):

        account = self.env['bank.account'].browse(account_id)

        if method == 'cheque':
            self._check_balance(amount, account)

        elif method == 'card':
            matched = self._match_card(card_no, account_id, amount)
            if matched:
                self._check_balance(amount, account)

        if account:
            update_balance = account.balance - amount
            account.write({'balance': update_balance})
            return True
        raise ValidationError(_("Account not found"))

    def _bill_payment(self, method, amount, payment_account_id, account_id=None):
        if method == 'cash':
            self._deposit(amount, payment_account_id)

    def _bank_to_bank_transfer(self, amount, account_id, payment_account_id):

        self._withdraw(amount, 'cheque', account_id)
        self._deposit(amount, payment_account_id)

    @api.model
    def create(self, vals):
        if vals['transaction_method'] == 'card' and vals['transaction_type'] == 'deposit':
            raise ValidationError(_("Cannot deposit from card"))

        gen_transaction_no = self.env['ir.sequence'].next_by_code('bank.transaction')
        vals['transaction_no'] = gen_transaction_no
        vals['date'] = date.today()

        if vals['transaction_type'] == 'deposit':
            self._deposit(vals['amount'], vals['account_id'])

        elif vals['transaction_type'] == 'withdrawal':
            if vals['transaction_method'] == 'card':
                self._withdraw(vals['amount'], 'card', vals['account_id'], vals['card_number'])
            elif vals['transaction_method'] == 'cheque':
                self._withdraw(vals['amount'], 'cheque', vals['account_id'])

        elif vals['transaction_type'] == 'bill_payment' and vals['transaction_method'] == 'cash':
            self._bill_payment("cash", vals['amount'], vals['account_id'])

        elif vals['transaction_type'] == 'bill_payment' or vals['transaction_type'] != 'bank_transfer':
            self._bank_to_bank_transfer(vals['amount'], vals['account_id'], vals['payment_account_id'])

        elif vals['transaction_type'] == 'bank_transfer':
            self._bank_to_bank_transfer(vals['amount'], vals['account_id'], vals['payment_account_id'], )

        return super(BankTransaction, self).create(vals)
