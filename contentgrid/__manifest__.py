# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Contentgrid",
    "summary": """Integrate your Attachments with ContentGrid""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Dixmit",
    "website": "https://github.com/dixmit/contentgrid",
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/contentgrid_connection.xml",
        "views/contentgrid_configuration.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "contentgrid/static/src/**/*.esm.js",
            "contentgrid/static/src/**/*.xml",
            "contentgrid/static/src/**/*.css",
        ],
    },
    "demo": [],
}
