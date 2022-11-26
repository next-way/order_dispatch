import logging

from odoo import SUPERUSER_ID, api

from ..models.conditions import CONDITION_BY_LABEL, CONDITION_SELECTION

_logger = logging.getLogger(__name__)


def create_default_conditions_data(cr, registry):
    """Add default conditions data"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    condition_labels = [selection[1] for selection in CONDITION_SELECTION]
    existing_conditions = (
        env["order.dispatch.condition"]
        .search(domain=[("name", "in", condition_labels)])
        .read(["name"])
    )
    missing_conditions_names = set(condition_labels) - {
        e_condition["name"] for e_condition in existing_conditions
    }
    # Create missing condition (on cold start, all conditions are to be created)
    created_conditions = env["order.dispatch.condition"].create(
        [
            {
                "name": condition_name,
                "domain": CONDITION_BY_LABEL[condition_name].domain,
                "condition": CONDITION_BY_LABEL[condition_name].id,
            }
            for condition_name in missing_conditions_names
        ]
    )
    _logger.info(f"Existing conditions: {len(existing_conditions)}")
    _logger.info(f"Missing conditions: {len(missing_conditions_names)}")
    _logger.info(f"Created conditions: {len(created_conditions)}")
