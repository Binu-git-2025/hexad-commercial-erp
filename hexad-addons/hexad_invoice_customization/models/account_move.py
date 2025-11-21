# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.fields import Command


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        """ Override to create TDS journal entry when invoice is posted """
        posted = super()._post(soft)
        
        # Process TDS journal entries for posted invoices
        for invoice in posted.filtered(lambda move: move.is_invoice() and move.move_type == 'out_invoice'):
            # Get sale orders linked to this invoice
            sale_orders = invoice.line_ids.sale_line_ids.order_id
            
            for order in sale_orders:
                if order.tds_applicable and order.tds_amount > 0:
                    invoice._create_tds_journal_entry(order)
        
        return posted

    def _create_tds_journal_entry(self, sale_order):
        """ Create a journal entry for TDS amount """
        self.ensure_one()
        invoice = self
        
        # Find TDS Write-Offs journal by code or name
        tds_journal = self.env['account.journal'].search([
            ('code', '=', 'TWS'),
            ('company_id', '=', invoice.company_id.id),
        ], limit=1)
        
        if not tds_journal:
            # Try to find by name if code doesn't match
            tds_journal = self.env['account.journal'].search([
                ('name', 'ilike', 'TDS Write-Offs'),
                ('company_id', '=', invoice.company_id.id),
            ], limit=1)
        
        if not tds_journal:
            raise UserError(_(
                "TDS Write-Offs journal (code: TWS) not found. "
                "Please create a journal with code 'TWS' for TDS entries."
            ))
        
        # Get TDS Receivable account - search by code first, then by account type
        # You can configure a specific account code for TDS Receivable (e.g., 'TDS-REC')
        tds_receivable_account = self.env['account.account'].with_company(invoice.company_id).search([
            ('code', '=', '100580'),('account_type', '=', 'asset_current')
        ], limit=1)
        
        
        if not tds_receivable_account:
            # Fallback to asset_current account type if no code match found
            tds_receivable_account = self.env['account.account'].with_company(invoice.company_id).search([
                ('account_type', '=', 'asset_current'),
            ], limit=1)
        
        if not tds_receivable_account:
            raise UserError(_(
                "TDS Receivable account not found. "
                "Please configure a receivable account for TDS entries."
            ))
        
        # Get Accounts Receivable from invoice
        invoice_receivable_lines = invoice.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable'
        )
        if not invoice_receivable_lines:
            raise UserError(_(
                "No receivable account found on invoice %s. "
                "Cannot create TDS journal entry." % invoice.name
            ))
        invoice_receivable_account = invoice_receivable_lines[0].account_id
        
        # Calculate TDS amount in invoice currency
        tds_amount = sale_order.currency_id._convert(
            sale_order.tds_amount,
            invoice.currency_id,
            invoice.company_id,
            invoice.date,
        )
        
        # Create journal entry
        tds_move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': tds_journal.id,
            'date': invoice.date,
            'ref': _('TDS Entry for Invoice %s - Order %s') % (invoice.name, sale_order.name),
            'line_ids': [
                Command.create({
                    'account_id': tds_receivable_account.id,
                    'partner_id': invoice.partner_id.id,
                    'debit': tds_amount,
                    'credit': 0.0,
                    'name': _('TDS Receivable - %s') % sale_order.name,
                }),
                Command.create({
                    'account_id': invoice_receivable_account.id,
                    'partner_id': invoice.partner_id.id,
                    'debit': 0.0,
                    'credit': tds_amount,
                    'name': _('TDS Write-Off - %s') % sale_order.name,
                }),
            ],
        })
        
        # Post the journal entry
        tds_move.action_post()
        
        return tds_move

