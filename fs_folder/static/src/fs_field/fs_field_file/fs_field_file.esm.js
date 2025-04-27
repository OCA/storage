import {Component} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
export class FsFieldFile extends Component {
    setup() {
        super.setup();
        this.orm = useService("orm");
    }
    get icon() {
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
}
FsFieldFile.template = "fs_field.FsFieldFile";
FsFieldFile.props = {
    record: Object,
    onClickDelete: Function,
    onCopy: Function,
    onCut: Function,
    onClickDownload: Function,
    onClickPreview: Function,
};
FsFieldFile.components = {};
