import {PreviewIframe} from "./preview_iframe.esm";
import {onWillDestroy} from "@odoo/owl";
import {registry} from "@web/core/registry";

let id = 1;

export function createPreviewIframeViewer() {
    const previewIframeViwerId = `fs_conent.preview_iframe_${id++}`;

    function close() {
        registry.category("main_components").remove(previewIframeViwerId);
    }

    /**
     * @param {String} url
     */
    function open(url) {
        registry.category("main_components").add(previewIframeViwerId, {
            Component: PreviewIframe,
            props: {url, onClose: close},
        });
    }

    return {open, close};
}

export function usePreviewIframeViewer() {
    const {open, close} = createPreviewIframeViewer();
    onWillDestroy(close);
    return {open, close};
}
