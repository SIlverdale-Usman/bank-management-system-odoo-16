from odoo import models, fields


class BankAssistant(models.TransientModel):
    _name = 'bank.assistant'
    _description = 'Bank AI Assistant'

    question = fields.Text(string='Question', required=True)
    answer = fields.Text(string='Answer', required=True)
