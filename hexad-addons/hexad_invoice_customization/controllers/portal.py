# -*- coding: utf-8 -*-

from odoo.addons.sale.controllers import portal as sale_portal


class CustomerPortal(sale_portal.CustomerPortal):

    def _get_payment_values(self, order_sudo, is_down_payment=False, payment_amount=None, **kwargs):
        """ Override to use amount_total_after_tds when TDS is applicable """
        # If TDS is applicable, calculate the adjusted payment amount
        print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        if order_sudo.tds_applicable and order_sudo.amount_total_after_tds:
            print("TDS is applicable------------------------------------------")
            print("payment_amount: ", payment_amount)
            print("order_sudo.amount_total_after_tds: ", order_sudo.amount_total_after_tds)
            # Calculate adjusted payment_amount based on TDS
            if is_down_payment:
                if payment_amount and payment_amount < order_sudo.amount_total_after_tds:
                    adjusted_payment_amount = payment_amount
                else:
                    # Adjust prepayment proportionally
                    prepayment_amount = order_sudo._get_prepayment_required_amount()
                    if order_sudo.amount_total > 0:
                        prepayment_ratio = prepayment_amount / order_sudo.amount_total
                        adjusted_payment_amount = order_sudo.amount_total_after_tds * prepayment_ratio
                    else:
                        adjusted_payment_amount = prepayment_amount
            elif order_sudo.state == 'sale':
                adjusted_payment_amount = payment_amount or order_sudo.amount_total_after_tds
            else:
                adjusted_payment_amount = order_sudo.amount_total_after_tds
            
            # Temporarily replace amount_total to affect super() calculations
            original_amount_total = order_sudo.amount_total
            order_sudo.amount_total = order_sudo.amount_total_after_tds
            
            try:
                # Call super with adjusted payment_amount
                res = super()._get_payment_values(
                    order_sudo, 
                    is_down_payment=is_down_payment, 
                    payment_amount=adjusted_payment_amount, 
                    **kwargs
                )
                # Ensure the amount in payment_context uses the adjusted amount
                if 'amount' in res:
                    res['amount'] = adjusted_payment_amount
            finally:
                # Restore original amount_total
                order_sudo.amount_total = original_amount_total
            
            return res
        
        # If TDS is not applicable, use default behavior
        return super()._get_payment_values(
            order_sudo, 
            is_down_payment=is_down_payment, 
            payment_amount=payment_amount, 
            **kwargs
        )

