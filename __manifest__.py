# -*- coding: utf-8 -*-
{
    'name': "Bank",

    'summary': """
        Bank Management System""",

    'description': """
        The bank management system module in Odoo 16 offers a complete solution for managing various aspects of banking operations.
         It allows users to create and maintain records for banks, branches, customers, accounts, credit cards, employees, and transactions.
    """,

    'author': "Usman",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'mail', 'hr', 'portal'],

    'application': True,
    'auto_install': False,
    'sequence': '-100',

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security_access_data_view.xml',
        'data/branch_data.xml',
        'data/account_data.xml',
        'data/transaction_data.xml',
        'data/complaint_data.xml',
        'data/mail_template_data.xml',
        'views/portal_template.xml',
        'views/menu.xml',
        'views/bank_view.xml',
        'views/branch_view.xml',
        'views/employee_view.xml',
        'views/customer_view.xml',
        'views/account_view.xml',
        'views/card_view.xml',
        'views/transaction_view.xml',
        'views/complaint_view.xml',
        'views/chatbot_view.xml',
        'views/complaint_tag_view.xml',
        'views/loan_view.xml',
        'views/loan_account_view.xml',
        'views/loan_payment_view.xml',
        'report/bank_card.xml',
        'report/bank_statement.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bank/static/src/xml/bank_assistant.xml',
            'bank/static/src/js/bank_assistant.js',
        ]
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
