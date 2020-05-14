# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        exclusive_domain = [('sale_ok', '=', True), ('exclusive_ok', '=', False)]

        if self.partner_id and self.partner_id.exclusive_product_ids:
            exclusive_domain[-1:] = ['|',  ('exclusive_ok', '=', False), ('product_tmpl_id', 'in', self.partner_id.exclusive_product_ids.ids)]

        return {
            'domain': {'order_line': exclusive_domain},
            }


class SaleOrderLIne(models.Model):
    _inherit = "sale.order.line"

    product_id = fields.Many2one(domain=[('sale_ok', '=', True), ('exclusive_ok', '=', False)])
