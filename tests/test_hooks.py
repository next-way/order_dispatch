from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestCreateDefaultConditionsDataHook(common.TransactionCase):
    def test_hook_on_setup(self):
        record = self.env["order.dispatch.condition"].search(domain=[])
        self.assertEqual(len(record), 3)
