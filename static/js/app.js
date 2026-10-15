// Global Application State
let currentDocId = null;
let currentFilename = null;
let totalPages = 1;
let currentPage = 1;
let currentHierarchy = null;
let selectedFile = null;
let currentZoom = 1.0;
let pageTopicsCache = {};

document.addEventListener('DOMContentLoaded', () => {
    initDragAndDrop();
    initTabs();
    initChat();
    initSearch();
});

// 1. Drag & Drop and File Selection Setup
function initDragAndDrop() {
    const dropCard = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    if (!dropCard || !fileInput) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropCard.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropCard.addEventListener(eventName, () => dropCard.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropCard.addEventListener(eventName, () => dropCard.classList.remove('drag-over'), false);
    });

    dropCard.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleSelectedFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });
}

function handleSelectedFile(file) {
    if (!file || (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf')) {
        alert('Please select a valid PDF file.');
        return;
    }

    selectedFile = file;
    document.getElementById('selectedFileName').textContent = file.name;
    document.getElementById('selectedFileSize').textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
    document.getElementById('selectedFileBox').style.display = 'flex';
}

function removeSelectedFile() {
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('selectedFileBox').style.display = 'none';
}

// 2. Upload & Processing Pipeline (12 Stages as specified in Section 2)
async function processSyllabus() {
    if (!selectedFile) {
        alert('Please select a syllabus PDF first.');
        return;
    }

    const processingCard = document.getElementById('processingCard');
    const progressBarFill = document.getElementById('progressBarFill');
    const progressPercentText = document.getElementById('progressPercentText');

    processingCard.style.display = 'block';

    const stages = [
        "Reading PDF",
        "Extracting text",
        "Detecting document structure",
        "Detecting courses",
        "Detecting semesters/sections",
        "Detecting units",
        "Detecting topics/subtopics",
        "Detecting outcomes",
        "Detecting books/references",
        "Indexing page references",
        "Calculating extraction confidence",
        "Ready for questions"
    ];

    let currentStage = 0;
    updatePipelineStepUI(0, stages[0]);
    progressBarFill.style.width = '8%';
    progressPercentText.textContent = '8%';

    const interval = setInterval(() => {
        if (currentStage < stages.length - 2) {
            currentStage++;
            const pct = Math.round(((currentStage + 1) / stages.length) * 90);
            progressBarFill.style.width = pct + '%';
            progressPercentText.textContent = pct + '%';
            updatePipelineStepUI(currentStage, stages[currentStage]);
        }
    }, 350);

    const formData = new FormData();
    formData.append('pdf', selectedFile);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(interval);

        const data = await response.json();

        if (!response.ok || !data.success) {
            alert(data.error || 'Failed to process syllabus PDF.');
            processingCard.style.display = 'none';
            return;
        }

        // Processing Complete
        progressBarFill.style.width = '100%';
        progressPercentText.textContent = '100%';
        updatePipelineStepUI(stages.length - 1, "Ready for questions");

        setTimeout(() => {
            loadWorkspace(data);
        }, 500);

    } catch (err) {
        clearInterval(interval);
        alert('Upload network error: ' + err.message);
        processingCard.style.display = 'none';
    }
}

function updatePipelineStepUI(stepIndex, stepName) {
    const container = document.getElementById('pipelineStepsContainer');
    if (!container) return;
    
    let html = '';
    const stages = [
        "Reading PDF", "Extracting text", "Detecting document structure", "Detecting courses",
        "Detecting semesters/sections", "Detecting units", "Detecting topics/subtopics",
        "Detecting outcomes", "Detecting books/references", "Indexing page references",
        "Calculating extraction confidence", "Ready for questions"
    ];

    stages.forEach((s, i) => {
        let cls = 'step-item';
        let icon = '⚪';
        if (i < stepIndex) {
            cls += ' completed';
            icon = '✅';
        } else if (i === stepIndex) {
            cls += ' active';
            icon = '⚡';
        }
        html += `<div class="${cls}"><span class="step-icon">${icon}</span> ${s}</div>`;
    });
    container.innerHTML = html;
}

