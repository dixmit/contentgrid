import {ContentgridConfiguration} from "./mock_models/contentgrid_configuration.esm";
import {ContentgridConnection} from "./mock_models/contentgrid_connection.esm";
import {ContentgridRecord} from "./mock_models/contentgrid_record.esm";
import {IrAttachment} from "./mock_models/ir_attachment.esm";
import {MailThread} from "./mock_models/mail_thread.esm";
import {defineModels} from "@web/../tests/web_test_helpers";
import {mailModels} from "@mail/../tests/mail_test_helpers";

export function defineContentgridModels() {
    defineModels({
        ...mailModels,
        MailThread,
        ContentgridRecord,
        ContentgridConnection,
        ContentgridConfiguration,
        IrAttachment,
    });
}
