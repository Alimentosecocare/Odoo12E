# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_res_default_code = fields.Boolean("Usar referencias únicas",
                                            implied_group='eco_care_stock.group_res_default_code')
