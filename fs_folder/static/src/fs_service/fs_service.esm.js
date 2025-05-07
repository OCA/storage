import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

class FsFieldService {
    getData(record, name, path) {
        return rpc(
            `/fs_field/get_children/${record.resModel}/${record.resId}/${name}`,
            {
                path: path.join("/"),
            }
        );
    }
    uploadFile(record, name, path, file, data) {
        return rpc(`/fs_field/upload/${record.resModel}/${record.resId}/${name}`, {
            path: path.join("/"),
            name: file.name,
            data: data,
        });
    }
    pasteFile(record, name, path, origin_path, file, move) {
        return rpc(
            `/fs_field/${move ? "move" : "copy"}/${record.resModel}/${record.resId}/${name}`,
            {
                path: path.join("/"),
                origin_path: origin_path,
                record: file.name,
            }
        );
    }
    getFileUrl(record, name, path, filename, download = 0) {
        var url = new URL(
            `/fs_field/get_file/${record.resModel}/${record.resId}/${name}`,
            window.location.origin
        );
        url.searchParams.append("path", [...path, filename].join("/"));
        if (download) {
            url.searchParams.append("download", download);
        }
        return url.toString();
    }
    delete(record, name, path, file) {
        return rpc(`/fs_field/delete/${record.resModel}/${record.resId}/${name}`, {
            path: path.join("/"),
            name: file.name,
        });
    }
    addFolder(record, name, path, folderName) {
        return rpc(`/fs_field/add_folder/${record.resModel}/${record.resId}/${name}`, {
            path: path.join("/") || "",
            name: folderName,
        });
    }
    initialize(record, name) {
        return rpc(
            `/fs_field/initialize/${record.resModel}/${record.resId}/${name}`,
            {}
        );
    }
}
export const fsFieldService = {
    start() {
        return new FsFieldService();
    },
};

registry.category("services").add("fs.field", fsFieldService);
