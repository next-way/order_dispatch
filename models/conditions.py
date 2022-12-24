"""
Fields of interest

model: sale.order
fields:
- partner_shipping_id (res.partner) Delivery Address
- partner_id (res.partner) Customer

model: stock.picking
fields:
- partner_id (res.partner) Delivery Address
- scheduled_date (datetime) Scheduled date
- weight (float) Weight
- shipping_weight (float) Weight for shipping
- move_type (selection) Shipping Policy
- user_id (res.users) Responsible
- carrier_id (delivery.carrier) Carrier
- carrier_tracking_ref (char) Tracking Reference

model: res.partner
fields:
ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id')

model: delivery.carrier
fields:
- country_ids
- state_ids
- zip_prefix_ids

props/methods:
- _match_address
- available_carriers
- addons.delivery.wizard.choose_delivery_carrier
.ChooseDeliveryCarrier._compute_available_carrier
"""
import logging
from ast import literal_eval
from typing import Protocol

from odoo import _, api

_logger = logging.getLogger(__name__)


class Condition(Protocol):
    content_type: str
    domain: str

    @classmethod
    def get_matches(cls, **kwargs):
        raise NotImplementedError

    @classmethod
    def get_assignee(cls, **kwargs):
        raise NotImplementedError


class BasicMatchMixin:
    @classmethod
    def get_matches(cls, env: api.Environment, **kwargs):
        return env[cls.content_type].search(
            domain=literal_eval(cls.domain),
        )


class BasicAssigneeMixin:
    @classmethod
    def get_assignee(cls, env: api.Environment, **kwargs):
        return env["res.user"]


class PackageTypeSmall:
    id = "condition.package.small"
    label = "Small package"
    domain = "[('weight', '<', 10.0)]"
    content_type = "sale.order"

    @classmethod
    def get_matches(cls, env: api.Environment, **kwargs):
        matching_packages_from_moves = env["stock.move.line"].search(
            [("result_package_id.package_type_id.max_weight", "<=", 10.0)]
        )
        pickings = matching_packages_from_moves.picking_id
        orders = env["sale.order"].search(
            domain=[("picking_ids.id", "in", pickings.ids)]
        )
        return orders


class PackageTypeMedium:
    id = "condition.package.medium"
    label = "Medium package"
    domain = "[('weight', '>=', 10), ('weight', '<', 50)]"
    content_type = "sale.order"

    @classmethod
    def get_matches(cls, env: api.Environment, **kwargs):
        matching_packages_from_moves = env["stock.move.line"].search(
            [
                ("result_package_id.package_type_id.max_weight", ">", 10.0),
                ("result_package_id.package_type_id.max_weight", "<=", 40.0),
            ]
        )
        pickings = matching_packages_from_moves.picking_id
        orders = env["sale.order"].search(
            domain=[("picking_ids.id", "in", pickings.ids)]
        )
        return orders


class OrderCityFrom:
    id = "condition.city.from"
    label = "Order city from"
    domain = "[('city', '=', 'city_from')]"
    premise_help = _(
        "Comma separated value starting with country and followed by the city. "
        "Example: Ireland,Dublin"
    )

    @classmethod
    def get_matches(cls, env: api.Environment, premise_value: str):
        try:
            country, city = list(
                map(lambda x: x.strip().title(), premise_value.split(",", maxsplit=1))
            )
        except (ValueError, AttributeError):
            return
        _logger.info("[.] OrderCityFrom country=(%s) city=(%s)", country, city)
        orders = env["sale.order"].search(
            domain=[
                ("picking_ids.partner_id.country_id.name", "=", country),
                ("picking_ids.partner_id.city", "=", city),
            ]
        )
        return orders


# list of pairs ``(value, label)``, or a model
# method, or a method name.
condition: Condition

ALL_CONDITIONS = [
    PackageTypeSmall,
    PackageTypeMedium,
    OrderCityFrom,
]

CONDITION_SELECTION = [(condition.id, condition.label) for condition in ALL_CONDITIONS]

CONDITION_BY_LABEL = {condition.label: condition for condition in ALL_CONDITIONS}

CONDITION_BY_ID = {condition.id: condition for condition in ALL_CONDITIONS}
