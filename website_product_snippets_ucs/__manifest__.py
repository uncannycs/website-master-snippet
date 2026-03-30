# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO Open Source Management Solution
#
#    ODOO Addon module by Uncanny Consulting Services LLP
#    Copyright (C) 2022 Uncanny Consulting Services LLP (<https://uncannycs.com>).
#
##############################################################################
{
    "name": "Dynamic Product Master Snippet",
    "summary": "This module features to provide you a dynamic product master snippet in card structure.",
    "version": "18.0.0.0",
    "category": "Website",
    "website": "https://uncannycs.com",
    "author": "Uncanny Consulting Services LLP",
    "maintainers": "Uncanny Consulting Services LLP",
    "license": "Other proprietary",
    "application": False,
    "installable": True,
    "preloadable": True,
    "images": ["static/description/banner.gif"],
    "depends": [
        "website_sale","website","stock"
    ],
    "data": [
        'data/data.xml',
        'views/product_template_snippet_data.xml',
        'views/snippets.xml',
        'views/s_dynamic_snippet_products_template.xml',
    ],
    "assets": {
        'website.assets_wysiwyg': [
            'website_product_snippets_ucs/static/src/js/website_sale_snippet_products_options.js',
        ],
    },
    "price": 30,
    "currency": "USD",
}
