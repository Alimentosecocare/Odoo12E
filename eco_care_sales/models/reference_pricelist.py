# Copyright 2014 - Vauxoo http://www.vauxoo.com/
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
#   (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _

class ReferencePricelist(models.Model):
    _name = 'reference.price.list'

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.user.company_id.id)

    listprice_id = fields.Many2one('product.pricelist', 'Tarifa')
    product_id = fields.Many2one('product.product', 'Producto')
    product_tmpl_id = fields.Many2one('product.template', 'Producto')
    total_price = fields.Float('Total', compute='_compute_price')
    tax_ids = fields.Many2many(related='product_id.taxes_id', string='Impuestos')
    subunits = fields.Integer(related='product_id.subunits')
    currency_id = fields.Many2one(related='listprice_id.currency_id')
    price_unit = fields.Float('Neto por Unidad', compute='_compute_price')
    total_unit = fields.Float('Total por Unidad', compute='_compute_price')
    price = fields.Float('Neto')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=_get_default_company_id)

    @api.multi
    def _compute_price_unit(self):
        for record in self:
            record.price_unit = record.total_price / record.subunits

    @api.multi
    def _compute_price(self):
        for record in self:
            taxes = record.tax_ids.compute_all(record.price, record.currency_id, 1, record.product_id)
            amount_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
            total_price = amount_tax + record.price
            record.total_price = total_price
            if record.subunits:
                record.total_unit = record.total_price / record.subunits
                record.price_unit = record.price / record.subunits