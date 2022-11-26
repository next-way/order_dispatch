import logging

from odoo import SUPERUSER_ID, models

from .dispatch import NoConditionClassException

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_assign(self):
        """Assigns the order to company driver when available and has matches"""
        action_assign = super().action_assign()

        for picking in self:
            if picking.state != "assigned":
                continue
            DispatchCondition = self.env["order.dispatch.condition"]
            matched_conditions = {}
            # Find conditions in which orders got this picking
            for condition in DispatchCondition.search([]):
                try:
                    matched_orders = (
                        condition.get_matches()
                    )  # returns sale.order recordset
                except (NoConditionClassException, NotImplementedError):
                    _logger.info(f"[CRITICAL] Got a problem with condition {condition}")
                    continue
                matched_orders_with_this_picking = matched_orders.filtered(
                    lambda o: picking.id == o.picking_ids.id
                )
                if len(matched_orders_with_this_picking):
                    matched_conditions[condition.id] = (
                        condition,
                        matched_orders_with_this_picking,
                    )
            # Test
            if len(matched_conditions.keys()):
                self.user_id = SUPERUSER_ID

        return action_assign
