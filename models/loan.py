from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LoanType(models.Model):
    _name = 'bank.loan.type'
    _description = 'Bank Loan Type'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Loan Type Name', required=True, tracking=1)
    description = fields.Text(string='Description')
    interest_rate = fields.Float(string='Interest Rate (%)', required=True, tracking=2)
    term_years = fields.Integer(string='Term (Years)', required=True, tracking=3)
    prefix = fields.Char(string='Prefix', required=True, tracking=True)
    bank_id = fields.Many2one("bank.bank", string="Bank", tracking=4, required=True)

    @api.model
    def create(self, vals):
        if vals.get('prefix'):
            sequence = self.env['ir.sequence'].create({
                'name': 'Bank Loan Type Sequence',
                'padding': 4,
                'prefix': vals['prefix'],
                'code': 'bank.loan.type.' + vals['prefix'],
            })
            print(sequence)

        result = super(LoanType, self).create(vals)
        return result


class LoanAccount(models.Model):
    _name = 'bank.loan.account'
    _description = 'Bank Loan Account'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Loan Reference', copy=False, readonly=True, default=lambda self: _('New'))
    account_id = fields.Many2one('bank.account', string='Related Account', required=True)
    loan_type_id = fields.Many2one('bank.loan.type', string='Loan Type', required=True)
    loan_amount = fields.Integer(string='Loan Amount', required=True)
    interest_rate = fields.Float(string='Interest Rate (%)', related='loan_type_id.interest_rate', store=True,
                                 readonly=True)
    term_years = fields.Integer(string='Term (Years)', related='loan_type_id.term_years', store=True, readonly=True)
    monthly_payment = fields.Float(string='Monthly Payment', compute='_compute_monthly_payment', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ], string='Status', readonly=True, copy=False, tracking=True, default='draft')
    bank_id = fields.Many2one("bank.bank", string="Bank", tracking=4, required=True)
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)

    @api.model
    def create(self, vals):
        seq = self.env['bank.loan.type'].browse(vals['loan_type_id'])
        get_code = 'bank.loan.type.' + seq.prefix
        vals['name'] = self.env['ir.sequence'].next_by_code(get_code)
        result = super(LoanAccount, self).create(vals)
        return result

    @api.depends('loan_amount', 'interest_rate', 'term_years')
    def _compute_monthly_payment(self):
        for loan in self:
            if loan.loan_amount and loan.interest_rate and loan.term_years:
                L = loan.loan_amount
                c = loan.interest_rate / 100 / 12
                n = loan.term_years * 12
                if c == 0:
                    loan.monthly_payment = L / n
                else:
                    loan.monthly_payment = L * c * (1 + c) ** n / ((1 + c) ** n - 1)
            else:
                loan.monthly_payment = 0

    def action_approved(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = 'approved'

    def action_paid(self):
        for rec in self:
            if rec.state == "approved":
                rec.state = 'paid'
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Loan Paid',
                'type': 'rainbow_man',
            }
        }

    def action_reject(self):
        for rec in self:
            if rec.state == "draft" or rec.state == "approved":
                rec.state = 'cancelled'


class LoanPayment(models.Model):
    _name = 'bank.loan.payment'
    _description = 'Bank Loan Payment'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    account_id = fields.Many2one('bank.account', string='Related Account', required=True)
    loan_account_id = fields.Many2one('bank.loan.account', string='Loan Account', required=True)
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.context_today)
    amount = fields.Float(string='Payment Amount', required=True)

    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)

    loan_paid = fields.Float(string="Loan Paid", compute='_compute_loan_paid', store=True, tracking=True)
    remaining_amount = fields.Float(string="Remaining Amount", compute='_compute_remaining_amount', store=True,
                                    tracking=True)

    @api.constrains('amount')
    def _check_payment_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_("The payment amount must be positive."))

    @api.depends('loan_account_id')
    def _compute_loan_paid(self):
        for record in self:
            loan_payments = self.search([('loan_account_id', '=', record.loan_account_id.id)])
            record.loan_paid = sum(payment.amount for payment in loan_payments)

    @api.depends('loan_account_id', 'loan_paid')
    def _compute_remaining_amount(self):
        for record in self:
            if record.loan_account_id:
                record.remaining_amount = record.loan_account_id.loan_amount - record.loan_paid

    @api.model
    def create(self, vals):
        record = super(LoanPayment, self).create(vals)
        record._compute_loan_paid()
        record._compute_remaining_amount()
        return record
