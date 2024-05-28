# -*- coding: utf-8 -*-
# from odoo import http


# class Bank(http.Controller):
#     @http.route('/bank/bank', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bank/bank/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bank.listing', {
#             'root': '/bank/bank',
#             'objects': http.request.env['bank.bank'].search([]),
#         })

#     @http.route('/bank/bank/objects/<model("bank.bank"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bank.object', {
#             'object': obj
#         })
