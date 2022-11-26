{
    "name": "Dispatch",
    "summary": "Dispatch for sale orders",
    "author": "Nextway",
    "website": "https://next-way.org",
    "license": "AGPL-3",
    "category": "Inventory/Delivery",
    "version": "16.0.0.0.1",
    # any module necessary for this one to work correctly
    "depends": ["delivery", "sale", "stock"],
    "post_init_hook": "create_default_conditions_data",
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/dispatch_rule_view.xml",
        "views/dispatch_rule_menu.xml",
    ],
    # only loaded in demonstration mode
    # "demo": [
    #     "demo/demo.xml",
    # ],
}
