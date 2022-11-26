from odoo import fields, models

from .conditions import CONDITION_BY_ID, CONDITION_SELECTION


class Driver(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"
    _order = "driver_priority asc"

    # TODO When added by other dispatch rules, this field can be changed!
    driver_priority = fields.Integer(
        string="Priority",
        default=0,
        help="Ordered by ascending priority, first driver gets assigned (by default). "
        "Otherwise, uses dispatch rule driver preference.",
    )
    has_vehicle = fields.Boolean(
        compute="_compute_has_vehicle",
        search="_search_has_vehicle",
        store=False,
        readonly=True,
    )

    def _compute_has_vehicle(self):
        driver_ids = self.env["fleet.vehicle"].search([]).driver_id.ids
        for record in self:
            record.has_vehicle = record.id in driver_ids

    def _search_has_vehicle(self, operator, value):
        if (operator == "=" and value is True) or (operator == "!=" and value is False):
            operator_new = "inselect"
        else:
            operator_new = "not inselect"
        return [("id", operator_new, ("SELECT driver_id FROM fleet_vehicle", ()))]


class DispatchRule(models.Model):
    _name = "order.dispatch.rule"
    _description = "Dispatch rules"
    _order = "priority asc"

    name = fields.Char(required=True, size=64)
    priority = fields.Integer(
        default=0,
        help="Ordered by ascending priority, first dispatch rule "
        "that yields matches for drivers is used for automatic "
        "order-driver assignment",
    )
    conditions = fields.Many2many(
        comodel_name="order.dispatch.condition",
    )
    active = fields.Boolean(default=True, help="Activate/deactivate the rule")
    preferred_drivers = fields.Many2many("res.partner")

    def get_matches(self):
        for condition in self.conditions:
            _matches = condition.get_matches()
            if _matches:
                return (condition, _matches)


class NoConditionClassException(Exception):
    pass


class DispatchCondition(models.Model):
    _name = "order.dispatch.condition"
    _description = "Condition"
    _order = "sequence, id"

    name = fields.Char(required=True, size=64)
    sequence = fields.Integer(help="Determine the display order", default=10)
    domain = fields.Char(
        string="Filter", compute="_compute_domain", readonly=False, store=True
    )
    # Conditions that yields matching orders
    condition = fields.Selection(
        selection=CONDITION_SELECTION,
    )
    # Premise value
    premise_value = fields.Char(
        string="Premise",
        required=False,
        help="Premise value to complement condition if needed. "
        "(Example: City (condition) is Dublin (premise value))",
    )
    premise_help = fields.Text(required=False)

    def get_matches(self):
        condition_class = CONDITION_BY_ID.get(self.condition)
        if not condition_class:
            raise NoConditionClassException(f"{condition_class} not found")
        if not hasattr(condition_class, "get_matches"):
            raise NotImplementedError(
                f"{condition_class} has no `get_matches` implementation"
            )
        return condition_class.get_matches(
            env=self.env, premise_value=self.premise_value
        )
