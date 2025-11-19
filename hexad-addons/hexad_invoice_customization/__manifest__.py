# -*- coding: utf-8 -*-
{
    'name': 'Hexad Invoice Customization',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Customize invoice',
    'description': """
            Customize invoice email template
    """,
    'author': 'Hexad',
    'website': '',
    'depends': ['account', 'l10n_in'],
    'data': [
        # 'data/mail_template_data.xml',
        'views/report_invoice.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}