// 3. Workspace Initialization
function loadWorkspace(data) {
    currentDocId = data.doc_id;
    currentFilename = data.filename;
    totalPages = data.total_pages;
    currentPage = 1;
    currentHierarchy = data.hierarchy;
    pageTopicsCache = {};

    // Hide upload screen, show workspace screen
    document.getElementById('uploadScreen').style.display = 'none';
    document.getElementById('workspaceScreen').style.display = 'flex';

    // Populate Overview Stats Bar
    document.getElementById('statFilename').textContent = currentFilename;
    document.getElementById('statPages').textContent = totalPages;
    document.getElementById('statCourses').textContent = data.courses_detected;
    document.getElementById('statConfidence').textContent = data.confidence + '%';
    document.getElementById('pageTotalDisplay').textContent = totalPages;

    // Populate and Show "SYLLABUS LOADED" Overview Modal (Section 1 & 30)
    populateSyllabusLoadedModal(data);

    // Populate Course Filter Dropdown & Directory Modal
    populateCourseSelectAndModal(currentHierarchy.courses || []);

    // Render PDF Page 1
    renderPdfPage(1);

    // Render Full Syllabus Tree
    renderFullSyllabusTree(currentHierarchy);

    // Render 8-signal Confidence Breakdown
    renderConfidenceBreakdown(data.confidence_details);

    // Initial greeting in Chatbot
    const chatContainer = document.getElementById('chatMessages');
    chatContainer.innerHTML = `
        <div class="msg-bubble msg-bot">
            <h3>🤖 AI Syllabus Chatbot Ready</h3>
            <p>I have processed <strong>${escapeHtml(currentFilename)}</strong> (${totalPages} pages, ${data.courses_detected} courses detected with <strong>${data.confidence}% estimated confidence</strong>).</p>
            <p>Ask me anything about courses, units, topics, subtopics, credits, outcomes, Bloom's levels, or books. Every response includes exact source page citations!</p>
        </div>
    `;
}

// 4. "SYLLABUS LOADED" Modal Handlers (Section 1 & 30)
function populateSyllabusLoadedModal(data) {
    document.getElementById('modalFileName').textContent = data.filename;
    document.getElementById('modalPages').textContent = data.total_pages;
    document.getElementById('modalCourses').textContent = data.courses_detected;
    document.getElementById('modalConfidence').textContent = data.confidence + '%';

    const metaBox = document.getElementById('modalMetaDetails');
    let metaHtml = '';
    const h = data.hierarchy;
    if (h.institution) metaHtml += `<div class="meta-badge">🏛️ ${escapeHtml(h.institution.name)}</div>`;
    if (h.programme) metaHtml += `<div class="meta-badge">🎓 ${escapeHtml(h.programme.name)}</div>`;
    if (h.department) metaHtml += `<div class="meta-badge">🏢 ${escapeHtml(h.department.name)}</div>`;
    if (h.batch_year) metaHtml += `<div class="meta-badge">📅 ${escapeHtml(h.batch_year.val)}</div>`;
    metaBox.innerHTML = metaHtml || `<div style="color:var(--text-muted); font-size:0.85rem;">Document structure parsed across ${totalPages} pages.</div>`;

    document.getElementById('syllabusLoadedModal').style.display = 'flex';
}

function closeLoadedModal() {
    document.getElementById('syllabusLoadedModal').style.display = 'none';
}

function openSyllabusViewFromModal() {
    closeLoadedModal();
    switchTab('tabTree');
}

function openChatFromModal() {
    closeLoadedModal();
    switchTab('tabChat');
}

// 5. PDF Navigation & Page Topics Synchronization (Line 9 Feature)
function renderPdfPage(pageNum) {
    if (pageNum < 1) pageNum = 1;
    if (pageNum > totalPages) pageNum = totalPages;

    currentPage = pageNum;
    document.getElementById('pageInput').value = pageNum;

    const imgElem = document.getElementById('pdfPageImage');
    imgElem.src = `/api/document/${currentDocId}/page_image/${pageNum}`;

    // Update Topics on this Page
    updatePageTopics(pageNum);
}

function prevPage() {
    if (currentPage > 1) renderPdfPage(currentPage - 1);
}

function nextPage() {
    if (currentPage < totalPages) renderPdfPage(currentPage + 1);
}

function jumpToPage(num) {
    const p = parseInt(num);
    if (!isNaN(p)) renderPdfPage(p);
}

// Zoom Controls
function zoomIn() {
    currentZoom = Math.min(2.5, currentZoom + 0.2);
    applyZoom();
}

