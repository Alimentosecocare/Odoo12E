# Copyright 2014 - Vauxoo http://www.vauxoo.com/
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
#   (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    subunits = fields.Integer(
        string='Sub Unidades',
    )
    reference_list_price_ids = fields.One2many('reference.price.list',
                                              related='product_variant_id.reference_list_price_ids')

    @api.multi
    def create_update_reference_pricelist(self):
        for record in self:
            record.product_variant_id.create_update_reference_pricelist()

class ProductProduct(models.Model):
    _inherit = 'product.product'

    reference_list_price_ids = fields.One2many('reference.price.list',
                                              'product_id',
                                              string='Prices Reference'
                                               )

    @api.multi
    def create_update_reference_pricelist(self):
        for record in self:
            ProductPricelist = self.env.get('product.pricelist')
            rest_price_list = ProductPricelist.search([])
            rest_price_list.create_update_reference_pricelist_pdct(record)
