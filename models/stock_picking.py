import json
import logging
import random

from odoo import models

from .dispatch import DispatchRule, NoConditionClassException

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_assign(self):
        """Assigns the order to company driver when available and has matches"""
        _logger.info("[.] Starting action")
        action_assign = super().action_assign()

        for picking in self:
            _logger.info("[.] Picking state %s", picking.state)
            if picking.state != "assigned":
                continue
            DispatchRules = self.env["order.dispatch.rule"]
            matched_conditions = {}
            preferred_drivers = []
            debug_dump = {
                "partner_id.country_id.name": picking.partner_id.country_id.name,
                "partner_id.city": picking.partner_id.city,
            }
            _logger.info("Debug dump\n%r", json.dumps(debug_dump))
            # Find conditions in which orders got this picking
            for rule in DispatchRules.search([("active", "=", True)]):
                _logger.info("Dispatch rule %s", rule.name)
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
                _logger.info("[!] Rule has match? %r", rule_has_match)
                _logger.info("[!] Rule has drivers? %r", rule.preferred_drivers)
                if rule_has_match and rule.preferred_drivers:
                    _logger.info(
                        "Rule (name=%s, drivers=%r)",
                        rule.name,
                        rule.preferred_drivers.id,
                    )
                    preferred_drivers.extend(rule.preferred_drivers)

            # Auto-assign first preferred driver if only one
            preferred_drivers_set = {x for x in preferred_drivers}
            _logger.info("Matched conditions")
            for __, (_condition, _morders) in matched_conditions.items():
                _logger.info("%r %r", _condition, " ".join(str(x) for x in _morders))
            _logger.info("Preferred drivers %r", preferred_drivers_set)
            if len(matched_conditions.keys()):
                User = self.env["res.users"]
                partner = None
                driver = None  # User
                if len(preferred_drivers_set) == 1:
                    partner = preferred_drivers_set.pop()
                # TODO Prefer weighing than just random
                else:
                    partner = random.sample(sorted(preferred_drivers_set), 1)[0]
                driver = User.search([("partner_id", "=", partner.id)])
                if not driver:
                    _logger.warning(
                        "[!] Partner (%r) has no associated user_id. "
                        "Make sure to select the correct partner with associated user.",
                        partner,
                    )
                _logger.info(
                    "Driver (id=%d, name=%s) assigned to picking (id=%d)",
                    driver.id,
                    driver.display_name,
                    picking.id,
                )
                picking.sudo().write({"user_id": driver})
        return action_assign
