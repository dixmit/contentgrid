import {Chatter} from "@mail/chatter/web_portal/chatter";
import {ContentGridDialog} from "../contentgrid_dialog/contentgrid_dialog.esm";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
    },
    async onClickContentGrid() {
        const contentgrid_data = await this.orm.call(
            this.state.thread.model,
            "get_contentgrid_data",
            [this.state.thread.id]
        );
        this.dialog.add(ContentGridDialog, {data: contentgrid_data});
    },
    async oClickSendContentGrid() {
        await this.orm.call(this.state.thread.model, "send_contentgrid_data", [
            this.state.thread.id,
        ]);
    },
});
