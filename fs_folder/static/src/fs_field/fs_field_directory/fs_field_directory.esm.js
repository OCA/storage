import {Component} from "@odoo/owl";
export class FsFieldDirectory extends Component {}
FsFieldDirectory.template = "fs_field.FsFieldDirectory";
FsFieldDirectory.props = {
    record: Object,
    onClickDelete: Function,
    onCopy: Function,
    onCut: Function,
    onClick: Function,
};
FsFieldDirectory.components = {};
