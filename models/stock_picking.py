import logging

from odoo import models

from .dispatch import DispatchRule, NoConditionClassException

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_assign(self):
        """Assigns the order to company driver when available and has matches"""
        action_assign = super().action_assign()

        for picking in self:
            if picking.state != "assigned":
                continue
            DispatchRules = self.env["order.dispatch.rule"]
            matched_conditions = {}
            preferred_drivers = []
            # Find conditions in which orders got this picking
            for rule in DispatchRules.search([("active", "=", True)]):
                rule: DispatchRule = rule
                rule_has_match = False
                for condition in rule.conditions:
                    try:
                        matched_orders = (
                            condition.get_matches()
                        )  # returns sale.order recordset
                    except (NoConditionClassException, NotImplementedError):
                        _logger.info(
                            f"[CRITICAL] Got a problem with condition {condition}"
                        )
                        continue
                    matched_orders_with_this_picking = matched_orders.filtered(
                        lambda o: picking.id == o.picking_ids.id
                    )
                    if len(matched_orders_with_this_picking):
                        matched_conditions[condition.id] = (
                            condition,
                            matched_orders_with_this_picking,
                        )
                        rule_has_match = True

                # Get preferred drivers
                if rule_has_match and rule.preferred_drivers:
                    preferred_drivers.extend(rule.preferred_drivers)

            # Auto-assign first preferred driver if only one
            if len(matched_conditions.keys()):
                if len(preferred_drivers) == 1:
                    # TODO Driver must be odoo user too?
                    picking.user_id = preferred_drivers[0].user_id
            # TODO Notify if multiple preferred drivers?

        return action_assign