function zoomOut() {
    currentZoom = Math.max(0.6, currentZoom - 0.2);
    applyZoom();
}

function resetZoom() {
    currentZoom = 1.0;
    applyZoom();
}

function applyZoom() {
    const wrapper = document.getElementById('pdfZoomWrapper');
    if (wrapper) wrapper.style.transform = `scale(${currentZoom})`;
    const label = document.getElementById('pdfZoomLabel');
    if (label) label.textContent = `${Math.round(currentZoom * 100)}%`;
}

// Page Topics Panel (Prompt Line 9: "display the topic in pdf for user reference with subtopics")
function togglePageTopicsPanel() {
    const panel = document.getElementById('pageTopicsPanel');
    const btn = document.getElementById('btnTogglePageTopics');
    if (!panel) return;

    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        if (btn) btn.classList.add('active');
    } else {
        panel.style.display = 'none';
        if (btn) btn.classList.remove('active');
    }
}

async function updatePageTopics(pageNum) {
    const numDisplay = document.getElementById('pageTopicsNum');
    const content = document.getElementById('pageTopicsContent');
    const countBadge = document.getElementById('pageTopicsCount');
    if (!content) return;

    if (numDisplay) numDisplay.textContent = pageNum;

    // Check cache first
    if (pageTopicsCache[pageNum]) {
        renderPageTopicsContent(pageTopicsCache[pageNum]);
        return;
    }

    try {
        const resp = await fetch(`/api/document/${currentDocId}/page_topics/${pageNum}`);
        if (!resp.ok) return;
        const data = await resp.json();
        pageTopicsCache[pageNum] = data;
        renderPageTopicsContent(data);
    } catch (e) {
        content.innerHTML = `<div style="color:var(--text-muted); font-size:0.8rem;">Unable to load page topics.</div>`;
    }
}

function renderPageTopicsContent(data) {
    const content = document.getElementById('pageTopicsContent');
    const countBadge = document.getElementById('pageTopicsCount');
    if (!content) return;

    const topics = data.topics || [];
    const units = data.units || [];
    const courses = data.courses || [];

    if (countBadge) countBadge.textContent = `${topics.length} Topics`;

    if (topics.length === 0 && units.length === 0 && courses.length === 0) {
        content.innerHTML = `
            <div style="color:var(--text-muted); font-size:0.8rem; padding:6px 0;">
                No specific topics or units identified on this page (Page ${data.page}). Overview, tables, or introductory content.
            </div>
        `;
        return;
    }

    let html = '';
    
    // Header for courses on this page
    if (courses.length > 0) {
        courses.forEach(c => {
            html += `<div class="topic-ref-course">📘 <strong>${escapeHtml(c.code)}</strong>: ${escapeHtml(c.title)}</div>`;
        });
    }

    // Units on this page
    if (units.length > 0) {
        units.forEach(u => {
            const hrs = u.hours ? ` (${u.hours} Hours)` : '';
            html += `<div class="topic-ref-unit">📗 <strong>Unit ${escapeHtml(u.unit_number)}</strong>: ${escapeHtml(u.title)}${hrs}</div>`;
        });
    }

    // Topics & Subtopics
    topics.forEach((t, i) => {
        html += `
            <div class="topic-ref-item">
                <div class="topic-ref-title">
                    <span>🔸 ${escapeHtml(t.title)}</span>
                    <button class="btn-ask-topic" onclick="askAboutTopic('${escapeQuotes(t.title)}')">Ask Chat</button>
                </div>
        `;

        if (t.subtopics && t.subtopics.length > 0) {
            html += `<div class="topic-ref-subtopics">`;
            t.subtopics.forEach(st => {
                html += `<div class="topic-ref-subtopic">• ${escapeHtml(st)}</div>`;
            });
            html += `</div>`;
        }

        html += `</div>`;
    });

    content.innerHTML = html;
}

function askAboutTopic(topicTitle) {
    switchTab('tabChat');
    const input = document.getElementById('chatInput');
    input.value = `Tell me about the topic: ${topicTitle}`;
    sendChatMessage();
}

