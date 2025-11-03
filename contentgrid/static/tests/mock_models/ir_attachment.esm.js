import {getKwArgs} from "@web/../tests/web_test_helpers";
import {mailModels} from "@mail/../tests/mail_test_helpers";

export class IrAttachment extends mailModels.IrAttachment {
    _to_store() {
        const kwargs = getKwArgs(arguments, "ids", "store", "fields");
        const store = kwargs.store;
        var result = super._to_store(...arguments);
        const id = kwargs.ids[0];
        store.add(this.browse(id), {
            contentgrid: Boolean(
                this.env["contentgrid.record"].search([
                    ["res_model", "=", this._name],
                    ["res_id", "=", id],
                ]).length
            ),
        });
        return result;
    }

    get_contentgrid_data(ids) {
        const records = this.env["contentgrid.record"].search([
            ["res_model", "=", this._name],
            ["res_id", "in", ids],
        ]);
        const result = [];
        for (const recordId of records) {
            const record = this.env["contentgrid.record"].browse(recordId)[0];
            result.push({
                id: record.id,
                name: record.name,
                element: record.element,
                contentgrid_connection: record.contentgrid_connection_id,
                data: record.data,
                url: "/contentgrid/record/" + record.id,
            });
        }
        return result;
    }
}
