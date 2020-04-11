# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_repr

from odoo.addons import decimal_precision as dp

from odoo.tools import pycompat


class ResPArtner(models.Model):
    _inherit= "res.partner"

    vat = fields.Char(required=True, copy=False)

    # _sql_constraints = [
    #     ('name_country_vat_uid_unique',
    #      'unique (vat, country_id)', 'El RUT debe ser ùnico para un socio del mismo país'),
    # ]

    @api.constrains('vat', 'country_id')
    def only_vat_country(self):
        if self.search([('vat', '=', self.vat),
                        ('country_id', '=', self.country_id.id)]) - self:
            raise ValidationError(_('El RUT debe ser único para un socio del mismo país'))
