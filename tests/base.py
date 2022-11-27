from parameterized import parameterized

from odoo.fields import Command
from odoo.tests import Form, new_test_user

from odoo.addons.sale.tests.common import SaleCommon


def custom_name_func(testcase_func, param_num, param):
    return "%s_%s" % (
        testcase_func.__name__,
        parameterized.to_safe_name("_".join(str(x) for x in param.args)),
    )


class DispatchTestMixin(SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.warehouse = cls.stock_location.warehouse_id

        cls.package_type_small = cls.env["stock.package.type"].create(
            dict(
                name="Small Package",
                height=30.0,
                width=30.0,
                packaging_length=30.0,
                base_weight=0.0,
                max_weight=10.0,
                weight_uom_name="kg",
                length_uom_name="mm",
            )
        )
        cls.small_package = cls.env["stock.quant.package"].create(
            {
                "name": "Pallet 1",
                "package_type_id": cls.package_type_small.id,
            }
        )
        cls.package_type_medium = cls.env["stock.package.type"].create(
            dict(
                name="Medium Package",
                height=50.0,
                width=50.0,
                packaging_length=50.0,
                base_weight=10.1,
                max_weight=40.0,
                weight_uom_name="kg",
                length_uom_name="mm",
            )
        )
        cls.medium_package = cls.env["stock.quant.package"].create(
            {
                "name": "Pallet 2",
                "package_type_id": cls.package_type_medium.id,
            }
        )
        cls.productA = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.productB = cls.env["product.product"].create(
            {"name": "Product B", "type": "product"}
        )

        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.productA.id,
                            "product_uom_qty": 5.0,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.productB.id,
                            "product_uom_qty": 12.0,
                        }
                    ),
                ],
            }
        )

        cls.country_us = cls.env.ref("base.us")
        cls.country_ph = cls.env.ref("base.ph")
        cls.country_ie = cls.env.ref("base.ie")
        # Fleet
        manager = new_test_user(
            cls.env,
            "test fleet manager",
            groups="fleet.fleet_group_manager,base.group_partner_manager",
        )
        cls.driver = new_test_user(cls.env, "driver user", groups="base.group_user")
        cls.driver.partner_id.write(
            {
                "phone": "",
                "email": "",
                "mobile": "",
                "street": "Test street",
                "street2": "Test street2",
                "city": "Cebu City",
                "zip": "6000",
                "state_id": False,
                "country_id": cls.country_ph.id,
            }
        )
        brand = cls.env["fleet.vehicle.model.brand"].create(
            {
                "name": "Suzuki",
            }
        )
        model = cls.env["fleet.vehicle.model"].create(
            {
                "brand_id": brand.id,
                "name": "Carry",
            }
        )
        cls.env["fleet.vehicle"].with_user(manager).create(
            {
                "model_id": model.id,
                "driver_id": cls.driver.partner_id.id,
                "plan_to_change_car": False,
            }
        )

    def setup_order(self, package, customer=None):
        # create picking
        source_package = self.env["stock.quant.package"].create({"name": "Src Pack"})
        dest_package = package  # small_package, medium_package
        picking_form = Form(self.env["stock.picking"])
        picking_form.picking_type_id = self.warehouse.pick_type_id
        if customer:
            picking_form.partner_id = customer
        with picking_form.move_ids_without_package.new() as move_line:
            move_line.product_id = self.productA
            move_line.product_uom_qty = 120
        picking = picking_form.save()
        # HACK: Should be from somewhere else, I think...
        # if customer:
        #     picking.write({"partner_id": customer})
        # HACK: Should be from a purchase order
        self.sale_order.picking_ids = [picking.id]
        picking.action_confirm()
        # Update quantity on hand: 100 units in package
        self.env["stock.quant"]._update_available_quantity(
            self.productA, self.stock_location, 100, package_id=source_package
        )
        # Check Availability
        picking.action_assign()

        self.assertEqual(picking.state, "assigned")
        self.assertEqual(picking.package_level_ids.package_id, source_package)

        move = picking.move_ids
        line = move.move_line_ids

        # change the result package and set a qty_done
        line.qty_done = 100
        line.result_package_id = dest_package

        picking.action_assign()
