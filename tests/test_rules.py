from odoo.tests import common, new_test_user, tagged

from ..models.conditions import PackageTypeMedium
from .base import DispatchTestMixin


@tagged("-at_install", "post_install")
class TestRules(DispatchTestMixin, common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.default_customer = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "phone": "",
                "email": "",
                "mobile": "",
                "street": "Test street",
                "street2": "Test street2",
                "city": "Cebu City",
                "zip": "6000",
                "state_id": False,
                "country_id": self.country_ph.id,
            }
        )
        self.driver_2_user = new_test_user(
            self.env, "driver user 2", groups="base.group_user"
        )
        self.driver_2_user.partner_id.write(
            {
                "phone": "",
                "email": "",
                "mobile": "",
                "street": "Test street",
                "street2": "Test street2",
                "city": "Talisay City",
                "zip": "6045",
                "state_id": False,
                "country_id": self.country_ph.id,
            }
        )
        self.driver_2 = self.driver_2_user.partner_id
        self.driver_1 = self.driver.partner_id

    # TODO Promote to DispatchTestMixin
    def setup_rule(
        self, conditions=None, priority=0, preferred_drivers=None, active=True
    ):
        conditions = conditions or []
        if len(conditions) == 0:
            raise ValueError("Must specify at least one condition")
        preferred_drivers = preferred_drivers or []
        DispatchRule = self.env["order.dispatch.rule"]
        dispatch_rule = DispatchRule.create(
            {
                "name": f"Dispatch rule #{ DispatchRule.search_count([]) + 1 }",
                "conditions": conditions,
                "preferred_drivers": preferred_drivers,
                "active": active,
            }
        )
        return dispatch_rule

    def test_one_rule_one_preferred_driver(self):
        t_condition = self.env["order.dispatch.condition"].search(
            domain=[("condition", "=", "condition.city.from")]
        )
        t_condition.premise_value = "philippines, cebu city"
        self.setup_rule(
            conditions=[t_condition.id], preferred_drivers=[self.driver_1.id]
        )
        self.setup_order(package=self.small_package, customer=self.default_customer)
        picking = self.sale_order.picking_ids[0]
        self.assertEqual(self.driver_1.user_id, picking.user_id)

    def test_one_rule_multiple_preferred_drivers(self):
        t_condition = self.env["order.dispatch.condition"].search(
            domain=[("condition", "=", "condition.city.from")]
        )
        t_condition.premise_value = "philippines, cebu city"
        self.setup_rule(
            conditions=[t_condition.id],
            preferred_drivers=[self.driver_2.id, self.driver_1.id],
        )
        self.setup_order(package=self.small_package, customer=self.default_customer)
        picking = self.sale_order.picking_ids[0]
        # Must not auto-assign if multiple preferred drivers
        self.assertNotEqual(self.driver_1.user_id, picking.user_id)
        self.assertNotEqual(self.driver_2.user_id, picking.user_id)

    def test_multiple_rules(self):
        # rule 1: order city from nowhere
        t_condition = self.env["order.dispatch.condition"].search(
            domain=[("condition", "=", "condition.city.from")]
        )
        t_condition.premise_value = (
            "philippines, talisay city"  # No order setup for this address
        )
        self.setup_rule(
            conditions=[t_condition.id], preferred_drivers=[self.driver_2.id]
        )
        # rule 2: but package type should match
        s_condition = self.env["order.dispatch.condition"].search(
            domain=[("condition", "=", PackageTypeMedium.id)]
        )
        self.setup_rule(
            conditions=[t_condition.id, s_condition.id],
            preferred_drivers=[self.driver_1.id],
        )
        self.setup_order(package=self.medium_package, customer=self.default_customer)
        picking = self.sale_order.picking_ids[0]
        # Driver from second condition should be assigned
        self.assertEqual(self.driver_1.user_id, picking.user_id)
