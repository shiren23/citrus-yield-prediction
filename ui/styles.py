"""Global CSS."""

GLOBAL_CSS = """
.gradio-container {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 24px 32px !important;
    background: #f1f5f9 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    font-size: 14px !important;
    color: #334155 !important;
}
main.contain, .app, .wrap.svelte-zxu34v, .gradio-container > .main {
    width: 100% !important;
    max-width: 100% !important;
}
.tabitem, .tabs, .row, .column, .form {
    width: 100% !important;
    max-width: 100% !important;
}
footer, .gradio-footer, .built-with { display: none !important; }

/* ===== 加载状态：单一圆环，隐藏多处 processing 图标 ===== */
.progress-text,
.meta-text-center,
.timer,
.footer-bar,
.status-tracker,
[data-testid="status-display"],
.wrap .loader,
.block .loader,
.generating .icon-loading,
.generating .loading {
    display: none !important;
    visibility: hidden !important;
}
.generating {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    animation: none !important;
}
.block.html.generating,
.block.markdown.generating,
.form .block.generating:not(.predict-result-image):not(.predict-chart-image) {
    opacity: 1 !important;
    filter: none !important;
}
.block.html.generating::before,
.block.html.generating::after,
.block.markdown.generating::before,
.block.markdown.generating::after,
.form .block.generating:not(.predict-result-image):not(.predict-chart-image)::before,
.form .block.generating:not(.predict-result-image):not(.predict-chart-image)::after {
    display: none !important;
    content: none !important;
}
.predict-result-image.generating,
.predict-chart-image.generating {
    position: relative !important;
}
.predict-result-image.generating .image-container,
.predict-result-image.generating .container,
.predict-chart-image.generating .image-container,
.predict-chart-image.generating .container {
    position: relative !important;
    min-height: 160px !important;
}
.predict-result-image.generating .image-container::before,
.predict-result-image.generating .container::before,
.predict-chart-image.generating .image-container::before,
.predict-chart-image.generating .container::before {
    content: "正在分析，请稍候…" !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding-top: 72px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #2563eb !important;
    letter-spacing: 0.02em !important;
    position: absolute !important;
    inset: 0 !important;
    background: rgba(255, 255, 255, 0.82) !important;
    border-radius: 6px !important;
    z-index: 10 !important;
    pointer-events: none !important;
}
.predict-result-image.generating .image-container::after,
.predict-result-image.generating .container::after,
.predict-chart-image.generating .image-container::after,
.predict-chart-image.generating .container::after {
    content: "" !important;
    display: block !important;
    position: absolute !important;
    top: calc(50% - 18px) !important;
    left: 50% !important;
    width: 56px !important;
    height: 56px !important;
    margin: -28px 0 0 -28px !important;
    border: 4px solid #dbeafe !important;
    border-top-color: #2563eb !important;
    border-radius: 50% !important;
    animation: citrus-spin 0.75s linear infinite !important;
    z-index: 11 !important;
    pointer-events: none !important;
    background: transparent !important;
    box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.08) !important;
}
@keyframes citrus-spin {
    to { transform: rotate(360deg); }
}

.page-header {
    text-align: center;
    padding: 18px 24px;
    margin: 0 -24px 20px;
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    width: calc(100% + 48px) !important;
}
.page-header h1 {
    font-size: 18px;
    font-weight: 700;
    color: #1e293b;
    margin: 0;
    letter-spacing: 0.02em;
}
.page-header p {
    font-size: 12px;
    color: #64748b;
    margin: 6px 0 0;
}

.app-card {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    padding: 20px !important;
    margin-bottom: 16px !important;
    gap: 12px !important;
    overflow: visible !important;
}
.form-stack, .column, .row-compact, .tabitem {
    overflow: visible !important;
}
.card-title {
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 4px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #f1f5f9;
}
.field-label {
    font-size: 13px;
    font-weight: 500;
    color: #475569;
    margin: 0 0 6px 0;
    line-height: 1.4;
}
.hint-text {
    font-size: 12px;
    color: #64748b;
    margin: 0;
    line-height: 1.5;
}
.form-stack { gap: 12px !important; }

.app-card .form,
.app-card.form,
.form-stack .form,
.tabitem .form,
.column .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    gap: 12px !important;
    padding: 0 !important;
}
.app-card .block,
.form-stack .block,
.tabitem .block.padded {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 0 12px 0 !important;
}
.app-card .block:last-child,
.form-stack .block:last-child { margin-bottom: 0 !important; }
.label-wrap, .block-label {
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: 0 !important;
}
.icon-wrap, .label-icon { display: none !important; }
.upload-box .icon-button,
.upload-box .icon-wrap,
.upload-box .source-selection,
.upload-box .button-row,
.upload-box .image-buttons,
.upload-box .footer,
.upload-box .toolbar-wrap,
.upload-box .tool-buttons {
    display: none !important;
}
/* 文本/数字：单层边框在 wrap 上（当组件存在 wrap 容器时使用该规则） */
.field-input .wrap input,
.field-input .wrap textarea,
.field-input .wrap select {
    border: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    background-image: none !important;
    font-size: 14px !important;
    color: #334155 !important;
    box-shadow: none !important;
    filter: none !important;
    min-height: 32px !important;
    line-height: 1.35 !important;
    padding: 5px 10px !important;
}

/* 页面内提示条（用于果园管理等场景的操作反馈） */
.inline-alert {
    margin: 8px 0 0 0;
    padding: 12px 14px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 14px;
    line-height: 1.45;
    border: 1px solid transparent;
}
.inline-alert.inline-alert-success {
    background: #f0fdf4;
    color: #15803d;
    border-color: #bbf7d0;
}
.inline-alert.inline-alert-error {
    background: #fef2f2;
    color: #b91c1c;
    border-color: #fecaca;
}
.inline-alert { display: none !important; }

/* 补充：确保所有常见输入控件在视觉上一致，有浅色外框便于识别 */
.gradio-container input[type="text"],
.gradio-container input[type="number"],
.gradio-container textarea,
.gradio-container select {
    border: 1px solid #e6eef8 !important;
    border-radius: 6px !important;
    padding: 6px 10px !important;
    background: #ffffff !important;
    box-shadow: none !important;
    color: #334155 !important;
}

.gradio-container input[type="text"]:focus,
.gradio-container input[type="number"]:focus,
.gradio-container textarea:focus,
.gradio-container select:focus {
    outline: none !important;
    border-color: #93c5fd !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.06) !important;
}
/* 文本/数字：边框在 wrap（下拉框用 Gradio 原生样式，避免破坏 fixed 选项层）
   增强：输入/输出框增加外框并使用更浅色，以便用户快速识别可输入区域 */
.field-input:not(.dropdown-field) .wrap {
    border: 1px solid #e6eef8 !important; /* 更浅的边框颜色 */
    border-radius: 6px !important;
    background: #ffffff !important;
    background-image: none !important;
    box-shadow: none !important;
    filter: none !important;
    min-height: 32px !important;
    padding: 0 !important;
    overflow: visible !important;
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
}

/* 下拉框外层也加外框，风格统一 */
.dropdown-field .wrap {
    border: 1px solid #e6eef8 !important;
    border-radius: 6px !important;
    padding: 0 !important;
}

/* 焦点态更醒目但仍保持轻微 */
.field-input:not(.dropdown-field) .wrap:focus-within,
.dropdown-field .wrap:focus-within {
    border-color: #93c5fd !important; /* 轻蓝色高亮 */
    box-shadow: 0 4px 12px rgba(37,99,235,0.06) !important;
}
/* 下拉：仅去掉 block 外层多余间距，不覆盖 .wrap / ul.options */
.dropdown-field.block,
.dropdown-field .block,
.dropdown-field .form,
.dropdown-field .label-wrap {
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}
/* 下拉：Gradio6 用 mousedown 时读取 event.target.dataset.index，须让点击落在 li 上 */
ul.options li[data-index],
ul.options li.item {
    pointer-events: auto !important;
    cursor: pointer !important;
}
ul.options li[data-index] > *,
ul.options li.item > * {
    pointer-events: none !important;
}
.dropdown-field .label-wrap,
.dropdown-field .block-label {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #475569 !important;
    margin: 0 0 6px 0 !important;
    padding: 0 !important;
}
.stage-choice .wrap {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
}
.stage-choice label {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 10px 12px !important;
    margin: 0 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    background: #ffffff !important;
    cursor: pointer !important;
    font-size: 14px !important;
    line-height: 1.45 !important;
}
.stage-choice label:hover {
    border-color: #2563eb !important;
    background: #f8fafc !important;
}
.stage-choice input {
    margin: 0 !important;
    accent-color: #2563eb !important;
}
.field-input:not(.dropdown-field) input:focus,
.field-input:not(.dropdown-field) textarea:focus,
.field-input:not(.dropdown-field) .wrap:focus-within {
    border-color: #2563eb !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.12) !important;
}
/* 关联历史预测记录：选项文字样式 */
.record-select ul.options li,
.record-select [role="option"] {
    font-weight: 400 !important;
    font-size: 13px !important;
    padding: 8px 12px !important;
    line-height: 1.4 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    min-height: unset !important;
}
.record-select .wrap [role="combobox"] {
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}

.upload-box .image-container,
.upload-box .container,
.upload-box .video-container {
    border: 1px dashed #cbd5e1 !important;
    border-radius: 6px !important;
    background: #fafbfc !important;
    min-height: 130px !important;
    transition: border-color 0.15s, background 0.15s !important;
}
.upload-box .image-container:hover,
.upload-box .container:hover {
    border-color: #2563eb !important;
    background: #f8fafc !important;
}
.upload-box .icon-button,
.upload-box .source-selection,
.upload-box .icon-wrap,
.upload-box .button-row,
.upload-box .image-buttons,
.upload-box .footer,
.upload-box .toolbar-wrap,
.upload-box .tool-buttons {
    display: none !important;
}
.upload-box .empty,
.upload-box .upload-text {
    font-size: 13px !important;
    color: #64748b !important;
}
.media-upload-box .wrap,
.media-upload-box .file-preview,
.media-upload-box .upload-container,
.media-upload-box .container,
.media-upload-box .upload-area {
    border: 1px dashed #cbd5e1 !important;
    border-radius: 6px !important;
    background: #fafbfc !important;
    background-image: none !important;
    box-shadow: none !important;
    filter: none !important;
    min-height: 120px !important;
    padding: 16px 12px !important;
    transition: border-color 0.15s, background 0.15s !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}
.media-upload-box .wrap:hover,
.media-upload-box .upload-container:hover,
.media-upload-box .upload-area:hover {
    border-color: #2563eb !important;
    background: #f8fafc !important;
}
.media-upload-box .file-name,
.media-upload-box label,
.media-upload-box .upload-text,
.media-upload-box .empty,
.media-upload-box p,
.media-upload-box span {
    font-size: 12px !important;
    line-height: 1.6 !important;
    color: #64748b !important;
    margin: 0 !important;
    white-space: normal !important;
    word-break: break-word !important;
}
.media-upload-box .file-preview {
    min-height: auto !important;
    padding: 10px 12px !important;
    justify-content: flex-start !important;
    text-align: left !important;
}
.media-upload-box button,
.media-upload-box .icon-button,
.media-upload-box .x-button {
    display: inline-flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
}
.media-clear-row {
    margin-top: 4px !important;
}
.media-clear-row button {
    width: auto !important;
    min-height: 34px !important;
    padding: 6px 14px !important;
    font-size: 13px !important;
    color: #dc2626 !important;
    background: #ffffff !important;
    border: 1px solid #fecaca !important;
    border-radius: 6px !important;
}
.media-clear-row button:hover {
    background: #fef2f2 !important;
    border-color: #fca5a5 !important;
}
.media-preview-wrap {
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    background: #f8fafc !important;
    overflow: hidden !important;
    min-height: 220px !important;
}
.media-preview-wrap .image-container,
.media-preview-wrap .video-container,
.media-preview-wrap .container {
    min-height: 220px !important;
    background: #f8fafc !important;
}
.media-preview-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 220px;
    color: #94a3b8;
    font-size: 13px;
    border: 1px dashed #cbd5e1;
    border-radius: 6px;
    background: #fafbfc;
}

.btn-row { gap: 10px !important; align-items: center !important; margin-top: 4px !important; }
.btn-row > .block { flex: 1 !important; margin: 0 !important; }
.btn-row .form { gap: 10px !important; flex-direction: row !important; }
.btn-row button {
    width: 100% !important;
    min-height: 38px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}
.btn-row button.primary {
    background: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #2563eb !important;
}
.btn-row button.primary:hover {
    background: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
}
.btn-row button.secondary {
    background: #ffffff !important;
    color: #334155 !important;
    border: 1px solid #e2e8f0 !important;
}
.btn-row button.secondary:hover {
    background: #f8fafc !important;
    border-color: #cbd5e1 !important;
}
.btn-full button {
    width: 100% !important;
    min-height: 38px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
}
.btn-full button.primary {
    background: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #2563eb !important;
}
.btn-danger-wrap button {
    background: #ffffff !important;
    color: #dc2626 !important;
    border: 1px solid #fecaca !important;
    border-radius: 6px !important;
    min-height: 36px !important;
}

.tabs {
    border-bottom: 1px solid #e2e8f0 !important;
    margin-bottom: 16px !important;
    background: #ffffff !important;
    padding: 0 4px !important;
    border-radius: 8px 8px 0 0 !important;
}
.tab-nav button,
button[role="tab"] {
    font-size: 14px !important;
    color: #64748b !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    background: transparent !important;
    padding: 12px 18px !important;
    box-shadow: none !important;
    font-weight: 400 !important;
}
.tab-nav button.selected,
button[role="tab"][aria-selected="true"] {
    color: #2563eb !important;
    font-weight: 500 !important;
    border-bottom: 2px solid #2563eb !important;
    background: transparent !important;
}
.tabitem { padding-top: 4px !important; }

.yield-value {
    font-size: 36px;
    font-weight: 700;
    color: #2563eb;
    line-height: 1.2;
    margin: 12px 0 8px;
}
.yield-unit { font-size: 16px; color: #64748b; font-weight: 400; }
.info-row { font-size: 14px; color: #334155; margin: 5px 0; line-height: 1.5; }
.info-label { color: #64748b; }
.risk-alert {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    padding: 12px 14px;
    margin-top: 12px;
}
.risk-alert-title { color: #dc2626; font-weight: 600; font-size: 14px; margin-bottom: 6px; }
.risk-alert-text { font-size: 12px; color: #334155; line-height: 1.6; }
.auto-fill-block {
    background: #f1f5f9;
    border-radius: 6px;
    padding: 12px 14px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 16px;
    font-size: 14px;
    margin: 4px 0;
}
.error-calc-block {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 6px;
    padding: 12px 14px;
    font-size: 12px;
    color: #334155;
    line-height: 1.6;
    margin: 4px 0;
}
.success-text { color: #16a34a; font-size: 14px; margin: 8px 0 0; }
.fail-text { color: #dc2626; font-size: 14px; margin: 8px 0 0; }
/* 统一居中提示：直接隐藏 toast 容器里未生效的残留内容，防止只首次显示 */
.citrus-toast-overlay,
.citrus-toast-overlay.wrap,
#app_toast,
#app_toast.wrap {
    position: fixed !important;
    inset: 0 !important;
    width: auto !important;
    height: auto !important;
    pointer-events: none !important;
    z-index: 99999 !important;
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: visible !important;
}
.citrus-toast-overlay .html-container,
.citrus-toast-overlay [data-testid="html"],
.citrus-toast-overlay .prose,
#app_toast .html-container,
#app_toast [data-testid="html"],
#app_toast .prose {
    position: relative !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 100vh !important;
    overflow: visible !important;
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
}
#app_toast textarea,
#app_toast input {
    display: none !important;
}
.citrus-toast-inline {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 1;
    pointer-events: none;
}
.citrus-toast-inline[data-toast-nonce] {
    animation: citrus-toast-auto-hide 2s ease forwards !important;
}
@keyframes citrus-toast-auto-hide {
    0%, 72% {
        opacity: 1;
        visibility: visible;
        transform: translate(-50%, -50%) scale(1);
    }
    100% {
        opacity: 0;
        visibility: hidden;
        transform: translate(-50%, -50%) scale(0.96);
    }
}
.citrus-toast-success {
    background: #f0fdf4;
    color: #15803d;
    border: 1px solid #bbf7d0;
}
.citrus-toast-error {
    background: #fef2f2;
    color: #b91c1c;
    border: 1px solid #fecaca;
}
.center-narrow { max-width: 960px; width: 100%; }
.center-wide { max-width: 1100px; width: 100%; }
.config-panel { max-width: 720px; width: 100%; overflow: visible !important; }
.config-panel .form-stack { gap: 8px !important; }
.config-panel .field-label { margin: 0 0 4px !important; }
.config-panel .block { margin-bottom: 0 !important; }
.config-panel .form-stack { gap: 8px !important; }
.config-panel .block { margin-bottom: 0 !important; }
.config-panel .field-label { margin-bottom: 4px !important; }

/* 参数说明样式 */
.param-desc {
    background: #f8fafc;
    border: 1px solid #e6eef8;
    border-radius: 6px;
    padding: 10px 12px;
    font-size: 13px;
    color: #475569;
    line-height: 1.5;
    margin-top: 6px;
}
.param-desc div { margin: 4px 0; }

/* 计算过程卡片 */
.calc-card {
    background: #ffffff;
    border: 1px solid #e6eef8;
    border-radius: 6px;
    padding: 10px 12px;
    margin-top: 8px;
}

.detection-stats { font-size: 14px; color: #334155; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f1f5f9; }

/* 预测结果标注图：强制按原图比例缩放，避免框与图错位 */
.predict-result-image,
.predict-result-image .block,
.predict-result-image .wrap,
.predict-result-image .image-container,
.predict-result-image .container {
    width: 100% !important;
    max-width: 100% !important;
    height: auto !important;
    max-height: 420px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
}
.predict-result-image img {
    max-width: 100% !important;
    max-height: 420px !important;
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
}
.history-delete-bar {
    margin-top: 12px;
    align-items: flex-end !important;
    gap: 12px !important;
}
.history-table-host .prose, .history-table-host .html-container,
.history-table-host [data-testid="html"] {
    overflow: visible !important;
    max-width: 100% !important;
}
.history-table-wrap .hist-del-btn {
    pointer-events: auto !important;
    cursor: pointer !important;
}
.hist-delete-submit,
.hist-delete-id-input,
.orchard-edit-submit,
.orchard-delete-submit,
.orchard-edit-id-input,
.orchard-edit-name-input,
.orchard-edit-trees-input,
.orchard-delete-id-input,
.orchard-delete-name-input {
    position: absolute !important;
    left: -9999px !important;
    top: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    opacity: 0 !important;
    pointer-events: none !important;
    overflow: hidden !important;
}
.hist-hidden { display: none !important; }
.history-table-wrap {
    overflow-x: auto;
    margin-top: 8px;
    width: 100%;
    -webkit-overflow-scrolling: touch;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
}
.history-table-wrap table {
    width: 100%;
    min-width: 640px;
    border-collapse: collapse;
    font-size: 14px;
    table-layout: auto;
    border: none;
    margin: 0;
}
.history-table-wrap th {
    font-weight: 600; text-align: left; padding: 8px 12px;
    border-bottom: 1px solid #e2e8f0; background: #f8fafc; color: #475569;
    white-space: nowrap;
}
.history-table-wrap td {
    padding: 8px 12px; border-bottom: 1px solid #e2e8f0;
    color: #334155; white-space: normal; word-break: break-word;
}
.history-table-wrap tbody tr:last-child td { border-bottom: none; }
.history-table-wrap tr:hover td { background: #f8fafc; }
.history-table-header {
    display: grid;
    grid-template-columns: 1.1fr 0.9fr 0.65fr 0.65fr 0.9fr 0.75fr 72px;
    gap: 8px;
    padding: 8px 12px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px 6px 0 0;
    font-weight: 600;
    font-size: 13px;
    color: #475569;
}
.history-data-row {
    display: grid !important;
    grid-template-columns: 1.1fr 0.9fr 0.65fr 0.65fr 0.9fr 0.75fr 72px !important;
    gap: 8px !important;
    align-items: center !important;
    padding: 8px 12px !important;
    border: 1px solid #e2e8f0 !important;
    border-top: none !important;
    background: #ffffff !important;
    margin: 0 !important;
}
.history-data-row:last-of-type {
    border-radius: 0 0 6px 6px !important;
}
.history-data-row:hover { background: #f8fafc !important; }
.history-data-row > .block,
.history-data-row > .form {
    margin: 0 !important;
    padding: 0 !important;
    min-width: 0 !important;
}
.history-cell {
    font-size: 14px;
    color: #334155;
    line-height: 1.4;
    word-break: break-word;
}
.btn-delete-row button {
    min-height: 32px !important;
    padding: 4px 10px !important;
    font-size: 13px !important;
    color: #dc2626 !important;
    background: #ffffff !important;
    border: 1px solid #fecaca !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}
.btn-delete-row button:hover {
    background: #fef2f2 !important;
    border-color: #fca5a5 !important;
}
.hist-del-btn {
    min-height: 32px;
    padding: 4px 10px;
    font-size: 13px;
    color: #dc2626;
    background: #ffffff;
    border: 1px solid #fecaca;
    border-radius: 6px;
    cursor: pointer;
}
.hist-del-btn:hover {
    background: #fef2f2;
    border-color: #fca5a5;
}
.risk-normal { color: #16a34a; font-weight: 500; }
.risk-warning { color: #dc2626; font-weight: 500; }
.about-content h2 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 18px 0 8px; }
.about-content h2:first-child { margin-top: 0; }
.about-content p, .about-content li { font-size: 14px; color: #334155; line-height: 1.75; }
.about-content ol { padding-left: 20px; margin: 0; }
.trend-title { font-size: 15px !important; font-weight: 700 !important; color: #1e293b !important; margin: 0 0 12px !important; }
.trend-title p { margin: 0 !important; font-size: 15px !important; font-weight: 700 !important; color: #1e293b !important; }

.filter-col { min-width: 260px !important; flex: 0 0 260px !important; }
.filter-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 20px;
    padding: 10px 14px;
    margin-top: 4px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 13px;
    color: #475569;
}
.filter-summary span { white-space: nowrap; }
.stats-cards {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 14px;
    width: 100%;
    margin: 8px 0 4px;
}
.stat-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    min-height: 86px;
}
.stat-title {
    color: #64748b;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 8px;
}
.stat-value {
    color: #0f172a;
    font-size: 26px;
    font-weight: 800;
    line-height: 1.15;
}
.filter-summary strong { color: #1e293b; font-weight: 600; }
.chart-col { flex: 1 1 auto !important; min-width: 0 !important; }
.history-filter-bar .block { margin-bottom: 0 !important; }
.history-filter-bar .form-stack { gap: 4px !important; }
.history-filter-bar .field-label { margin-bottom: 2px !important; }
.history-filter-bar .column {
    gap: 4px !important;
    min-width: 0 !important;
}
.history-filter-bar > .column.history-filter-actions {
    justify-content: flex-end !important;
}
.orchard-header {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 160px;
    gap: 12px;
    padding: 8px 12px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px 6px 0 0;
    font-weight: 600;
    font-size: 13px;
    color: #475569;
}
.orchard-data-row {
    display: grid !important;
    grid-template-columns: 2fr 1fr 1fr 160px !important;
    gap: 12px !important;
    align-items: center !important;
    padding: 10px 12px !important;
    border: 1px solid #e2e8f0 !important;
    border-top: none !important;
    background: #ffffff !important;
}
.orchard-data-row:last-child { border-radius: 0 0 6px 6px !important; }
.orchard-actions { display: flex !important; gap: 8px !important; }
.orchard-actions button:last-child {
    color: #dc2626 !important;
    border-color: #fecaca !important;
}
.orchard-actions button:last-child:hover {
    background: #fef2f2 !important;
}
.citrus-modal {
    position: fixed !important;
    inset: 0 !important;
    z-index: 9990 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 16px !important;
    background: rgba(15, 23, 42, 0.55) !important;
}
.citrus-modal.hide { display: none !important; }
.citrus-modal .citrus-modal-panel {
    width: min(560px, calc(100vw - 32px)) !important;
    max-height: calc(100vh - 32px) !important;
    overflow: auto !important;
    margin: 0 !important;
}
.row-compact { gap: 20px !important; width: 100% !important; }
.layout-full { width: 100% !important; }
.history-filter-bar { min-width: 0 !important; }
.history-filter-bar > .column { overflow: visible !important; }
"""
