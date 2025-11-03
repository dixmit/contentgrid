import {fields, models} from "@web/../tests/web_test_helpers";

export class ContentgridConfiguration extends models.ServerModel {
    _name = "contentgrid.configuration";
    connection_id = fields.Many2one({relation: "contentgrid.connection"});
    model_id = fields.Many2one({relation: "ir.model"});
    active = fields.Boolean({default: true});
    allow_manual_send = fields.Boolean({default: false});
}
