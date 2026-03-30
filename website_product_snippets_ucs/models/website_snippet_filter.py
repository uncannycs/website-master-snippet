# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from collections import Counter
from odoo.osv import expression


class WebsiteSnippetFilter(models.Model):
    _inherit = 'website.snippet.filter'

    def _get_hardcoded_sample(self, model):
        samples = super()._get_hardcoded_sample(model)
        if model._name == 'product.template':
            data = [{
                'image_512': b'/product/static/img/product_chair.jpg',
                'display_name': _('Chair'),
                'description_sale': _('Sit comfortably'),
            }, {
                'image_512': b'/product/static/img/product_lamp.png',
                'display_name': _('Lamp'),
                'description_sale': _('Lightbulb sold separately'),
            }, {
                'image_512': b'/product/static/img/product_product_20-image.png',
                'display_name': _('Whiteboard'),
                'description_sale': _('With three feet'),
            }, {
                'image_512': b'/product/static/img/product_product_27-image.jpg',
                'display_name': _('Drawer'),
                'description_sale': _('On wheels'),
            }, {
                'image_512': b'/product/static/img/product_product_7-image.png',
                'display_name': _('Box'),
                'description_sale': _('Reinforced for heavy loads'),
            }, {
                'image_512': b'/product/static/img/product_product_9-image.jpg',
                'display_name': _('Bin'),
                'description_sale': _('Pedal-based opening system'),
            }]
            merged = []
            for index in range(0, max(len(samples), len(data))):
                merged.append({**samples[index % len(samples)], **data[index % len(data)]})
                # merge definitions
            samples = merged
        return samples

    def _filter_records_to_values(self, records, is_sample=False):
        res_products = super()._filter_records_to_values(records, is_sample)
        if self.model_name == 'product.template':
            for res_product in res_products:
                product = res_product.get('_record')
                if not is_sample:
                    res_product.update(product.product_variant_ids[0]._get_combination_info_variant())
                    if records.env.context.get('add2cart_rerender'):
                        res_product['_add2cart_rerender'] = True
        return res_products

    @api.model
    def _get_products_template(self, mode, context):
        dynamic_filter = context.get('dynamic_filter')
        handler = getattr(self, '_get_products_template_%s' % mode, self._get_products_latest_sold)
        website = self.env['website'].get_current_website()
        search_domain = context.get('search_domain')
        limit = context.get('limit')
        domain = expression.AND([
            [('website_published', '=', True)],
            website.website_domain(),
            [('company_id', 'in', [False, website.company_id.id])],
            search_domain or [],
        ])
        products = handler(website, limit, domain, context)
        return dynamic_filter._filter_records_to_values(products, False)


    def _get_products_template_latest_sold(self, website, limit, domain, context):
        product_templates = []
        sale_orders = self.env['sale.order'].sudo().search([
            ('website_id', '=', website.id),
            ('state', 'in', ('sale', 'done')),
        ], limit=8, order='date_order DESC')
        if sale_orders:
            sold_products = [p.product_id.id for p in sale_orders.order_line]
            products_ids = [id for id, _ in Counter(sold_products).most_common()]
            products = self.env['product.product'].browse(products_ids)
            product_template_ids = products.mapped('product_tmpl_id').mapped('id')
            if product_template_ids:
                domain = expression.AND([
                    domain,
                    [('id', 'in', product_template_ids)],
                ])
                product_templates = self.env['product.template'].with_context(display_default_code=False).search(domain)
                product_templates = product_templates.sorted(key=lambda p: product_template_ids.index(p.id))[:limit]
        return product_templates

    def _get_products_template_latest_viewed(self, website, limit, domain, context):
        product_templates = []
        visitor = self.env['website.visitor']._get_visitor_from_request()
        if visitor:
            excluded_products = website.sale_get_order().order_line.product_id.ids
            tracked_products = self.env['website.track'].sudo()._read_group(
                [('visitor_id', '=', visitor.id), ('product_id', '!=', False),
                 ('product_id.website_published', '=', True), ('product_id', 'not in', excluded_products)],
                ['product_id', 'visit_datetime:max'], ['product_id'], limit=limit, orderby='visit_datetime DESC')
            products_ids = [product['product_id'][0] for product in tracked_products]
            products = self.env['product.product'].browse(products_ids)
            product_template_ids = products.mapped('product_tmpl_id').mapped('id')
            if product_template_ids:
                domain = expression.AND([
                    domain,
                    [('id', 'in', product_template_ids)],
                ])
                product_templates = self.env['product.template'].with_context(display_default_code=False,
                                                                              add2cart_rerender=True).search(domain,
                                                                                                             limit=limit)
        return product_templates

    def _get_products_template_recently_sold_with(self, website, limit, domain, context):
        product_templates = []
        current_id = context.get('product_template_id')
        if current_id:
            current_id = int(current_id)
            sale_orders = self.env['sale.order'].sudo().search([
                ('website_id', '=', website.id),
                ('state', 'in', ('sale', 'done')),
                ('order_line.product_id.product_tmpl_id', '=', current_id),
            ], limit=8, order='date_order DESC')
            if sale_orders:
                current_template = self.env['product.template'].browse(current_id)
                excluded_products = website.sale_get_order().order_line.product_id.product_tmpl_id.product_variant_ids.ids
                excluded_products.extend(current_template.product_variant_ids.ids)
                included_products = []
                for sale_order in sale_orders:
                    included_products.extend(sale_order.order_line.product_id.ids)
                products_ids = list(set(included_products) - set(excluded_products))
                products = self.env['product.product'].browse(products_ids)
                product_template_ids = products.mapped('product_tmpl_id').mapped('id')
                if product_template_ids:
                    domain = expression.AND([
                        domain,
                        [('id', 'in', product_template_ids)],
                    ])
                    product_templates = self.env['product.template'].with_context(display_default_code=False).search(domain, limit=limit)
        return product_templates

    def _get_products_template_accessories(self, website, limit, domain, context):
        product_templates = []
        current_id = context.get('product_template_id')
        if current_id:
            current_id = int(current_id)
            current_template = self.env['product.template'].browse(current_id)
            if current_template.exists():
                excluded_products = website.sale_get_order().order_line.product_id.ids
                excluded_products.extend(current_template.product_variant_ids.ids)
                included_products = current_template._get_website_accessory_product().ids
                products_ids = list(set(included_products) - set(excluded_products))
                products = self.env['product.product'].browse(products_ids)
                product_template_ids = products.mapped('product_tmpl_id').mapped('id')
                if product_template_ids:
                    domain = expression.AND([
                        domain,
                        [('id', 'in', product_template_ids)],
                    ])
                    product_templates = self.env['product.template'].with_context(display_default_code=False).search(domain, limit=limit)
        return product_templates

    def _get_products_template_alternative_products(self, website, limit, domain, context):
        product_templates = self.env['product.template']
        current_id = context.get('product_template_id')
        if not current_id:
            return products
        current_template = self.env['product.template'].browse(int(current_id))
        if current_template.exists():
            excluded_products = website.sale_get_order().order_line.product_id
            excluded_products |= current_template.product_variant_ids
            included_products = current_template.alternative_product_ids.product_variant_ids
            products = included_products - excluded_products
            product_templates = products.mapped('product_tmpl_id')
            if products:
                domain = expression.AND([
                    domain,
                    [('id', 'in', product_templates.ids)],
                ])
                product_templates = self.env['product.template'].with_context(display_default_code=False).search(domain, limit=limit)
        return product_templates