# -*- coding: utf-8 -*-
##########################################################################
#
#	Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   "License URL : <https://store.webkul.com/license.html/>"
#
##########################################################################
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
	_inherit = "account.invoice"


	@api.one
	@api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice', 'global_discount_type', 'global_order_discount')
	def _compute_amount(self):
		super(AccountInvoice, self)._compute_amount()
		totalAmount, totalDiscount = 0, 0
		amountUntaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
		amountTax = sum(line.amount for line in self.tax_line_ids)
		totalAmount = amountUntaxed + amountTax
		lineTotalDiscount = sum((line.quantity*(line.price_unit) - line.price_subtotal) if line.discount_type == 'percent' else line.discount for line in self.invoice_line_ids)
		totalDiscount = lineTotalDiscount
		IrConfigPrmtrSudo = self.env['ir.config_parameter'].sudo()
		orderObj = False
		discTax = 'untax'
		moduleObj = self.env['ir.module.module'].sudo().search(
			[("name","=","discount_sale_order"),("state","=","installed")])
		if self.type and self.type == 'in_invoice':
			orderObj = self.env['purchase.order'].sudo().search([('name', '=', self.origin)])
			discTax = IrConfigPrmtrSudo.get_param('purchase.global_discount_tax_po')
		if self.type and self.type == 'out_invoice' and moduleObj:
			orderObj = self.env['sale.order'].sudo().search([('name', '=', self.origin)])
			discTax = IrConfigPrmtrSudo.get_param('sale.global_discount_tax')
		totalGlobalDiscount = 0
		if discTax == 'untax':
			totalAmount = amountUntaxed
		else:
			totalAmount = amountUntaxed + amountTax
		if self.global_discount_type == 'percent':
			beforeGlobal = totalAmount
			totalAmount = totalAmount * (1 - (self.global_order_discount or 0.0)/100)
			totalGlobalDiscount = beforeGlobal - totalAmount
			totalDiscount += totalGlobalDiscount
		else:
			totalGlobalDiscount = self.global_order_discount or 0.0
			totalAmount = totalAmount - totalGlobalDiscount
			totalDiscount += totalGlobalDiscount
		if discTax == 'untax':
			totalAmount = totalAmount + amountTax
		self.total_discount = totalDiscount
		self.amount_untaxed = amountUntaxed
		self.amount_tax = amountTax
		self.amount_total = totalAmount
		self.total_global_discount = totalGlobalDiscount
		amount_total_company_signed = self.amount_total
		amount_untaxed_signed = self.amount_untaxed
		if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
			currency_id = self.currency_id.with_context(date=self.date_invoice)
			amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
			amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
		sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
		self.amount_total_company_signed = amount_total_company_signed * sign
		self.amount_total_signed = self.amount_total * sign
		self.amount_untaxed_signed = amount_untaxed_signed * sign

	@api.multi
	def get_taxes_values(self):
		tax_grouped = {}
		for line in self.invoice_line_ids:
			quantity = 1.0
			if line.discount_type == 'fixed':
				price_unit = line.price_unit * line.quantity - (line.discount or 0.0)
			else:
				quantity = line.quantity
				price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, quantity, line.product_id, self.partner_id)['taxes']
			for tax in taxes:
				val = self._prepare_tax_line_vals(line, tax)
				key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)
				if key not in tax_grouped:
					tax_grouped[key] = val
				else:
					tax_grouped[key]['amount'] += val['amount']
					tax_grouped[key]['base'] += val['base']
		return tax_grouped

	total_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_compute_amount', track_visibility='always')
	total_global_discount = fields.Monetary(string='Total Global Discount', store=True, readonly=True, compute='_compute_amount')
	global_discount_type = fields.Selection([
		('fixed', 'Fixed'),
		('percent', 'Percent')
		], string="Discount Type")
	global_order_discount = fields.Float(string='Global Discount', store=True, track_visibility='always')

	def _prepare_invoice_line_from_po_line(self, line):
		res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
		res.update(
			discount=line.discount,
			discount_type=line.discount_type
			)
		return res

	@api.onchange('invoice_line_ids')
	def _onchange_origin(self):
		super(AccountInvoice, self)._onchange_origin()
		purchase_ids = self.invoice_line_ids.mapped('purchase_id')
		if purchase_ids:
			self.global_discount_type = purchase_ids[0].global_discount_type
			self.global_order_discount = purchase_ids[0].global_order_discount

	@api.multi
	def finalize_invoice_move_lines(self, move_lines):
		inv_obj = self[0]
		if inv_obj.total_global_discount > 0.0 and self.type not in ('out_invoice', 'in_refund'):
			IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
			global_account = IrConfigPrmtr.get_param('purchase.discount_account_po')
			if not global_account:
				raise UserError(_("Global Discount!\nPlease first set account for global discount in purchase setting"))
			if global_account and int(global_account):
				global_account = self.env['account.account'].browse(int(global_account))
				for _, _ , line in move_lines:
					if line.get('credit') and not line.get('product_id'):
						line['credit'] -= inv_obj.total_global_discount
						break
				amount_currency = 0.0
				currency = inv_obj.currency_id
				company_currency = inv_obj.company_id.currency_id
				diff_currency = currency != company_currency
				if diff_currency:
					date = self._get_currency_rate_date() or fields.Date.context_today(self)
					amount_currency = currency._convert(
						inv_obj.total_global_discount, company_currency, inv_obj.company_id, date)
				else:
					currency = False
				global_line =  {
					'type': 'dest',
					'name': global_account.name,
					'price': -(inv_obj.total_global_discount),
					'account_id': global_account.id,
					'date_maturity': inv_obj.date_due,
					'amount_currency': diff_currency and amount_currency,
					'currency_id': currency and currency.id,
					'invoice_id': inv_obj.id
				}
				part = self.env['res.partner']._find_accounting_partner(inv_obj.partner_id)
				global_line = [(0, 0, self.line_get_convert(global_line, part.id))]
				move_lines += global_line
		return move_lines


class AccountInvoiceLine(models.Model):
	_inherit = "account.invoice.line"

	discount = fields.Float(string='Discount', digits=dp.get_precision('Discount'), default=0.0)
	discount_type = fields.Selection([
		('fixed', 'Fixed'),
		('percent', 'Percent')
		], string="Discount Type")

	@api.one
	@api.depends('price_unit', 'discount', 'discount_type', 'invoice_line_tax_ids', 'quantity',
		'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
		'invoice_id.date_invoice')
	def _compute_price(self):
		super(AccountInvoiceLine, self)._compute_price()
		currency = self.invoice_id and self.invoice_id.currency_id or None
		quantity = 1.0
		subTotalAmount = 0.0
		if self.discount_type == 'fixed':
			price = self.price_unit * self.quantity - self.discount or 0.0
			subTotalAmount = price
		else:
			quantity = self.quantity
			price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
			subTotalAmount = self.quantity * price
		taxes = False
		if self.invoice_line_tax_ids:
			taxes = self.invoice_line_tax_ids.compute_all(
				price, currency, quantity, product=self.product_id, partner=self.invoice_id.partner_id)
		if self.discount_type == 'fixed':
			self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else price
		else:
			self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
		if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
			price_subtotal_signed = self.invoice_id.currency_id.with_context(
				date=self.invoice_id.date_invoice).compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
		sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
		self.price_subtotal_signed = price_subtotal_signed * sign
