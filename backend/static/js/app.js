/**
 * IDA-MAS Frontend — Single-page RAG chat application.
 *
 * Modules:
 *   Chat  — message rendering, send/retrieve, source citations
 *   Upload — drag & drop, file selection, progress feedback
 *   Docs   — document list, refresh, delete
 *   Toast  — ephemeral notification helper
 *
 * All communication goes through the FastAPI backend at /api/*.
 */

// ==========================================================================
// Toast Helpers
// ==========================================================================

function showToast(text, type) {
    const container = document.getElementById('toastContainer');
    const el = document.createElement('div');
    el.className = 'toast ' + (type || 'success');
    el.textContent = text;
    container.appendChild(el);
    setTimeout(function () { el.remove(); }, 3000);
}

// ==========================================================================
// Document List
// ==========================================================================

async function refreshDocList() {
    const list = document.getElementById('docList');
    try {
        const resp = await fetch('/api/documents');
        if (!resp.ok) throw new Error('加载失败');
        const data = await resp.json();
        if (data.documents.length === 0) {
            list.innerHTML = '<p class="empty-hint">暂无文档</p>';
            return;
        }
        list.innerHTML = data.documents.map(function (doc) {
            return (
                '<div class="doc-item">'
                + '<div class="doc-info">'
                + '<div class="doc-name">' + escHtml(doc.name) + '</div>'
                + '<div class="doc-meta">' + doc.chunk_count + ' 个片段</div>'
                + '</div>'
                + '<button class="doc-delete" data-name="' + escHtml(doc.name) + '" title="删除">×</button>'
                + '</div>'
            );
        }).join('');
        // Attach delete handlers
        list.querySelectorAll('.doc-delete').forEach(function (btn) {
            btn.addEventListener('click', function () {
                deleteDocument(btn.dataset.name);
            });
        });
    } catch (err) {
        list.innerHTML = '<p class="empty-hint" style="color:var(--error)">加载失败</p>';
    }
}

async function deleteDocument(name) {
    if (!confirm('确定要删除 "' + name + '" 吗？')) return;
    try {
        const resp = await fetch('/api/documents/' + encodeURIComponent(name), { method: 'DELETE' });
        if (!resp.ok) throw new Error('删除失败');
        showToast('已删除: ' + name, 'success');
        refreshDocList();
    } catch (err) {
        showToast('删除失败: ' + (err.message || '未知错误'), 'error');
    }
}

// ==========================================================================
// File Upload
// ==========================================================================

function setupUpload() {
    const zone = document.getElementById('uploadZone');
    const input = document.getElementById('fileInput');
    const btn = document.getElementById('uploadBtn');
    const status = document.getElementById('uploadStatus');

    // Click to select
    btn.addEventListener('click', function () { input.click(); });
    zone.addEventListener('click', function (e) { if (e.target !== btn) input.click(); });

    // Drag & drop
    zone.addEventListener('dragover', function (e) {
        e.preventDefault();
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', function () {
        zone.classList.remove('drag-over');
    });
    zone.addEventListener('drop', function (e) {
        e.preventDefault();
        zone.classList.remove('drag-over');
        var files = e.dataTransfer.files;
        if (files.length) uploadFile(files[0]);
    });

    // File selected
    input.addEventListener('change', function () {
        if (input.files.length) uploadFile(input.files[0]);
        input.value = '';
    });

    function uploadFile(file) {
        var ext = file.name.split('.').pop().toLowerCase();
        if (['pdf', 'docx', 'txt'].indexOf(ext) === -1) {
            showToast('不支持的文件类型: .' + ext, 'error');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            showToast('文件过大，最大支持 10MB', 'error');
            return;
        }

        status.innerHTML = '<p class="progress">正在上传并解析 "' + escHtml(file.name) + '"…</p>';

        var formData = new FormData();
        formData.append('file', file);

        fetch('/api/upload', { method: 'POST', body: formData })
            .then(function (resp) {
                if (!resp.ok) {
                    return resp.json().then(function (err) {
                        throw new Error(err.detail || '上传失败');
                    });
                }
                return resp.json();
            })
            .then(function (data) {
                status.innerHTML = '<p class="success">' + data.message + '</p>';
                refreshDocList();
                // Auto-hide success after 5s
                setTimeout(function () { status.innerHTML = ''; }, 5000);
            })
            .catch(function (err) {
                status.innerHTML = '<p class="error">' + escHtml(err.message) + '</p>';
            });
    }
}

// ==========================================================================
// Chat
// ==========================================================================

var isSending = false;

