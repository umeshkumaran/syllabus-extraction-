// Global State
let currentDocId = null;
let currentFilename = null;
let totalPages = 1;
let currentPage = 1;
let currentHierarchy = null;
let selectedFile = null;

document.addEventListener('DOMContentLoaded', () => {
    initDragAndDrop();
    initTabs();
    initChat();
    initSearch();
});

// Drag & Drop Setup
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

    const maxVercelBytes = 4.5 * 1024 * 1024; // Vercel 4.5 MB limit
    if (file.size > maxVercelBytes) {
        alert(`File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds Vercel's 4.5 MB upload limit. Please select a syllabus PDF under 4.5 MB or compress your PDF.`);
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

// Upload & Process Pipeline Simulation
async function processSyllabus() {
    if (!selectedFile) {
        alert('Please select a syllabus PDF first.');
        return;
    }

    const maxVercelBytes = 4.5 * 1024 * 1024;
    if (selectedFile.size > maxVercelBytes) {
        alert(`Your file is ${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB. Vercel serverless functions restrict uploads to 4.5 MB max. Please upload a smaller PDF or compress it.`);
        return;
    }

    const processingCard = document.getElementById('processingCard');
    const progressBarFill = document.getElementById('progressBarFill');
    const progressPercentText = document.getElementById('progressPercentText');

    processingCard.style.display = 'block';

    // Pipeline steps
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
    }, 400);

    const formData = new FormData();
    formData.append('pdf', selectedFile);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(interval);

        if (response.status === 413) {
            alert('HTTP 413 Payload Too Large: Upload exceeds Vercel 4.5 MB limit. Please compress your PDF and try again.');
            processingCard.style.display = 'none';
            return;
        }

        const data = await response.json();

        if (!response.ok || !data.success) {
            alert(data.error || 'Processing failed.');
            processingCard.style.display = 'none';
            return;
        }

        // Processing Complete
        progressBarFill.style.width = '100%';
        progressPercentText.textContent = '100%';
        updatePipelineStepUI(stages.length - 1, "Ready for questions");

        setTimeout(() => {
            loadWorkspace(data);
        }, 600);

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

// Workspace Loading
function loadWorkspace(data) {
    currentDocId = data.doc_id;
    currentFilename = data.filename;
    totalPages = data.total_pages;
    currentPage = 1;
    currentHierarchy = data.hierarchy;

    // Hide upload screen, show workspace screen
    document.getElementById('uploadScreen').style.display = 'none';
    document.getElementById('workspaceScreen').style.display = 'flex';

    // Populate Overview Stats Bar
    document.getElementById('statFilename').textContent = currentFilename;
    document.getElementById('statPages').textContent = totalPages;
    document.getElementById('statCourses').textContent = data.courses_detected;
    document.getElementById('statConfidence').textContent = data.confidence + '%';

    document.getElementById('pageTotalDisplay').textContent = totalPages;

    // Render PDF page 1
    renderPdfPage(1);

    // Render Full Syllabus Tree
    renderFullSyllabusTree(currentHierarchy);

    // Render Confidence Breakdown
    renderConfidenceBreakdown(data.confidence_details);

    // Initial greeting in Chatbot
    const chatContainer = document.getElementById('chatMessages');
    chatContainer.innerHTML = `
        <div class="msg-bubble msg-bot">
            <h3>🤖 AI Syllabus Chatbot Ready</h3>
            <p>I have processed <strong>${currentFilename}</strong> (${totalPages} pages, ${data.courses_detected} courses detected with <strong>${data.confidence}% estimated confidence</strong>).</p>
            <p>Ask me anything about courses, units, topics, subtopics, credits, outcomes, or books. Every answer will cite exact source pages!</p>
        </div>
    `;
}

// PDF Navigation Functions
function renderPdfPage(pageNum) {
    if (pageNum < 1) pageNum = 1;
    if (pageNum > totalPages) pageNum = totalPages;

    currentPage = pageNum;
    document.getElementById('pageInput').value = pageNum;

    const imgElem = document.getElementById('pdfPageImage');
    imgElem.src = `/api/document/${currentDocId}/page_image/${pageNum}`;
}

function prevPage() {
    if (currentPage > 1) renderPdfPage(currentPage - 1);
}

function nextPage() {
    if (currentPage < totalPages) renderPdfPage(currentPage + 1);
}

function jumpToPage(num) {
    renderPdfPage(parseInt(num));
}

// Tab Switching
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const target = btn.getAttribute('data-tab');
            document.getElementById(target).classList.add('active');
        });
    });
}

// Chat Implementation
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
        chatContainer.removeChild(thinkingMsg);

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
            html += `<div style="margin-top:12px; font-size:0.8rem; color:var(--text-muted); border-top:1px solid var(--bg-card-border); padding-top:8px;">`;
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

