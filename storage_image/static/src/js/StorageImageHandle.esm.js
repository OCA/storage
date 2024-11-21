import {registry} from "@web/core/registry";
import {X2ManyField, x2ManyField} from "@web/views/fields/x2many/x2many_field";
import {KanbanRenderer} from "@web/views/kanban/kanban_renderer";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

export class StorageImageKanbanRenderer extends KanbanRenderer {
    setup() {
        super.setup();
        this.notification = useService("notification");
    }
    async sortRecordDrop(dataRecordId, dataGroupId, {element, parent, previous}) {
        await super.sortRecordDrop(dataRecordId, dataGroupId, {
            element,
            parent,
            previous,
        });
        this.notification.add(_t("Records have been successfully rearranged."), {
            type: "success",
        });
    }
}

export class StorageImageHandle extends X2ManyField {
    static components = {
        ...X2ManyField.components,
        KanbanRenderer: StorageImageKanbanRenderer,
    };
}

export const storageImageHandle = {
    ...x2ManyField,
    component: StorageImageHandle,
    additionalClasses: [...(x2ManyField.additionalClasses || []), "o_field_one2many"],
};

registry.category("fields").add("storage_image_handle", storageImageHandle);