// 6. Courses Directory Modal & Filter
function populateCourseSelectAndModal(courses) {
    const select = document.getElementById('courseTreeFilter');
    const modalList = document.getElementById('coursesModalList');
    if (!select || !modalList) return;

    select.innerHTML = `<option value="all">All Detected Courses (${courses.length})</option>`;
    let modalHtml = '';

    courses.forEach((c, idx) => {
        const cred = c.credits_info;
        const credStr = cred ? `L:${cred.L} T:${cred.T} P:${cred.P} C:${cred.C}` : 'Credits: N/A';
        const sem = c.semester ? `Semester ${c.semester}` : 'Semester: N/A';
        const unitCount = (c.units || []).length;

        // Select Option
        select.innerHTML += `<option value="${c.code}">${c.code} - ${c.title}</option>`;

        // Modal Card
        modalHtml += `
            <div class="course-modal-card">
                <div class="course-modal-header">
                    <div>
                        <div class="course-modal-code">${escapeHtml(c.code)}</div>
                        <div class="course-modal-title">${escapeHtml(c.title)}</div>
                    </div>
                    <span class="citation-chip" onclick="jumpToPageAndCloseModal(${c.start_page})">📄 Start Page ${c.start_page}</span>
                </div>
                <div class="course-modal-meta">
                    <span>${sem}</span> • <span>${credStr}</span> • <span>${unitCount} Units</span>
                </div>
                <div class="course-modal-actions">
                    <button class="btn-secondary btn-sm" onclick="jumpToPageAndCloseModal(${c.start_page})">View in PDF</button>
                    <button class="btn-primary btn-sm" onclick="askCourseInChat('${escapeQuotes(c.code)}', '${escapeQuotes(c.title)}')">Chat about Course</button>
                </div>
            </div>
        `;
    });

    modalList.innerHTML = modalHtml || `<div style="color:var(--text-muted);">No distinct courses detected.</div>`;
}

function openCoursesModal() {
    document.getElementById('coursesModal').style.display = 'flex';
}

function closeCoursesModal() {
    document.getElementById('coursesModal').style.display = 'none';
}

function jumpToPageAndCloseModal(pageNum) {
    closeCoursesModal();
    jumpToPage(pageNum);
}

function askCourseInChat(code, title) {
    closeCoursesModal();
    switchTab('tabChat');
    const input = document.getElementById('chatInput');
    input.value = `What is the syllabus structure and units for ${code} (${title})?`;
    sendChatMessage();
}

// 7. Tab Switching
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-tab');
            switchTab(target);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-tab') === tabId);
    });
    document.querySelectorAll('.tab-content').forEach(c => {
        c.classList.toggle('active', c.id === tabId);
    });
}

// 8. Chat Implementation
function initChat() {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendChatBtn');

    if (!chatInput || !sendBtn) return;

    sendBtn.addEventListener('click', () => sendChatMessage());
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
}

function sendSuggestedPrompt(text) {
    document.getElementById('chatInput').value = text;
    sendChatMessage();
}

async function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const question = chatInput.value.trim();
    if (!question || !currentDocId) return;

    const chatContainer = document.getElementById('chatMessages');

    // Append User Bubble
    const userMsg = document.createElement('div');
    userMsg.className = 'msg-bubble msg-user';
    userMsg.textContent = question;
    chatContainer.appendChild(userMsg);

    chatInput.value = '';
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Append Bot Thinking Indicator
    const thinkingMsg = document.createElement('div');
    thinkingMsg.className = 'msg-bubble msg-bot';
    thinkingMsg.id = 'botThinking';
    thinkingMsg.innerHTML = `<em>Searching syllabus & retrieving grounded evidence...</em>`;
    chatContainer.appendChild(thinkingMsg);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                doc_id: currentDocId,
                question: question
            })
        });

        const data = await response.json();
        if (document.getElementById('botThinking')) {
            chatContainer.removeChild(thinkingMsg);
        }

        if (!response.ok || !data.success) {
            const errMsg = document.createElement('div');
            errMsg.className = 'msg-bubble msg-bot';
            errMsg.innerHTML = `<span style="color:var(--accent-rose)">Error: ${data.error || 'Unable to answer.'}</span>`;
            chatContainer.appendChild(errMsg);
            return;
        }

        // Render Bot Answer
        const botMsg = document.createElement('div');
        botMsg.className = 'msg-bubble msg-bot';

        let html = parseMarkdownAndCitations(data.answer);

        // Sources toggle & confidence badge
        if (data.source_pages && data.source_pages.length > 0) {
            html += `<div style="margin-top:14px; font-size:0.8rem; color:var(--text-muted); border-top:1px solid var(--bg-card-border); padding-top:10px;">`;
            html += `<strong>Cited PDF Pages:</strong> `;
            data.source_pages.forEach(p => {
                html += `<span class="citation-chip" onclick="jumpToPage(${p})">📄 Page ${p}</span> `;
            });
            html += `</div>`;
        }

        botMsg.innerHTML = html;
        chatContainer.appendChild(botMsg);
        chatContainer.scrollTop = chatContainer.scrollHeight;

    } catch (err) {
        if (document.getElementById('botThinking')) {
            chatContainer.removeChild(thinkingMsg);
        }
        alert('Chat request failed: ' + err.message);
    }
}

