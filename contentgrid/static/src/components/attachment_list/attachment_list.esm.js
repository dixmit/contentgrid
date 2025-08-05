import {AttachmentList} from "@mail/core/common/attachment_list";
import {ContentGridDialog} from "../contentgrid_dialog/contentgrid_dialog.esm";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

patch(AttachmentList.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
    },
    async onClickAttachmentContentGrid(attachment) {
        const contentgrid_data = await this.orm.call(
            "ir.attachment",
            "get_contentgrid_data",
            [attachment.id]
        );
        this.dialog.add(ContentGridDialog, {data: contentgrid_data});
    },
});
