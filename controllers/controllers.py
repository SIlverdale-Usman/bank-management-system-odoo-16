# -*- coding: utf-8 -*-
from odoo import http

import google.generativeai as genai
from md2gemini import md2gemini

genai.configure(api_key="AIzaSyDPB7mgtFvpzMHKFjWMv14xiN-VvyxMBv0")
model = genai.GenerativeModel('gemini-pro')


class Bank(http.Controller):
    @http.route('/bank/rpc-chatbot', type='json', auth='user')
    def generateResponse(self, **kw):
        query = kw.get('query')
        response = model.generate_content({'role': 'model',
                                           'parts': query})
        return md2gemini(response.text)