// Markdown & Interactive Citation Link Parser
function parseMarkdownAndCitations(text) {
    if (!text) return '';

    let parsed = text
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');

    // Convert PDF Page citations into interactive clickable chips
    parsed = parsed.replace(/(?:Source:\s*)?PDF Page[s]?\s*(\d+)(?:–(\d+))?/gi, (match, p1, p2) => {
        if (p2) {
            return `<span class="citation-chip" onclick="jumpToPage(${p1})">📄 Pages ${p1}–${p2}</span>`;
        }
        return `<span class="citation-chip" onclick="jumpToPage(${p1})">📄 Page ${p1}</span>`;
    });

    parsed = parsed.replace(/\(Source:\s*Page\s*(\d+)\)/gi, (match, p1) => {
        return `<span class="citation-chip" onclick="jumpToPage(${p1})">📄 Page ${p1}</span>`;
    });

    parsed = parsed.replace(/Source:\s*PDF Page\s*(\d+)/gi, (match, p1) => {
        return `<span class="citation-chip" onclick="jumpToPage(${p1})">📄 Page ${p1}</span>`;
    });

    return parsed;
}

// 9. Full Syllabus Tree View Renderer
function renderFullSyllabusTree(h) {
    const container = document.getElementById('treeContainer');
    if (!container || !h) return;

    let html = `<div class="syllabus-doc-meta-card">`;
    if (h.institution) html += `<div class="meta-row"><strong>🏛️ Institution:</strong> ${escapeHtml(h.institution.name)} <span class="citation-chip" onclick="jumpToPage(${h.institution.page})">📄 Page ${h.institution.page}</span></div>`;
    if (h.programme) html += `<div class="meta-row"><strong>🎓 Programme:</strong> ${escapeHtml(h.programme.name)} <span class="citation-chip" onclick="jumpToPage(${h.programme.page})">📄 Page ${h.programme.page}</span></div>`;
    if (h.department) html += `<div class="meta-row"><strong>🏢 Department:</strong> ${escapeHtml(h.department.name)} <span class="citation-chip" onclick="jumpToPage(${h.department.page})">📄 Page ${h.department.page}</span></div>`;
    if (h.batch_year) html += `<div class="meta-row"><strong>📅 Regulation / Batch:</strong> ${escapeHtml(h.batch_year.val)} <span class="citation-chip" onclick="jumpToPage(${h.batch_year.page})">📄 Page ${h.batch_year.page}</span></div>`;
    html += `</div>`;

    const courses = h.courses || [];
    if (courses.length === 0) {
        html += `<div style="color:var(--text-muted); padding:20px;">No course structures found.</div>`;
    }

    courses.forEach((c, cIdx) => {
        const cred = c.credits_info;
        const credStr = cred ? ` [L: ${cred.L}, T: ${cred.T}, P: ${cred.P}, C: ${cred.C}]` : '';

        html += `
            <div class="tree-node tree-course-node" data-course-code="${escapeHtml(c.code)}">
                <div class="tree-course-header">
                    <div>
                        <span class="tree-toggle" onclick="toggleTreeNode(this)">▼</span>
                        <strong>📘 ${escapeHtml(c.code)} - ${escapeHtml(c.title)}</strong>
                        <span style="font-size:0.85rem; color:var(--accent-blue);">${credStr}</span>
                    </div>
                    <span class="citation-chip" onclick="jumpToPage(${c.start_page})">📄 Page ${c.start_page}</span>
                </div>
                <div class="tree-node-body">
        `;

        // Units
        (c.units || []).forEach(u => {
            const hrs = u.hours ? ` (${u.hours} Hours)` : '';
            html += `
                <div class="tree-node tree-unit-node">
                    <div class="tree-title">
                        <div>
                            <span class="tree-toggle" onclick="toggleTreeNode(this)">▼</span>
                            <strong>📗 Unit ${escapeHtml(u.unit_number)}: ${escapeHtml(u.title)}</strong>${hrs}
                        </div>
                        <span class="citation-chip" onclick="jumpToPage(${u.page})">📄 Page ${u.page}</span>
                    </div>
                    <div class="tree-node-body">
            `;

            (u.topics || []).forEach(t => {
                html += `
                    <div class="tree-topic-item">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span>🔸 ${escapeHtml(t.title)}</span>
                            <span class="citation-chip" onclick="jumpToPage(${t.page})">📄 Page ${t.page}</span>
                        </div>
                `;

                if (t.subtopics && t.subtopics.length > 0) {
                    html += `<div class="tree-subtopics-list">`;
                    t.subtopics.forEach(st => {
                        html += `<div>• ${escapeHtml(st.title)} <span class="citation-chip citation-chip-sm" onclick="jumpToPage(${st.page})">p.${st.page}</span></div>`;
                    });
                    html += `</div>`;
                }

                html += `</div>`;
            });

            html += `</div></div>`;
        });

        // Course Outcomes with Bloom's Taxonomy
        if (c.outcomes && c.outcomes.length > 0) {
            html += `<div class="tree-section-box"><strong>🎯 Course Outcomes:</strong><ul class="tree-list">`;
            c.outcomes.forEach(co => {
                const bloomBadge = co.bloom_level ? `<span class="bloom-badge">Bloom: ${co.bloom_level} (${co.bloom_source})</span>` : '';
                html += `<li>${escapeHtml(co.text)} ${bloomBadge} <span class="citation-chip citation-chip-sm" onclick="jumpToPage(${co.page})">p.${co.page}</span></li>`;
            });
            html += `</ul></div>`;
        }

        // Textbooks & Reference Books
        if (c.textbooks && c.textbooks.length > 0) {
            html += `<div class="tree-section-box"><strong>📖 Text Books:</strong><ul class="tree-list">`;
            c.textbooks.forEach(tb => {
                html += `<li>${escapeHtml(tb.title)} <span class="citation-chip citation-chip-sm" onclick="jumpToPage(${tb.page})">p.${tb.page}</span></li>`;
            });
            html += `</ul></div>`;
        }

        if (c.reference_books && c.reference_books.length > 0) {
            html += `<div class="tree-section-box"><strong>📚 Reference Books:</strong><ul class="tree-list">`;
            c.reference_books.forEach(rb => {
                html += `<li>${escapeHtml(rb.title)} <span class="citation-chip citation-chip-sm" onclick="jumpToPage(${rb.page})">p.${rb.page}</span></li>`;
            });
            html += `</ul></div>`;
        }

        // CO-PO Matrix
        if (c.co_po_matrix && c.co_po_matrix.length > 0) {
            const mat = c.co_po_matrix[0];
            html += `<div class="tree-section-box"><strong>📊 CO-PO Mapping Matrix:</strong> <span class="citation-chip" onclick="jumpToPage(${mat.page})">📄 Page ${mat.page}</span>`;
            html += `<div class="table-responsive"><table class="matrix-table">`;
            (mat.matrix || []).forEach((row, rI) => {
                html += `<tr>`;
                row.forEach(cell => {
                    html += rI === 0 ? `<th>${escapeHtml(String(cell))}</th>` : `<td>${escapeHtml(String(cell))}</td>`;
                });
                html += `</tr>`;
            });
            html += `</table></div></div>`;
        }

        html += `</div></div>`;
    });

    container.innerHTML = html;
}

