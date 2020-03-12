# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Discount On Purchase Order",
  "summary"              :  "The module allows you to set discount in fixed/percent basis for purchase orders and order lines separately. The total discount in an order is sum of global discount and order line discount.",
  "category"             :  "Purchases",
  "version"              :  "1.3.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Discount-On-Purchase-Order.html",
  "description"          :  """Odoo Discount on Purchase Order
Purchase order discount
PO discount
Vendor discount Odoo
Odoo vendor discount
Instant discount Odoo
Odoo POS Order Discount
POS Order line discount
POS Orderline discount
Discount per product
POS Per product off
Odoo POS discount
Order discount
Fixed order line discount POS
Percentage discount odoo POS
Customer discount POS
Purchase discount """,
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=discount_purchase_order",
  "depends"              :  [
                             'purchase',
                             'account',
                            ],
  "data"                 :  [
                             'security/discount_security.xml',
                             'views/purchase_views.xml',
                             'views/account_invoice_view.xml',
                             'views/res_config_views.xml',
                             'report/purchase_order_templates.xml',
                            ],
  "demo"                 :  [
                             'data/discount_data.xml',
                             'data/discount_demo.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  25,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}