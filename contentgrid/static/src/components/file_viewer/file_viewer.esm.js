import {ContentGridDialog} from "../contentgrid_dialog/contentgrid_dialog.esm";
import {FileViewer} from "@web/core/file_viewer/file_viewer";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

patch(FileViewer.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
    },
    async onClickContentGrid() {
        const contentgrid_data = await this.orm.call(
            "ir.attachment",
            "get_contentgrid_data",
            [this.state.file.id]
        );
        this.dialog.add(ContentGridDialog, {data: contentgrid_data});
    },
});
