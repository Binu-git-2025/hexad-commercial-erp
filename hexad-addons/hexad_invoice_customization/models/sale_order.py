# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    tds_applicable = fields.Boolean("Is TDS Applicable?", default=False, tracking=True)
    tds_percent = fields.Float("TDS %", default=0.0, readonly=True, tracking=True)
    tds_amount = fields.Monetary(
        "TDS Amount",
        compute="_compute_tds_amount",
        store=True,
        readonly=True,
        currency_field="currency_id",
        tracking=True,
    )
    amount_total_after_tds = fields.Monetary(
        "Total After TDS",
        compute="_compute_tds_amount",
        store=True,
        readonly=True,
        currency_field="currency_id",
        tracking=True,
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_tds(self):
        """Update TDS fields from partner when partner is selected"""
        if self.partner_id:
            self.tds_applicable = self.partner_id.tds_applicable
            self.tds_percent = self.partner_id.tds_percent


    @api.depends("amount_untaxed","amount_total", "tds_percent", "tds_applicable")
    def _compute_tds_amount(self):
        for order in self:
            if order.tds_applicable and order.tds_percent > 0:
                order.tds_amount = (order.amount_untaxed * order.tds_percent) / 100
            else:
                order.tds_amount = 0.0

            order.amount_total_after_tds = order.amount_total - order.tds_amount

    def _get_prepayment_required_amount(self):
        """ Override to use amount_total_after_tds when TDS is applicable for order confirmation """
        if self.tds_applicable and self.amount_total_after_tds:
            # Use amount_total_after_tds for prepayment calculation
            # This ensures that when customer pays amount_total_after_tds, the order gets confirmed
            if not self.require_payment:
                return 0
            else:
                return self.currency_id.round(self.amount_total_after_tds * self.prepayment_percent)
        return super()._get_prepayment_required_amount()

    def _get_default_payment_link_values(self):
        """ Override to use amount_total_after_tds when TDS is applicable in payment link """
        res = super()._get_default_payment_link_values()
        self.ensure_one()
        
        if self.tds_applicable and self.amount_total_after_tds:
            # Use amount_total_after_tds instead of amount_total for payment calculations
            remaining_balance = self.amount_total_after_tds - self.amount_paid
            
            # Adjust suggested_amount based on remaining balance
            # _get_prepayment_required_amount() is already overridden to use amount_total_after_tds
            if self.state in ('draft', 'sent') and self.require_payment:
                suggested_amount = self._get_prepayment_required_amount()
            else:
                suggested_amount = remaining_balance
            
            res.update({
                'amount': suggested_amount,
                'amount_max': remaining_balance,
            })
        
        return res

    

