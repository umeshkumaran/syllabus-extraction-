# AI Syllabus PDF Chatbot

An intelligent, page-grounded web application that processes any college or university syllabus PDF, dynamically extracts hierarchical course structures, and provides a RAG chatbot interface with exact page citations and interactive PDF navigation.

---

## 🌟 Key Features

- **Universal PDF Support**: Upload any syllabus PDF (scanned or native text) with automatic EasyOCR / PyTesseract fallback.
- **Hierarchical Extraction**: Dynamically parses Institution, Programme, Department, Semesters, Courses, Units, Topics, Subtopics, Course Outcomes (with Bloom's Taxonomy), Books, and CO-PO Matrices.
- **Estimated Extraction Confidence**: Calculates confidence percentage based on text quality, OCR performance, and metadata coverage.
- **Grounded RAG Chatbot**: Answers user queries strictly from the uploaded PDF text. Never hallucinates outside knowledge unless explicitly requested.
- **Clickable PDF Citations**: Every answer includes source page links (e.g., `📄 Page 15`). Clicking a citation automatically navigates the embedded PDF viewer to that exact page.
- **Multi-Turn Memory**: Handles follow-up questions and pronoun resolution (e.g., "it", "its units", "which course").
- **Search & Full Syllabus Views**: Direct keyword search across chunks, plus an interactive hierarchical accordion tree view.
- **Data Export**: Export structured JSON schemas, plain text extractions, and Markdown reports.

---

## 🛠️ Technology Stack

- **Backend**: Python, Flask, PyMuPDF (`fitz`), `pdfplumber`, `scikit-learn`, `EasyOCR`, `PyTesseract`, `FAISS`
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism / Dark Theme), JavaScript (ES6+)

---

## 🚀 Quick Start Guide

### 1. Clone the Repository

```bash
git clone https://github.com/umeshkumaran/syllabus-extraction-.git
cd syllabus-extraction-
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

### 4. Open in Browser

Navigate to **`http://localhost:5000`** in your browser.

---

## 📄 License

MIT License
