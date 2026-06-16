"""Client JS."""

# Gradio 6：在 Python 删除函数执行前注入表格行点击的记录 ID
HIST_DELETE_PREPROCESS_JS = """
(recordId, orchard, stage, period) => {
    const id = String((window.__histDeletePendingId != null && window.__histDeletePendingId !== '')
        ? window.__histDeletePendingId : (recordId || '')).trim();
    window.__histDeletePendingId = null;
    return [id, orchard, stage, period];
}
"""

ORCHARD_EDIT_PREPROCESS_JS = """
(orchardId, orchardName, orchardTrees) => {
    const id = String((window.__orchardEditPendingId != null && window.__orchardEditPendingId !== '')
        ? window.__orchardEditPendingId : (orchardId || '')).trim();
    const name = String((window.__orchardEditPendingName != null && window.__orchardEditPendingName !== '')
        ? window.__orchardEditPendingName : (orchardName || '')).trim();
    const trees = String((window.__orchardEditPendingTrees != null && window.__orchardEditPendingTrees !== '')
        ? window.__orchardEditPendingTrees : (orchardTrees || '')).trim();
    window.__orchardEditPendingId = null;
    window.__orchardEditPendingName = null;
    window.__orchardEditPendingTrees = null;
    return [id, name, trees];
}
"""

ORCHARD_DELETE_PREPROCESS_JS = """
(orchardId, orchardName) => {
    const id = String((window.__orchardDeletePendingId != null && window.__orchardDeletePendingId !== '')
        ? window.__orchardDeletePendingId : (orchardId || '')).trim();
    const name = String((window.__orchardDeletePendingName != null && window.__orchardDeletePendingName !== '')
        ? window.__orchardDeletePendingName : (orchardName || '')).trim();
    window.__orchardDeletePendingId = null;
    window.__orchardDeletePendingName = null;
    return [id, name];
}
"""

APP_JS = """
(() => {
    if (window.__citrusJsVersion === 18) return;
    window.__citrusJsVersion = 18;

    const safeDebug = () => {};
    window.citrusDebug = safeDebug;

    function findInRoots(selector) {
        const roots = [document];
        const app = document.querySelector('gradio-app');
        if (app && app.shadowRoot) roots.push(app.shadowRoot);
        for (const root of roots) {
            const el = root.querySelector(selector);
            if (el) return el;
        }
        return null;
    }

    function setComponentValue(selector, value) {
        const root = findInRoots(selector);
        if (!root) return false;
        const el = root.matches?.('input, textarea') ? root : root.querySelector('input, textarea');
        if (!el) return false;
        const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
        if (setter) setter.call(el, String(value ?? ''));
        else el.value = String(value ?? '');
        el.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
        el.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
        return true;
    }

    window.triggerHistDelete = function(id) {
        const recordId = String(id || '').trim();
        window.__histDeletePendingId = recordId;
        setComponentValue('#hist_delete_id, .hist-delete-id-input', recordId);
        return true;
    };

    window.triggerOrchardEdit = function(id, name, trees) {
        const orchardId = String(id || '').trim();
        window.__orchardEditPendingId = orchardId;
        window.__orchardEditPendingName = String(name || '');
        window.__orchardEditPendingTrees = String(trees || '');
        setComponentValue('#orchard_edit_id, .orchard-edit-id-input', orchardId);
        setComponentValue('#orchard_edit_name, .orchard-edit-name-input', name || '');
        setComponentValue('#orchard_edit_trees, .orchard-edit-trees-input', trees || '');
        return true;
    };

    window.triggerOrchardDelete = function(id, name) {
        const orchardId = String(id || '').trim();
        window.__orchardDeletePendingId = orchardId;
        window.__orchardDeletePendingName = String(name || '');
        setComponentValue('#orchard_delete_name, .orchard-delete-name-input', name || '');
        setTimeout(() => setComponentValue('#orchard_delete_id, .orchard-delete-id-input', orchardId), 0);
        return true;
    };

    function attrFromPath(e, attr) {
        const path = typeof e.composedPath === 'function' ? e.composedPath() : [];
        for (const n of path) {
            if (n && n.getAttribute && n.getAttribute(attr) != null) return n;
        }
        return e.target?.closest?.('[' + attr + ']') || null;
    }

    if (!window.__citrusClickBound) {
        window.__citrusClickBound = true;
        document.addEventListener('click', (e) => {
            const editBtn = attrFromPath(e, 'data-orchard-edit');
            if (editBtn) {
                e.preventDefault();
                e.stopPropagation();
                window.triggerOrchardEdit(
                    editBtn.getAttribute('data-orchard-edit'),
                    editBtn.getAttribute('data-orchard-name'),
                    editBtn.getAttribute('data-orchard-trees')
                );
                return;
            }
            const delBtn = attrFromPath(e, 'data-orchard-delete');
            if (delBtn) {
                e.preventDefault();
                e.stopPropagation();
                window.triggerOrchardDelete(
                    delBtn.getAttribute('data-orchard-delete'),
                    delBtn.getAttribute('data-orchard-name')
                );
                return;
            }
            const histBtn = attrFromPath(e, 'data-hist-delete');
            if (histBtn) {
                e.preventDefault();
                e.stopPropagation();
                window.triggerHistDelete(histBtn.getAttribute('data-hist-delete'));
            }
        }, true);
    }
})();
"""