function setupChat() {
    var input = document.getElementById('chatInput');
    var sendBtn = document.getElementById('sendBtn');

    sendBtn.addEventListener('click', function () { sendMessage(); });
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    input.addEventListener('input', function () {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    });

    // Sample question buttons
    document.querySelectorAll('.sample-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            sendMessage(btn.dataset.question);
        });
    });
}

function sendMessage(text) {
    if (isSending) return;

    var input = document.getElementById('chatInput');
    var query = (text || input.value.trim());
    if (!query) return;

    isSending = true;
    input.value = '';
    input.style.height = 'auto';

    // Hide welcome
    var welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.style.display = 'none';

    // Render user message
    addMessage('user', query);

    // Render loading indicator
    var loadingMsg = addMessage('assistant', '<div class="typing-indicator"><span></span><span></span><span></span></div>', true);

    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query, session_id: 'default' }),
    })
        .then(function (resp) {
            if (!resp.ok) {
                return resp.json().then(function (err) {
                    throw new Error(err.detail || '请求失败');
                });
            }
            return resp.json();
        })
        .then(function (data) {
            // Replace loading indicator with actual response
            loadingMsg.querySelector('.message-bubble').innerHTML = mdToHtml(data.response);

            // Add source citations if any
            if (data.sources && data.sources.length) {
                var sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'message-sources';

                var toggle = document.createElement('button');
                toggle.className = 'source-toggle';
                toggle.textContent = '引用来源 (' + data.sources.length + ')';
                sourcesDiv.appendChild(toggle);

                var details = document.createElement('div');
                details.className = 'source-details';
                details.innerHTML = data.sources.map(function (s, i) {
                    return (
                        '<div class="source-item">'
                        + '<div class="source-doc">' + escHtml(s.document) + '  #' + s.chunk_index + '</div>'
                        + '<div class="source-chunk">' + escHtml(s.chunk_preview) + '</div>'
                        + '<div class="source-distance">相似度: ' + (1 - s.distance).toFixed(2) + '</div>'
                        + '</div>'
                    );
                }).join('');

                toggle.addEventListener('click', function () {
                    details.classList.toggle('open');
                    toggle.textContent = details.classList.contains('open')
                        ? '收起引用 (' + data.sources.length + ')'
                        : '引用来源 (' + data.sources.length + ')';
                });

                sourcesDiv.appendChild(details);
                loadingMsg.appendChild(sourcesDiv);
            }

            loadingMsg.classList.remove('loading');
            scrollToBottom();
        })
        .catch(function (err) {
            loadingMsg.querySelector('.message-bubble').innerHTML =
                '<span style="color:var(--error)">错误: ' + escHtml(err.message) + '</span>';
            loadingMsg.classList.remove('loading');
        })
        .finally(function () {
            isSending = false;
            document.getElementById('chatInput').focus();
        });
}

function addMessage(role, content, isLoading) {
    var container = document.getElementById('chatMessages');
    var div = document.createElement('div');
    div.className = 'message ' + role;
    if (isLoading) div.classList.add('loading');

    var bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    if (role === 'assistant' && !isLoading) {
        bubble.innerHTML = mdToHtml(content);
    } else {
        bubble.innerHTML = content;
    }

    div.appendChild(bubble);
    container.appendChild(div);
    scrollToBottom();
    return div;
}

function scrollToBottom() {
    var el = document.getElementById('chatMessages');
    setTimeout(function () { el.scrollTop = el.scrollHeight; }, 50);
}

// ==========================================================================
// Simple Markdown → HTML (bold, code, links, lists, paragraphs)
// ==========================================================================

function mdToHtml(text) {
    if (!text) return '';

    // Escape HTML first (but not our generated tags)
    var out = escHtml(text);

    // Code blocks: ```...```
    out = out.replace(/```(\w*)\n([\s\S]*?)```/g, function (_, lang, code) {
        return '<pre><code>' + code.trim() + '</code></pre>';
    });

    // Inline code: `...`
    out = out.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold: **...**
    out = out.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Convert double newlines to paragraphs
    var paras = out.split(/\n\n+/);
    out = paras.map(function (p) {
        p = p.trim();
        if (!p) return '';
        if (p.startsWith('<pre>') || p.startsWith('<h')) return p;
        // Single newlines within a paragraph → <br>
        p = p.replace(/\n/g, '<br>');
        return '<p>' + p + '</p>';
    }).join('\n');

    // Numbered list detection: lines starting with "1. "
    out = out.replace(/<p>(\d+)\. /g, '<p>$1. ');

    return out;
}

function escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ==========================================================================
// Init
// ==========================================================================

document.addEventListener('DOMContentLoaded', function () {
    setupUpload();
    setupChat();
    refreshDocList();
});
