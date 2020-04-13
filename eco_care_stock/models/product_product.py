# Copyright 2014 - Vauxoo http://www.vauxoo.com/
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
#   (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.constrains('default_code')
    def only_default_code(self):
        if self.env.user.has_group('eco_care_stock.group_res_default_code') \
                and self.default_code:
            if self.search([('default_code', '=', self.default_code)]) - self:
                raise ValidationError(_('La referencia del producto debe ser única'))
