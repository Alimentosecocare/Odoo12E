# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    exclusive_product_ids = fields.Many2many(
        'product.template', 'product_template_exclusive_partner_rel', 'partner_id', 'product_tmpl_id',
        string="Exclusive Products"
        )