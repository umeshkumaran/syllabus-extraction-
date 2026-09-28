import os
import uuid
import json
import tempfile
import fitz  # PyMuPDF
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename

from extractor.pdf_reader import PDFReader
from extractor.structure_analyzer import StructureAnalyzer
from extractor.confidence import ConfidenceCalculator
from extractor.rag_engine import RAGEngine

app = Flask(__name__)

# Use system temp directory (/tmp on Linux/Vercel) to avoid read-only filesystem errors on serverless
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'syllabus_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB

# In-memory document storage session store
DOCUMENTS = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file part provided'}), 400

    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed.'}), 400

    doc_id = str(uuid.uuid4())
    filename = secure_filename(file.filename) or "uploaded_syllabus.pdf"
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{doc_id}_{filename}")
    file.save(pdf_path)

    try:
        # Step 1: Read PDF & Extract text (PyMuPDF + OCR fallback)
        reader = PDFReader(pdf_path)
        pages_data = reader.extract_all_pages()
        reader.close()

        # Step 2: Analyze Document Structure (Courses, Units, Topics, Outcomes, Books)
        analyzer = StructureAnalyzer(pages_data)
        hierarchy = analyzer.analyze()

        # Step 3: Calculate Extraction Confidence
        confidence_details = ConfidenceCalculator.calculate(pages_data, hierarchy)

        # Step 4: Initialize RAG Vector & Semantic Engine
        rag_engine = RAGEngine(pages_data, hierarchy)

        # Save into session memory
        DOCUMENTS[doc_id] = {
            "doc_id": doc_id,
            "filename": filename,
            "pdf_path": pdf_path,
            "total_pages": len(pages_data),
            "pages_data": pages_data,
            "hierarchy": hierarchy,
            "confidence": confidence_details,
            "rag_engine": rag_engine,
            "chat_history": []
        }

        return jsonify({
            'success': True,
            'doc_id': doc_id,
            'filename': filename,
            'total_pages': len(pages_data),
            'courses_detected': hierarchy['total_courses'],
            'confidence': confidence_details['overall'],
            'confidence_details': confidence_details,
            'hierarchy': hierarchy
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to process syllabus PDF: {str(e)}'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    doc_id = data.get('doc_id')
    question = data.get('question', '').strip()

    if not doc_id or doc_id not in DOCUMENTS:
        return jsonify({'error': 'Syllabus document not found or session expired. Please upload PDF again.'}), 404

    if not question:
        return jsonify({'error': 'Question cannot be empty.'}), 400

    doc = DOCUMENTS[doc_id]
    rag_engine = doc['rag_engine']
    chat_history = doc['chat_history']

    result = rag_engine.answer_question(question, chat_history)

    # Append to history
    doc['chat_history'].append({
        'question': question,
        'answer': result['answer']
    })

    return jsonify({
        'success': True,
        'answer': result['answer'],
        'sources': result['sources'],
        'source_pages': result.get('source_pages', []),
        'confidence': result['confidence']
    })

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json or {}
    doc_id = data.get('doc_id')
    query = data.get('query', '').strip()

    if not doc_id or doc_id not in DOCUMENTS:
        return jsonify({'error': 'Document not found.'}), 404

    doc = DOCUMENTS[doc_id]
    rag_engine = doc['rag_engine']
    results = rag_engine.retrieve(query, top_k=10)

    return jsonify({
        'success': True,
        'query': query,
        'results': [
            {
                'text': r['chunk']['text'],
                'page': r['chunk']['page'],
                'section': r['chunk']['section'],
                'course': r['chunk']['course'],
                'unit': r['chunk']['unit'],
                'score': r['score']
            }
            for r in results
        ]
    })

@app.route('/api/document/<doc_id>/pdf')
def get_pdf(doc_id):
    if doc_id not in DOCUMENTS:
        return "Document not found", 404
    pdf_path = DOCUMENTS[doc_id]['pdf_path']
    return send_file(pdf_path, mimetype='application/pdf')

@app.route('/api/document/<doc_id>/page_image/<int:page_num>')
def get_page_image(doc_id, page_num):
    if doc_id not in DOCUMENTS:
        return "Document not found", 404

    pdf_path = DOCUMENTS[doc_id]['pdf_path']
    try:
        doc = fitz.open(pdf_path)
        if page_num < 1 or page_num > len(doc):
            return "Page out of range", 400
        page = doc[page_num - 1]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        doc.close()
        return Response(img_bytes, mimetype='image/png')
    except Exception as e:
        return str(e), 500

@app.route('/api/document/<doc_id>/json')
def export_json(doc_id):
    if doc_id not in DOCUMENTS:
        return "Document not found", 404

    doc = DOCUMENTS[doc_id]
    export_payload = {
        "document": doc['filename'],
        "total_pages": doc['total_pages'],
        "confidence": doc['confidence'],
        "hierarchy": doc['hierarchy'],
        "raw_pages": [
            {
                "page": p["page"],
                "text": p["text"],
                "used_ocr": p["used_ocr"],
                "tables": p["tables"]
            }
            for p in doc['pages_data']
        ]
    }
    return Response(
        json.dumps(export_payload, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename={doc["filename"]}_extracted.json'}
    )

@app.route('/api/document/<doc_id>/text')
def export_text(doc_id):
    if doc_id not in DOCUMENTS:
        return "Document not found", 404

    doc = DOCUMENTS[doc_id]
    text_content = f"EXTRACTED SYLLABUS: {doc['filename']}\n"
    text_content += f"Total Pages: {doc['total_pages']}\n"
    text_content += f"Extraction Confidence: {doc['confidence']['overall']}%\n"
    text_content += "=" * 60 + "\n\n"

    for p in doc['pages_data']:
        text_content += f"--- PAGE {p['page']} ---\n"
        text_content += p['text'] + "\n\n"

    return Response(
        text_content,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment;filename={doc["filename"]}_extracted.txt'}
    )

@app.route('/api/document/<doc_id>/report')
def export_report(doc_id):
    if doc_id not in DOCUMENTS:
        return "Document not found", 404

    doc = DOCUMENTS[doc_id]
    h = doc['hierarchy']
    conf = doc['confidence']

    report = f"# EXTRACTION REPORT: {doc['filename']}\n\n"
    report += f"- **Total Pages:** {doc['total_pages']}\n"
    report += f"- **Courses Detected:** {h['total_courses']}\n"
    report += f"- **Estimated Extraction Confidence:** {conf['overall']}%\n"
    report += f"  - Text Quality: {conf['text_extraction']}%\n"
    report += f"  - OCR Score: {conf['ocr']}%\n"
    report += f"  - Course Detection: {conf['course_detection']}%\n"
    report += f"  - Unit Detection: {conf['unit_detection']}%\n"
    report += f"  - Topic Detection: {conf['topic_detection']}%\n\n"
    report += "---\n\n"

    report += "## Hierarchical Syllabus Structure\n\n"
    for course in h.get("courses", []):
        report += f"### Course: {course.get('code', '')} - {course.get('title', '')} (Page {course.get('start_page')})\n"
        for unit in course.get("units", []):
            report += f"#### Unit {unit.get('unit_number')}: {unit.get('title')} (Page {unit.get('page')})\n"
            for t in unit.get("topics", []):
                report += f"- {t.get('title')} (Page {t.get('page')})\n"
                for st in t.get("subtopics", []):
                    report += f"  - {st.get('title')} (Page {st.get('page')})\n"
        report += "\n"

    return Response(
        report,
        mimetype='text/markdown',
        headers={'Content-Disposition': f'attachment;filename={doc["filename"]}_report.md'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
