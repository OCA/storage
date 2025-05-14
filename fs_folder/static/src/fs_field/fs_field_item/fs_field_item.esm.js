import {Component} from "@odoo/owl";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {useService} from "@web/core/utils/hooks";

export class FsFieldItem extends Component {
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
    get icon() {
        if (this.props.record.type === "directory") {
            return "fa-folder";
        }
        const filename = this.props.record.name;
        const extensionStartPosition = filename.lastIndexOf(".");
        if (extensionStartPosition === -1) {
            return "fa-file-o";
        }
        const extension = filename.slice(extensionStartPosition + 1);
        switch (extension.toLowerCase()) {
            case "aac":
            case "ogg":
            case "mp3":
                return "fa-file-audio-o";
            case "avi":
            case "flv":
            case "mkv":
            case "mp4":
                return "fa-file-video-o";
            case "css":
            case "html":
            case "js":
                return "fa-file-code-o";
            case "csv":
                return "fa-file-csv-o";
            case "doc":
            case "docx":
                return "fa-file-word-o";
            case "gif":
            case "jpeg":
            case "jpg":
            case "png":
                return "fa-file-image-o";
            case "gz":
            case "zip":
            case "archive":
                return "fa-file-archive-o";
            case "pdf":
                return "fa-file-pdf-o";
            case "ppt":
            case "pptx":
                return "fa-file-powerpoint-o";
            case "txt":
            case "text":
                return "fa-file-alt-o";
            case "xls":
            case "xlsx":
                return "fa-file-excel-o";
            case "audio":
                return "fa-file-audio-o";
            case "code":
                return "fa-file-code-o";
            case "image":
                return "fa-file-image-o";
            case "excel":
                return "fa-file-excel-o";
            case "powerpoint":
                return "fa-file-powerpoint-o";
            case "video":
                return "fa-file-video-o";
            case "word":
                return "fa-file-word-o";
            default:
                return "fa-file-o";
        }
    }
    onClick() {
        if (this.props.record.type === "directory") {
            this.env.onClickDirectory(this.props.record);
        } else {
            this.env.onClickPreview(this.props.record);
        }
    }
}
FsFieldItem.template = "fs_field.FsFieldItem";
FsFieldItem.props = {
    record: Object,
    fieldDef: Object,
    moreActionDef: Object,
};
FsFieldItem.components = {
    Dropdown,
    DropdownItem,
};
