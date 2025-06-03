import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

class FsFolderService {
    getData(record, name, path) {
        return rpc(
            `/fs_folder/get_children/${record.resModel}/${record.resId}/${name}`,
            {
                path: path.join("/"),
            }
        );
    }
    uploadFile(record, name, path, file, data) {
        return rpc(`/fs_folder/upload/${record.resModel}/${record.resId}/${name}`, {
            path: path.join("/"),
            name: file.name,
            data: data,
        });
    }
    pasteFile(record, name, path, origin_path, file, move) {
        return rpc(
            `/fs_folder/${move ? "move" : "copy"}/${record.resModel}/${record.resId}/${name}`,
            {
                path: path.join("/"),
                origin_path: origin_path,
                record: file.name,
            }
        );
    }
    getFileUrl(record, name, path, filename, download = 0) {
        var url = new URL(
            `/fs_folder/get_file/${record.resModel}/${record.resId}/${name}`,
            window.location.origin
        );
        url.searchParams.append("path", [...path, filename].join("/"));
        if (download) {
            url.searchParams.append("download", download);
        }
        return url.toString();
    }
    delete(record, name, path, file) {
        return rpc(`/fs_folder/delete/${record.resModel}/${record.resId}/${name}`, {
            path: path.join("/"),
            name: file.name,
        });
    }
    addFolder(record, name, path, folderName) {
        return rpc(`/fs_folder/add_folder/${record.resModel}/${record.resId}/${name}`, {
            path: path.join("/") || "",
            name: folderName,
        });
    }
    rename(record, name, path, oldName, newName) {
        return rpc(`/fs_folder/rename/${record.resModel}/${record.resId}/${name}`, {
            path: path.join("/"),
            name: oldName,
            new_name: newName,
        });
    }
    initialize(record, name) {
        return rpc(
            `/fs_folder/initialize/${record.resModel}/${record.resId}/${name}`,
            {}
        );
    }
}
export const fsFolderService = {
    start() {
        return new FsFolderService();
    },
};

registry.category("services").add("fs.folder", fsFolderService);
