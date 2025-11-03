import {fields, models} from "@web/../tests/web_test_helpers";

export class ContentgridRecord extends models.ServerModel {
    _name = "contentgrid.record";
    contentgrid_connection_id = fields.Many2one({relation: "contentgrid.connection"});
    res_model = fields.Char();
    res_id = fields.Integer();
    name = fields.Char();
    element = fields.Char();
    data = fields.Json();
}
