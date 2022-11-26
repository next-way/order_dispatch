# import pytest
#
# import odoo
#
#
# @pytest.fixture(scope="session")
# def env():
#     # arrange
#     db_name = odoo.tests.common.get_db_name()
#     registry = odoo.registry(db_name)
#     cr = registry.cursor()
#     env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
#     yield env
#     # cleanup
#     registry.reset_changes()
#     registry.clear_caches()
#     env.flush_all()
#     cr.rollback()
#     cr.close()
#
#
# @pytest.fixture
# def small_package_type(env):
#     package_type = env["stock.package.type"].create(
#         [
#             dict(
#                 name="Small Package",
#                 height=30.0,
#                 width=30.0,
#                 packaging_length=30.0,
#                 base_weight=0.0,
#                 max_weight=10.0,
#                 weight_uom_name="kg",
#                 length_uom_name="mm",
#             )
#         ]
#     )
#     return package_type
#
#
# @pytest.fixture
# def small_package(env, small_package_type):
#     package = env["stock.quant.package"].create(
#         [
#             dict(
#                 package_type_id=small_package_type,
#                 package_use="disposable",
#             )
#         ]
#     )
#     return package
#
#
# @pytest.fixture
# def small_package_order(env, small_package):
#     package_type
#     env[""]
