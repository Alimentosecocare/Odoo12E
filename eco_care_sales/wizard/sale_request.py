# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# 1 : imports of python lib
# 2 :  imports of odoo
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.tools import float_is_zero
# 3 :  imports from odoo addons
from odoo.addons import decimal_precision as dp


class SaleOrderRequest(models.TransientModel):
    _name = "sale.order.request"
    _description = "Sale Order Request"
    _rec_name = 'date'

    date = fields.Datetime('Request Date', readonly=True, required=True, default=fields.Datetime.now)
    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('confirm', 'In Progress'),
        ('done', 'Validated'),
        ], copy=False, index=True, readonly=True,
        default='draft')
    line_ids = fields.One2many(
        'sale.order.request.line', 'request_id', string='Requests',
        copy=True, readonly=False,
        states={'done': [('readonly', True)]}
        )
    total_qty = fields.Float('Total Quantity', compute='_compute_total_qty')
    category_ids = fields.Many2many(
        'product.category', 'sale_order_request_product_category_rel', 'sale_request_id', 'category_id',
        string='Product Category', readonly=True, states={'draft': [('readonly', False)]},
        help="Specify Product Category to focus your request on a particular Category."
        )
    product_id = fields.Many2one(
        'product.product', 'Requested Product',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Specify Product to focus your request on a particular Product."
        )
    filter = fields.Selection(
        string='Request of', selection='_selection_filter',
        required=True,
        default='none',
        help="If you do an entire request, you can choose 'All Products' and it will prefill the request with the current stock.  If you only do some products  "
             "(e.g. Cycle Counting) you can choose 'Manual Selection of Products' and the system won't propose anything.  You can also let the "
             "system propose for a single product")
    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        readonly=True,
        domain=[('customer', '=', True)],
        states={'draft': [('readonly', False)]},
        help="Specify Customer to focus your Request on a particular Customer.")
    customer_id = fields.Many2one(
        'res.partner', 'Customer',
        readonly=True,
        domain=[('customer', '=', True)],
        states={'confirm': [('readonly', False)]})
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist',
        readonly=True, states={'confirm': [('readonly', False)]},
        help="Pricelist for the quotation order."
        )
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, index=True, required=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('sale.order.request')
        )
    exclusive = fields.Boolean('Include Exclusive Products', readonly=True, states={'draft': [('readonly', False)]})

    @api.one
    @api.depends('product_id', 'line_ids.product_qty')
    def _compute_total_qty(self):
        """ For single product inventory, total quantity of the counted """
        if self.product_id:
            self.total_qty = sum(self.mapped('line_ids').mapped('product_qty'))
        else:
            self.total_qty = 0

    @api.model
    def _selection_filter(self):
        """ Get the list of filter allowed  """
        return [
            ('none', _('All products')),
            ('category', _('One or more product category')),
            ('product', _('One product only')),
            ('partial', _('Select products manually')),
            ('previously_sale', _('One o more previously saled products for a specific cliente')),
            ]

    @api.onchange('filter')
    def _onchange_filter(self):
        if self.filter not in ('product', 'previously_sale'):
            self.product_id = False
        if self.filter not in ('previously_sale'):
            self.partner_id = False
        if self.filter != 'category':
            self.category_ids = False
        if self.filter in ('product', 'partial'):
            self.exclusive = False
        if self.filter == 'product':
            self.exhausted = True
            domain = [('sale_ok', '=', True)]
            if self.product_id:
                domain.append(('product_tmpl_id', '=', self.product_id.product_tmpl_id.id))
            return {
                'domain': {'product_id': domain},
                }


    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.customer_id = self.partner_id

    @api.multi
    @api.onchange('customer_id')
    def onchange_customer_id(self):
        if not self.customer_id:
            return

        values = {
            'pricelist_id': self.customer_id.property_product_pricelist and self.customer_id.property_product_pricelist.id or False,
            }

        self.update(values)

    # @api.one
    # @api.constrains('filter', 'product_id', 'lot_id', 'partner_id', 'package_id')
    # def _check_filter_product(self):
    #    if self.filter == 'none' and self.product_id:
    #        return
    #    if self.filter not in ('product', 'product_owner') and self.product_id:
    #        raise ValidationError(_('The selected product doesn\'t belong to that owner..'))
    #    if self.filter not in ('owner', 'product_owner') and self.partner_id:
    #        raise ValidationError(_('The selected owner doesn\'t have the proprietary of that product.'))

    def action_start(self):
        for request in self.filtered(lambda x: x.state not in ('done', 'cancel')):
            vals = {
                'date': fields.Datetime.now(),
                'state': 'confirm',
                }
            if (request.filter != 'partial') and not request.line_ids:
                vals.update({'line_ids': [(0, 0, line_values) for line_values in request._get_request_lines_values()]})
            request.write(vals)
        # return True

    def action_cancel_draft(self):
        self.write({
            'line_ids': [(5,)],
            'state': 'draft'
            })

    def action_reset_product_qty(self):
        self.mapped('line_ids').write({'product_qty': 0})
        # return True

    def action_validate(self):
        if not self.customer_id:
            raise ValidationError(_(
                "A customer is required for create a Quotations"
                ))

        lines = self.line_ids.filtered(lambda l: not float_is_zero(l.product_qty, precision_rounding=l.product_uom_id.rounding))
        if lines:
            order = self.env['sale.order'].create(self._prepare_order_vals(lines))

            order.onchange_partner_id()
            for line in order.order_line:
                line.product_id_change()

            self.write({
                'state': 'done',
                })

            return {
                'name': _('Quotation'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'target': 'main',
                'res_id': order.id,
                }

    def _get_request_lines_values(self):
        Product = self.env['product.product']
        vals = []

        # case 0: Filter on Saleable & exclusive products
        domain = [('sale_ok', '=', True), ('exclusive_ok', '=', self.exclusive)]
        # case 1: Filter on One or more product category
        if self.category_ids:
            domain.append(('categ_id', 'child_of', self.category_ids.ids))
        # case 2: Filter on One product
        if self.product_id:
            domain.append(('id', '=', self.product_id.id))
        # case 3: Filter on Company
        if self.company_id:
            domain.extend([
                '|', ('company_id', 'child_of', self.company_id.ids),
                ('company_id', '=', False),
                ])
        # case 4: Filter on previously sale to a specific owner
        if self.partner_id:
            previously_saleable_products = self.env['sale.order.line'].search([
                ('order_partner_id', '=', self.partner_id.id),
                ('is_downpayment', '=', False),
                ('is_expense', '=', False),
                ('state', '=', 'sale'),
                ]).mapped('product_id')
            domain.append(('id', 'in', previously_saleable_products.ids))

        for requested_product in Product.search(domain):
            vals.append(self._prepare_requested_line_vals(requested_product))

        return vals

    @api.model
    def _prepare_requested_line_vals(self, requested_product):
        return {
            'product_uom_id': requested_product.uom_id.id,
            'product_id': requested_product.id,
            }

    def _prepare_order_vals(self, lines):
        return {
            'pricelist_id': self.pricelist_id.id,
            'partner_id': self.customer_id.id,
            'date_order': self.date,
            'order_line': [(0, 0, self._prepare_order_line_vals(line)) for line in lines]
           }

    def _prepare_order_line_vals(self, line):
        return {
            'name': line.product_id.get_product_multiline_description_sale(),
            'product_uom': line.product_uom_id.id,
            'product_uom_qty': line.product_qty,
            'product_id': line.product_id.id,
            }


class SaleOrderRequestLIne(models.TransientModel):
    _name = "sale.order.request.line"
    _description = "Sale Order Request Line"
    _order = "product_id, request_id"


    request_id = fields.Many2one(
        'sale.order.request', 'Request',
        index=True, ondelete='cascade')
    request_partner_id = fields.Many2one(related='request_id.partner_id', store=True, string='Customer', readonly=False)
    product_id = fields.Many2one(
        'product.product', 'Product',
        index=True, required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        required=True)
    product_uom_category_id = fields.Many2one(
        string='Uom category', related='product_uom_id.category_id',
        readonly=True)
    product_qty = fields.Float(
        'Requested Quantity',
        digits=dp.get_precision('Product Unit of Measure'), default=0)
    company_id = fields.Many2one(
        'res.company', 'Company', related='request_id.company_id',
        index=True, readonly=True, store=True)
    state = fields.Selection(
        'Status', related='request_id.state', readonly=True)

    #    theoretical_qty = fields.Float(
    #        'Theoretical Quantity', compute='_compute_theoretical_qty',
    #        digits=dp.get_precision('Product Unit of Measure'), readonly=True, store=True
    #        )

    #    @api.one
    #    @api.depends('product_id', 'product_uom_id', 'company_id')
    #    def _compute_theoretical_qty(self):
    #        if not self.product_id:
    #            self.theoretical_qty = 0
    #            return
    #        theoretical_qty = self.product_id.get_theoretical_quantity(
    #            self.product_id.id,
    #            self.location_id.id,
    #            lot_id=self.prod_lot_id.id,
    #            package_id=self.package_id.id,
    #            owner_id=self.partner_id.id,
    #            to_uom=self.product_uom_id.id,
    #        )
    #        self.theoretical_qty = theoretical_qty

    @api.onchange('product_id')
    def _onchange_product(self):
        res = {}
        # If no UoM or incorrect UoM put default one from product
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
            res['domain'] = {'product_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return res

    @api.onchange('state')
    def _onchange_state(self):
        domain = [('exclusive_ok', '=', self.request_id.exclusive), ('sale_ok', '=', True)]

        if self.request_id.partner_id and self.request_id.exclusive:
            domain.append(('product_tmpl_id', 'in', self.request_id.partner_id.exclusive_product_ids.ids))

        return {
            'domain': {'product_id': domain},
            }
