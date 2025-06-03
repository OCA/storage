import {Component} from "@odoo/owl";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {useService} from "@web/core/utils/hooks";

export class FsFolderItem extends Component {
    setup() {
        super.setup();
        this.orm = useService("orm");
    }
    get items() {
        return this.props.moreActionDef
            .filter(
                (item) =>
                    (item.directory && this.props.record.type === "directory") ||
                    (item.file && this.props.record.type === "file")
            )
            .sort((a, b) => {
                if (a.sequence === b.sequence) {
                    return 0;
                }
                return a.sequence < b.sequence ? -1 : 1;
            });
    }
    onClick() {
        if (this.props.record.type === "directory") {
            this.env.onClickDirectory(this.props.record);
        } else {
            this.env.onClickPreview(this.props.record);
        }
    }
}
FsFolderItem.template = "fs_folder.FsFolderItem";
FsFolderItem.props = {
    record: Object,
    fieldDef: Object,
    moreActionDef: Object,
    showField: Function,
};
FsFolderItem.components = {
    Dropdown,
    DropdownItem,
};
