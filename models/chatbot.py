from odoo import models, fields

import google.generativeai as genai
from md2gemini import md2gemini

genai.configure(api_key="AIzaSyDPB7mgtFvpzMHKFjWMv14xiN-VvyxMBv0")
model = genai.GenerativeModel('gemini-pro')


class BankAssistant(models.TransientModel):
    _name = 'bank.assistant'
    _description = 'Bank AI Assistant'

    question = fields.Text(string='Question', required=True)
    answer = fields.Text(string='Answer', required=True)

    def generate_answer(self, query):
        {'role': 'You are customer service representative for a bank',
         'parts': query}

        response = model.generate_content(query)
        return md2gemini(response.text)
