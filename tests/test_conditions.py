from parameterized import parameterized

from odoo.tests import common, tagged

from ..models.conditions import PackageTypeMedium, PackageTypeSmall
from .base import DispatchTestMixin, custom_name_func


@tagged("-at_install", "post_install")
class TestDefaultConditions(DispatchTestMixin, common.TransactionCase):
    @parameterized.expand(
        [
            (PackageTypeSmall, "small_package"),
            (PackageTypeMedium, "medium_package"),
        ],
        name_func=custom_name_func,
    )
    def test_package_type_creates_dispatch(self, package_type, package_attr):
        # diagnostic
        t_condition = self.env["order.dispatch.condition"].search(
            domain=[("condition", "=", package_type.id)]
        )
        self.assertEqual(1, len(t_condition))
        matches = t_condition.get_matches().ids
        self.assertNotIn(self.sale_order.id, matches)

        self.setup_order(package=getattr(self, package_attr))

        # assert
        matches = t_condition.get_matches().ids
        self.assertIn(self.sale_order.id, matches)

    def test_order_address(self):
        t_condition = self.env["order.dispatch.condition"].search(
            domain=[("condition", "=", "condition.city.from")]
        )
        t_condition.premise_value = "philippines, cebu city"
        self.assertEqual(1, len(t_condition))
        matches = t_condition.get_matches().ids
        self.assertNotIn(self.sale_order.id, matches)

        # Address
        contact = self.env["res.partner"].create(
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
        self.setup_order(package=self.small_package, customer=contact)

        matches = t_condition.get_matches().ids
        self.assertIn(self.sale_order.id, matches)

    def test_order_address_city_same_name_but_not_the_same_country(self):
        t_condition = self.env["order.dispatch.condition"].search(
            domain=[("condition", "=", "condition.city.from")]
        )
        t_condition.premise_value = "ireland, dublin"
        self.assertEqual(1, len(t_condition))
        matches = t_condition.get_matches().ids
        self.assertNotIn(self.sale_order.id, matches)

        # Address
        contact = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "phone": "",
                "email": "",
                "mobile": "",
                "street": "Test street",
                "street2": "Test street2",
                "city": "Dublin",  # Same city name
                "zip": "6000",
                "state_id": False,
                "country_id": self.country_us.id,  # Different country
            }
        )
        self.setup_order(package=self.small_package, customer=contact)

        matches = t_condition.get_matches().ids
        self.assertNotIn(self.sale_order.id, matches)
