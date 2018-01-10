# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2017 Humanytek (<www.humanytek.com>).
#    Rubén Bravo <rubenred18@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ProductAnalysis(models.TransientModel):
    _name = "product.analysis"

    @api.multi
    def calculate(self):
        ProductProduct = self.env['product.product']
        ProductRejected = self.env['product.rejected']
        ProductAnalysisDetail = self.env['product.analysis.detail']
        StockMove = self.env['stock.move']
        #qty = 0
        #qty_reserve = 0
        products = ProductProduct.search([
                        ('product_tmpl_id.id', '=', self.product_id.id)])
        for product in products:
            stock_moves = StockMove.search([
                        ('product_id.id', '=', product.id),
                        ('date', '>=', self.date_start),
                        ('date', '<=', self.date_end),
                        ('state', '=', 'assigned'),
                        '|',
                        ('picking_type_id.code', '=', 'incoming'),
                        ('picking_type_id.code', '=', 'outgoing'),
                        #('location_dest_id.scrap_location', '=', False)
                        ],
                            order='date')
            ProductAnalysisDetail.search([]).unlink()
            product_outgoing = product_incomming = qty = qty_return = 0
            for stock_move in stock_moves:
                if stock_move.picking_type_id.code == 'incoming':
                    product_incomming += stock_move.product_uom_qty
                    #qty -= stock_move.product_uom_qty
                else:
                    product_outgoing += stock_move.product_uom_qty
                    #qty += stock_move.product_uom_qty
            stock_moves_ini = StockMove.search([
                        ('product_id.id', '=', self.product_id.id),
                        ('date', '<', self.date_end),
                        ('state', '=', 'done'),
                        '|',
                        ('picking_type_id.code', '=', 'incoming'),
                        ('picking_type_id.code', '=', 'outgoing'),
                        #('location_dest_id.scrap_location', '=', False)
                        ])
            for move_ini in stock_moves_ini:
                if move_ini.picking_type_id.code == 'incoming':
                    qty += move_ini.product_uom_qty
                else:
                    qty -= move_ini.product_uom_qty
            total_sale = qty_sale = qty_rejected = 0
            stock_moves_sale = StockMove.search([
                        ('product_id.id', '=', self.product_id.id),
                        ('state', 'in', ['done', 'assigned']),
                        ('picking_type_id.code', '=', 'outgoing'),
                        ('location_dest_id.scrap_location', '=', False)
                        ])
            for move_sale in stock_moves_sale:
                total_sale += move_sale.product_uom_qty
                if move_sale.date >= self.date_start and move_sale.date <= self.date_end:
                    qty_sale += move_sale.product_uom_qty
            stock_moves_return = StockMove.search([
                        ('product_id.id', '=', self.product_id.id),
                        ('date', '>=', self.date_start),
                        ('date', '<=', self.date_end),
                        ('state', '=', 'done'),
                        '|',
                        ('picking_type_id.code', '=', 'incoming'),
                        ('location_dest_id.scrap_location', '=', True)
                        ])
            for move_ret in stock_moves_return:
                qty_return += move_ret.product_uom_qty

            product_rejecteds = ProductRejected.search([
                        ('product_id.id', '=', product.id),
                        ('date', '>=', self.date_start),
                        ('date', '<=', self.date_end),
                        ])
            for product_rejected in product_rejecteds:
                qty_rejected += product_rejected.qty
            ProductAnalysisDetail.create({
                    #'stock_move_id': stock_move.id,
                    'product_id': product.id,
                    'product_analysis_id': self.id,
                    'qty_product': qty,
                    'qty_return': qty_return,
                    'product_incomming': product_incomming,
                    'product_outgoing': product_outgoing,
                    'qty_available': qty + product_incomming - product_outgoing,
                    'qty_total_sale': total_sale,
                    'qty_sale': qty_sale,
                    'qty_rejected': qty_rejected,
                    })
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.analysis',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
                }

    product_id = fields.Many2one('product.template', 'Product', required=True,
                        default=lambda self: self._context.get('product_id'))
    date_start = fields.Datetime('Start Date',
                                    required=True)
    date_end = fields.Datetime('End Date',
                                    required=True)
    product_analysis_detail_ids = fields.One2many('product.analysis.detail',
                            'product_analysis_id',
                            'Detail')


class ProductAnalysisDetail(models.TransientModel):
    _name = "product.analysis.detail"

    product_analysis_id = fields.Many2one('product.analysis', 'Analysis')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    #stock_move_id = fields.Many2one('stock.move', 'Move', readonly=True)
    qty_product = fields.Float('Quantity', readonly=True)
    product_incomming = fields.Float('Incoming Products', readonly=True)
    product_outgoing = fields.Float('Outgoing Products', readonly=True)
    qty_available = fields.Float('Available', readonly=True)
    qty_return = fields.Float('Quantity Return', readonly=True)
    qty_total_sale = fields.Float('Total Sales Quantity', readonly=True)
    qty_sale = fields.Float('Sales', readonly=True)
    qty_rejected = fields.Float('Rejected', readonly=True)