function toggleTreeNode(elem) {
    const parentNode = elem.closest('.tree-node');
    if (!parentNode) return;
    const body = parentNode.querySelector('.tree-node-body');
    if (!body) return;

    if (body.style.display === 'none') {
        body.style.display = 'block';
        elem.textContent = '▼';
    } else {
        body.style.display = 'none';
        elem.textContent = '►';
    }
}

function expandAllTreeNodes() {
    document.querySelectorAll('.tree-node-body').forEach(b => b.style.display = 'block');
    document.querySelectorAll('.tree-toggle').forEach(t => t.textContent = '▼');
}

function collapseAllTreeNodes() {
    document.querySelectorAll('.tree-node-body').forEach(b => b.style.display = 'none');
    document.querySelectorAll('.tree-toggle').forEach(t => t.textContent = '►');
}

function filterSyllabusTree(selectedCode) {
    const nodes = document.querySelectorAll('.tree-course-node');
    nodes.forEach(n => {
        if (selectedCode === 'all' || n.getAttribute('data-course-code') === selectedCode) {
            n.style.display = 'block';
        } else {
            n.style.display = 'none';
        }
    });
}

// 10. Search Functionality
function initSearch() {
    const input = document.getElementById('searchInput');
    const btn = document.getElementById('searchBtn');
    if (!input || !btn) return;

    btn.addEventListener('click', () => runSearch());
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') runSearch();
    });
}

