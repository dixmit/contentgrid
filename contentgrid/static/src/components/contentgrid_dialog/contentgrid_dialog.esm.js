import {Component, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";

export class ContentGridDialog extends Component {
    setup() {
        super.setup();
        this.state = useState({
            currentTab: this.props.data[0].id,
        });
    }
    get multiRecords() {
        return this.props.data.length > 1;
    }
    get title() {
        return "Content Grid";
    }
    get currentRecord() {
        return this.props.data.find((item) => item.id === this.state.currentTab);
    }
    onClickContentGridTab(item) {
        this.state.currentTab = item.id;
    }
    onClickContentGridRecord() {
        window.open(this.currentRecord.url, "_blank");
    }
}

ContentGridDialog.components = {Dialog};
ContentGridDialog.template = "contentgrid.ContentGridDialog";
ContentGridDialog.props = {
    data: {type: Object},
    close: Function,
};
