# Copyright 2014 - Vauxoo http://www.vauxoo.com/
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
#   (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "ECO-CARE SALES",
    "version": "11.0.1.0.1",
    "author": "Movilize",
    "category": "Sales",
    "license": "AGPL-3",
    "depends": [
        "sale_management",

    ],
    "data": [
        "views/product_template_views.xml",
        "views/product_pricelist_views.xml",
        'security/ir.model.access.csv',
    ],
    "installable": True,
}
