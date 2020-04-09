# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_repr

from odoo.addons import decimal_precision as dp

from odoo.tools import pycompat


class Pricelist(models.Model):
    _inherit= "product.pricelist"

    @api.multi
    def create_update_reference_pricelist(self):
        for record in self:
            product_ref_pricelist = self.env.get('reference.price.list').search(
                [('listprice_id', '=', record.id),
                 ('company_id', '=', record.company_id.id)]
            ).mapped('product_id')
            product_not_ref_pricelist = self.env.get('product.product').search([
                ('id', 'not in', product_ref_pricelist.ids)
            ])
            # CREAR SINO EXISTE
            if product_not_ref_pricelist:
                for product in product_not_ref_pricelist:
                    # Verificar primero si la tarifa aplica para el producto
                    # si aplica crearla
                    self.create_reference(product, record)
            #si existen productos y al cambiar la tarifa ya no aplica eliminar sus referencias
            if product_ref_pricelist:
                for product in product_ref_pricelist:
                    self.update_unlink_reference(product, record)

    @api.multi
    def create_update_reference_pricelist_pdct(self, product):
        for record in self:
            if record in product.reference_list_price_ids.mapped('listprice_id').filtered(
                    lambda l:l.company_id == record.company_id):
                self.update_unlink_reference(product, record)
            else:
                self.create_reference(product, record)

    @api.model
    def update_unlink_reference(self, product, pricelist):
        price_rule = pricelist._compute_price_rule([(product, 1.0, self.env.get('res.partner'))])
        if not price_rule:
            product.mapped('reference_list_price_ids').filtered(
                lambda r: r.listprice_id == pricelist).unlink()
        else:
            references = product.mapped('reference_list_price_ids').filtered(
                lambda r: r.listprice_id == pricelist)
            item = price_rule[product.id][1]
            if pricelist.item_ids and not item in pricelist.item_ids.ids:
                references.unlink()
            else:
                for ref in references:
                    if ref.price != price_rule[product.id][0]:
                        ref.write({'price': price_rule[product.id][0]})


    @api.model
    def create_reference(self, product, pricelist):
        price = product.list_price
        if not pricelist.item_ids:
            reference_pl = self.env.get('reference.price.list').sudo().create({
                'listprice_id': pricelist.id,
                'product_id': product.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'price': price,
                'company_id': pricelist.company_id.id
            })
        price_rule = pricelist._compute_price_rule([(product, 1.0, self.env.get('res.partner'))])
        if price_rule:
            item = price_rule[product.id][1]
            if item in pricelist.item_ids.ids:
                price = price_rule[product.id][0]
                reference_pl = self.env.get('reference.price.list').sudo().create({
                    'listprice_id': pricelist.id,
                    'product_id': product.id,
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'price': price,
                    'company_id': pricelist.company_id.id
                })