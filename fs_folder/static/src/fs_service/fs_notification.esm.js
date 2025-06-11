import {EventBus} from "@odoo/owl";
import {registry} from "@web/core/registry";

export const fsFolderNotificationService = {
    dependencies: ["bus_service"],
    start(env, {bus_service}) {
        const bus = new EventBus();
        bus_service.subscribe(
            "fs_folder_notification",
            ({res_id, res_model, field_name, type, path}) => {
                bus.trigger(type, {
                    resId: res_id,
                    resModel: res_model,
                    fieldName: field_name,
                    path: path,
                });
            }
        );
        bus_service.start();
        return {
            bus,
        };
    },
};

registry
    .category("services")
    .add("fs_folder_notification", fsFolderNotificationService);
