from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta


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
    paid_date = fields.Date(string="Paid Date")
    total_paid = fields.Float(string='Total Paid', compute='_compute_total_paid', store=True)
    remaining_amount = fields.Float(string='Remaining Amount', compute='_compute_remaining_amount', store=True)
    loan_payment_ids = fields.One2many('bank.loan.payment', 'loan_account_id', string='Loan Payments')

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

    @api.depends('loan_amount', 'loan_payment_ids.amount')
    def _compute_total_paid(self):
        for loan in self:
            total_paid = sum(payment.amount for payment in loan.loan_payment_ids)
            loan.total_paid = total_paid

    @api.depends('loan_amount', 'total_paid')
    def _compute_remaining_amount(self):
        for loan in self:
            loan.remaining_amount = loan.loan_amount - loan.total_paid

    def check_if_loan_paid(self):
        for loan in self:
            if loan.state == 'approved' and loan.total_paid >= loan.loan_amount:
                loan.state = 'paid'
                loan.paid_date = date.today()

    def action_approved(self):
        template = self.env.ref("bank.loan_request_mail_template")
        for rec in self:
            if rec.state == "draft":
                template.send_mail(rec.id, force_send=True)
                rec.state = 'approved'

    def action_paid(self):
        template = self.env.ref("bank.loan_request_accept_mail_template")
        for rec in self:
            if rec.state == "approved":
                template.send_mail(rec.id, force_send=True)
                rec.paid_date = date.today()
                rec.state = 'paid'
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Loan Paid',
                'type': 'rainbow_man',
            }
        }

    def action_reject(self):
        template = self.env.ref("bank.loan_request_cancel_mail_template")

        for rec in self:
            if rec.state == "draft" or rec.state == "approved":
                template.send_mail(rec.id, force_send=True)
                rec.state = 'cancelled'

    @api.model
    def send_loan_payment_reminder(self):
        today = date.today()
        overdue_loans = self.search([
            ('state', '=', 'approved'),
            ('loan_payment_ids.payment_date', '<', today - timedelta(days=30))
        ])
        print("hello")
        template = self.env.ref('bank.loan_payment_reminder_mail_template')
        for loan in overdue_loans:
            template.send_mail(loan.id, force_send=True)


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
        record.loan_account_id.check_if_loan_paid()
        return record
