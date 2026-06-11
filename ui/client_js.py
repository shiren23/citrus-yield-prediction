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

APP_JS = """
() => {
    if (window.__citrusJsVersion === 12) return;
    window.__citrusJsVersion = 12;
    function queryAll(selector) {
        const found = [];
        const visit = (root) => {
            if (!root) return;
            root.querySelectorAll(selector).forEach((el) => found.push(el));
            root.querySelectorAll('*').forEach((el) => {
                if (el.shadowRoot) visit(el.shadowRoot);
            });
        };
        visit(document);
        const app = document.querySelector('gradio-app');
        if (app && app.shadowRoot) visit(app.shadowRoot);
        return found;
    }
    function findHistDeleteSubmit() {
        const wraps = queryAll('#hist_delete_submit, .hist-delete-submit');
        for (const wrap of wraps) {
            if (wrap.tagName === 'BUTTON') return wrap;
            const btn = wrap.querySelector('button');
            if (btn) return btn;
        }
        return queryAll('#hist_delete_submit button, .hist-delete-submit button')[0] || null;
    }
    window.triggerHistDelete = function(id) {
        if (id == null || id === '') return;
        window.__histDeletePendingId = String(id);
        const submit = findHistDeleteSubmit();
        if (submit) submit.click();
    };
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-hist-delete]');
        if (!btn) return;
        e.preventDefault();
        e.stopPropagation();
        window.triggerHistDelete(btn.getAttribute('data-hist-delete'));
    }, true);
    function clickNativeMediaFileRemove() {
        const root = document.getElementById('citrus_media_input');
        const scopes = root ? [root] : [];
        queryAll('.media-upload-box').forEach((el) => scopes.push(el));
        scopes.forEach((scope) => {
            scope.querySelectorAll('button').forEach((btn) => {
                const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                const title = (btn.getAttribute('title') || '').toLowerCase();
                const text = (btn.textContent || '').trim();
                if (
                    label.includes('remove') || label.includes('clear') || label.includes('delete')
                    || label.includes('删除') || label.includes('移除')
                    || title.includes('remove') || title.includes('clear')
                    || text === '×' || text === '✕' || text === 'x'
                ) {
                    btn.click();
                }
            });
        });
    }
    document.addEventListener('click', (e) => {
        if (e.target.closest('#citrus_clear_media, .media-clear-trigger')) {
            setTimeout(clickNativeMediaFileRemove, 80);
        }
    }, true);
}
"""