async function runSearch() {
    const input = document.getElementById('searchInput');
    const q = input.value.trim();
    if (!q || !currentDocId) return;

    const resultsContainer = document.getElementById('searchResultsList');
    resultsContainer.innerHTML = '<div style="padding:10px;"><em>Searching extracted syllabus index...</em></div>';

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ doc_id: currentDocId, query: q })
        });
        const data = await response.json();

        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML = '<div style="padding:10px; color:var(--text-muted);">No direct matches found. Try alternative keywords or ask the chatbot.</div>';
            return;
        }

        let html = '';
        data.results.forEach(r => {
            html += `
                <div class="search-card">
                    <div class="search-card-meta">
                        <span>${escapeHtml(r.section)}</span>
                        <span class="citation-chip" onclick="jumpToPage(${r.page})">📄 Page ${r.page}</span>
                    </div>
                    <div style="font-size:0.9rem; color:var(--text-main); line-height:1.5;">${escapeHtml(r.text)}</div>
                </div>
            `;
        });
        resultsContainer.innerHTML = html;

    } catch (err) {
        resultsContainer.innerHTML = `<span style="color:var(--accent-rose)">Search error: ${err.message}</span>`;
    }
}

// 11. Render 8 Confidence Signals Breakdown Cards
function renderConfidenceBreakdown(conf) {
    const container = document.getElementById('confidenceGrid');
    if (!container || !conf) return;

    container.innerHTML = `
        <div class="conf-card"><div class="conf-name">Overall Confidence</div><div class="conf-val" style="color:var(--accent-cyan);">${conf.overall}%</div></div>
        <div class="conf-card"><div class="conf-name">Text Quality</div><div class="conf-val">${conf.text_extraction}%</div></div>
        <div class="conf-card"><div class="conf-name">OCR Performance</div><div class="conf-val">${conf.ocr}%</div></div>
        <div class="conf-card"><div class="conf-name">Course Detection</div><div class="conf-val">${conf.course_detection}%</div></div>
        <div class="conf-card"><div class="conf-name">Unit Detection</div><div class="conf-val">${conf.unit_detection}%</div></div>
        <div class="conf-card"><div class="conf-name">Topic Coverage</div><div class="conf-val">${conf.topic_detection}%</div></div>
        <div class="conf-card"><div class="conf-name">Table Detection</div><div class="conf-val">${conf.table_detection || 0}%</div></div>
        <div class="conf-card"><div class="conf-name">Outcome Detection</div><div class="conf-val">${conf.outcome_detection || 0}%</div></div>
    `;
}

// 12. Exports
function downloadJSON() {
    if (currentDocId) window.open(`/api/document/${currentDocId}/json`, '_blank');
}

function downloadText() {
    if (currentDocId) window.open(`/api/document/${currentDocId}/text`, '_blank');
}

function downloadReport() {
    if (currentDocId) window.open(`/api/document/${currentDocId}/report`, '_blank');
}

function resetUpload() {
    currentDocId = null;
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('selectedFileBox').style.display = 'none';
    document.getElementById('processingCard').style.display = 'none';
    document.getElementById('workspaceScreen').style.display = 'none';
    document.getElementById('uploadScreen').style.display = 'flex';
}

// Utilities
function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function escapeQuotes(str) {
    if (!str) return '';
    return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"');
}