// Markdown & Citation Link Parser
function parseMarkdownAndCitations(text) {
    if (!text) return '';

    // Convert Headers
    let parsed = text
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');

    // Convert PDF Page X citations into interactive chip buttons
    parsed = parsed.replace(/(?:Source:\s*)?PDF Page[s]?\s*(\d+)(?:–(\d+))?/gi, (match, p1, p2) => {
        if (p2) {
            return `<span class="citation-chip" onclick="jumpToPage(${p1})">📄 Pages ${p1}–${p2}</span>`;
        }
        return `<span class="citation-chip" onclick="jumpToPage(${p1})">📄 Page ${p1}</span>`;
    });

    parsed = parsed.replace(/Page (\d+)/gi, (match, p1) => {
        return `<span class="citation-chip" onclick="jumpToPage(${p1})">📄 Page ${p1}</span>`;
    });

    return parsed;
}

// Tree View Renderer
function renderFullSyllabusTree(h) {
    const container = document.getElementById('treeContainer');
    if (!container || !h) return;

    let html = `<div style="margin-bottom:16px;">`;
    if (h.institution) html += `<div><strong>Institution:</strong> ${h.institution.name} <span class="citation-chip" onclick="jumpToPage(${h.institution.page})">📄 Page ${h.institution.page}</span></div>`;
    if (h.programme) html += `<div><strong>Programme:</strong> ${h.programme.name} <span class="citation-chip" onclick="jumpToPage(${h.programme.page})">📄 Page ${h.programme.page}</span></div>`;
    if (h.department) html += `<div><strong>Department:</strong> ${h.department.name} <span class="citation-chip" onclick="jumpToPage(${h.department.page})">📄 Page ${h.department.page}</span></div>`;
    if (h.batch_year) html += `<div><strong>Regulation/Batch:</strong> ${h.batch_year.val} <span class="citation-chip" onclick="jumpToPage(${h.batch_year.page})">📄 Page ${h.batch_year.page}</span></div>`;
    html += `</div>`;

    (h.courses || []).forEach(c => {
        html += `<div class="tree-node" style="border-left-color:var(--accent-cyan);">`;
        html += `<div class="tree-title">📘 ${c.code} - ${c.title} <span class="citation-chip" onclick="jumpToPage(${c.start_page})">📄 Page ${c.start_page}</span></div>`;
        
        (c.units || []).forEach(u => {
            html += `<div class="tree-node" style="border-left-color:var(--accent-blue);">`;
            html += `<div class="tree-title">📗 Unit ${u.unit_number}: ${u.title} <span class="citation-chip" onclick="jumpToPage(${u.page})">📄 Page ${u.page}</span></div>`;

            (u.topics || []).forEach(t => {
                html += `<div class="tree-node">`;
                html += `<div style="font-size:0.9rem;">🔸 ${t.title} <span class="citation-chip" onclick="jumpToPage(${t.page})">📄 Page ${t.page}</span></div>`;
                
                (t.subtopics || []).forEach(st => {
                    html += `<div style="margin-left:16px; font-size:0.85rem; color:var(--text-muted);">• ${st.title} <span class="citation-chip" onclick="jumpToPage(${st.page})">📄 Page ${st.page}</span></div>`;
                });
                html += `</div>`;
            });
            html += `</div>`;
        });
        html += `</div>`;
    });

    container.innerHTML = html;
}

// Search Functionality
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
    resultsContainer.innerHTML = '<em>Searching extracted syllabus index...</em>';

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ doc_id: currentDocId, query: q })
        });
        const data = await response.json();

        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML = '<div>No direct matches found. Try alternative keywords.</div>';
            return;
        }

        let html = '';
        data.results.forEach(r => {
            html += `
                <div class="search-card">
                    <div class="search-card-meta">
                        <span>${r.section}</span>
                        <span class="citation-chip" onclick="jumpToPage(${r.page})">📄 Page ${r.page}</span>
                    </div>
                    <div style="font-size:0.9rem; color:var(--text-main);">${r.text}</div>
                </div>
            `;
        });
        resultsContainer.innerHTML = html;

    } catch (err) {
        resultsContainer.innerHTML = `<span style="color:var(--accent-rose)">Search error: ${err.message}</span>`;
    }
}

// Render Confidence Cards
function renderConfidenceBreakdown(conf) {
    const container = document.getElementById('confidenceGrid');
    if (!container || !conf) return;

    container.innerHTML = `
        <div class="conf-card"><div class="conf-name">Overall Confidence</div><div class="conf-val">${conf.overall}%</div></div>
        <div class="conf-card"><div class="conf-name">Text Quality</div><div class="conf-val">${conf.text_extraction}%</div></div>
        <div class="conf-card"><div class="conf-name">OCR Score</div><div class="conf-val">${conf.ocr}%</div></div>
        <div class="conf-card"><div class="conf-name">Course Detection</div><div class="conf-val">${conf.course_detection}%</div></div>
        <div class="conf-card"><div class="conf-name">Unit Detection</div><div class="conf-val">${conf.unit_detection}%</div></div>
        <div class="conf-card"><div class="conf-name">Topic Detection</div><div class="conf-val">${conf.topic_detection}%</div></div>
    `;
}

// Exports
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
