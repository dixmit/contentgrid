import {fields, models} from "@web/../tests/web_test_helpers";

export class ContentgridConnection extends models.ServerModel {
    _name = "contentgrid.connection";
    name = fields.Char();
    _records = [{id: 1, name: "Default Connection"}];
}
