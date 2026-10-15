Build a complete working web application called:

**AI Syllabus PDF Chatbot**

The application must allow a user to upload ANY college/university syllabus PDF and then chat with that uploaded syllabus.

The core idea is:

**Upload PDF → Extract syllabus → Index content with page numbers → display the topic in pdf for user reference  with subtopics→  User asks questions → Chatbot answers from PDF → Show exact source page numbers->no example must be used the answer responce must be accroding to the uploaded pdf from the user**

This is NOT a generic AI chatbot.

The chatbot must use the uploaded syllabus as its primary and only knowledge source for syllabus-related questions.

IMPORTANT:

* Never hardcode a particular college.
* Never hardcode course names.
* Never hardcode units or topics.
* Never hardcode page numbers.
* Never use example syllabus content as actual application data.
* Everything displayed after upload must come from the uploaded PDF.
* The application must work with completely different college syllabus formats.
* Never invent missing syllabus information.
* Never correct mistakes or spelling in the source document.
* Preserve source terminology and wording as closely as possible.
* If information is not present in the PDF, clearly say that it was not found in the uploaded syllabus.

==================================================

1. APPLICATION CONCEPT
   ==================================================

Create a chatbot-style interface.

Main screen:

---

## AI SYLLABUS PDF CHATBOT

Upload your syllabus PDF

[ Drag & Drop PDF Here ]

[ Browse PDF ]

Selected file:
[filename.pdf]

[ Process Syllabus ]

After processing:

---

## SYLLABUS LOADED

File: filename.pdf
Pages: XX
Courses detected: XX
Extraction confidence: XX%

[ View Syllabus ]
[ Start Chat ]
--------------

Then show a chatbot interface.

LEFT SIDE:
PDF/document navigation

RIGHT SIDE:
AI chatbot

==================================================
2. PDF UPLOAD
=============

Allow:

* Drag and drop PDF
* Browse PDF
* Upload
* Remove PDF
* Upload another PDF

Only PDF files should be accepted.

After uploading, process the entire PDF.

Show processing stages:

Reading PDF
↓
Extracting text
↓
Detecting document structure
↓
Detecting courses
↓
Detecting semesters/sections
↓
Detecting units
↓
Detecting topics/subtopics
↓
Detecting outcomes
↓
Detecting books/references
↓
Indexing page references
↓
Calculating extraction confidence
↓
Ready for questions

==================================================
3. FULL SYLLABUS EXTRACTION
===========================

After processing the PDF, automatically create a structured representation of everything the PDF contains.

For example, the application should dynamically identify information such as:

* Institution name
* Programme
* Batch/year
* Departments/branches
* Semesters
* Courses
* Course codes
* Course titles
* Credits
* Lecture/tutorial/practical information
* Units
* Unit titles
* Unit hours
* Topics
* Subtopics
* Course outcomes
* Programme outcomes
* CO-PO mapping
* Text books
* Reference books
* Notes
* Footnotes
* Special requirements
* Electives
* Other syllabus information

Only extract fields that actually exist in the PDF.

If a particular syllabus does not contain a field, do not create fake data.

==================================================
4. SYLLABUS VIEW
================

Create a button:

**View Extracted Syllabus**

When clicked, display the syllabus hierarchically.

Structure:

Institution
↓
Programme
↓
Department / Branch
↓
Semester
↓
Course
↓
Unit
↓
Topics
↓
Subtopics

Every extracted section must display:

**Source: PDF Page X**

The page number must refer to the actual page of the uploaded PDF.

The user should be able to click the page number and open that page in the PDF viewer.

==================================================
5. CHATBOT
==========

The main feature is:

**Chat with your syllabus**

The user can type natural-language questions.

The chatbot should understand queries about the uploaded syllabus.

Questions can ask for:

* entire syllabus
* courses
* specific course
* specific semester
* specific unit
* specific topic
* specific subtopic
* course credits
* course code
* course outcomes
* programme outcomes
* Bloom's taxonomy
* CO-PO mapping
* books
* references
* page location
* comparison of syllabus sections
* whether a topic/course exists
* where information is located in the PDF

The chatbot must dynamically retrieve the relevant portions of the uploaded PDF before answering.

==================================================
6. SOURCE PAGE NUMBER IS MANDATORY
==================================

Every answer must include source page information.

Use a format such as:

**Source: PDF Page 15**

or

**Source: PDF Pages 15–16**

For multiple pieces of information:

Topic: [extracted topic]
Source: PDF Page X

Subtopic: [extracted subtopic]
Source: PDF Page X

Course: [extracted course]
Source: PDF Page X

The page number must always come from the uploaded PDF.

Do NOT fabricate page numbers.

==================================================
7. CLICKABLE CITATIONS
======================

Make the page references clickable.

Example UI:

**Source: Page 15**

When the user clicks "Page 15":

→ Open the PDF viewer
→ Navigate automatically to page 15
→ Highlight or visually focus on the relevant extracted section where technically possible.

This should make the application behave like a document-grounded research chatbot.

==================================================
8. ANSWER FORMAT
================

When a user asks about a topic, answer naturally but structure the response clearly.

For example:

### Result

[Information extracted from syllabus]

### Topics / Subtopics

[Topics and subtopics actually present in PDF]

### Source

PDF Page XX

Do not add information from general AI knowledge unless the user specifically requests outside knowledge.

For syllabus questions, source-grounded information has priority.

==================================================
9. WHEN USER ASKS FOR FULL SYLLABUS
===================================

If the user asks for:

"Give me the syllabus"

or

"Show the complete syllabus"

or an equivalent request,

do NOT simply dump raw PDF text.

Instead, organize the extracted content hierarchically:

Programme
→ Department
→ Semester
→ Course
→ Unit
→ Topic
→ Subtopic

Keep the source wording intact.

Every major section should include its page number.

==================================================
10. TOPIC + SUBTOPIC EXTRACTION
===============================

This is extremely important.

When the PDF contains:

Unit
Topic
Subtopic

the chatbot should preserve that hierarchy.

For example, internally represent:

Unit
Topic
Subtopic
Subtopic

Do not flatten all text into one paragraph.

Determine hierarchy dynamically from the document layout, numbering, indentation, headings and semantic structure.

Do not assume that every PDF uses the same formatting.

==================================================
11. COURSE EXTRACTION
=====================

Detect all courses in the PDF.

For every detected course, store:

* course code
* course title
* starting page
* relevant pages
* semester
* branch/department when available
* credits and course structure when available

Create a searchable course index.

Do not assume a fixed number of courses.

==================================================
12. USER QUERY RETRIEVAL
========================

Implement Retrieval-Augmented Generation (RAG).

Pipeline:

Uploaded PDF
↓
Extract text page by page
↓
Preserve page numbers
↓
Detect sections and tables
↓
Chunk content
↓
Create embeddings/index
↓
Store metadata:
page number
section
course
unit
topic
↓
Retrieve relevant chunks for each user question
↓
Generate answer ONLY from retrieved syllabus content
↓
Attach source page numbers
↓
Display answer

The retrieval system should prioritize:

1. Exact keyword matches
2. Semantic matches
3. Course/section metadata
4. Page context

==================================================
13. PDF PAGE-AWARE INDEX
========================

Every chunk of extracted information must store metadata like:

{
"text": "...",
"page": 15,
"section": "...",
"course": "...",
"unit": "...",
"topic": "..."
}

This is mandatory because the chatbot must return accurate source pages.

==================================================
14. OCR SUPPORT
===============

Support both:

1. Text-based PDFs
2. Scanned/image PDFs

Pipeline:

First attempt normal PDF text extraction.

If a page has insufficient or unusable text:

→ perform OCR on that page.

Store OCR text together with the original PDF page number.

Use OCR confidence where available.

==================================================
15. TABLE EXTRACTION
====================

The syllabus may contain tables such as:

Course lists
Semester tables
Credit tables
CO-PO matrices
Book lists

Detect and preserve tables.

Do not convert table values into invented prose.

For CO-PO mapping:

preserve the exact values/symbols shown in the PDF.

==================================================
16. BLOOM'S TAXONOMY
====================

When Bloom's taxonomy levels appear in the PDF, extract them.

Allowed normalized values:

remember
understand
apply
analyse
evaluate
create

Also store:

bloom_source

where:

printed = explicitly stated in the document

inferred = determined from the document

Do not invent a Bloom level when there is insufficient evidence.

==================================================
17. FAITHFULNESS RULE
=====================

The uploaded PDF is the source of truth.

The system must NOT:

* rewrite syllabus text
* improve grammar
* correct spelling
* expand abbreviations
* add outside topics
* add missing outcomes
* invent books
* invent mappings
* invent page numbers
* supply standard programme outcomes that are absent

If the PDF contains a mistake, preserve it.

If something cannot be extracted, report it.

==================================================
18. "NOT FOUND IN PDF"
======================

When the user asks a question and the answer is not present in the uploaded PDF, respond clearly:

**This information was not found in the uploaded syllabus PDF.**

Do not answer from general knowledge.

Also provide:

**Relevant source pages checked: [pages if available]**

when technically possible.

==================================================
19. EXTRACTION CONFIDENCE
=========================

After processing the document, calculate:

**Estimated Extraction Confidence: XX%**

Do NOT falsely claim that this percentage is ground-truth accuracy.

Calculate the confidence from actual extraction signals such as:

* PDF text extraction quality
* OCR confidence
* section detection
* course detection
* topic detection
* table extraction
* metadata completeness
* retrieval confidence

Show:

Overall Extraction Confidence: XX%

Optionally show:

Text Extraction: XX%
OCR: XX%
Course Detection: XX%
Unit Detection: XX%
Topic Detection: XX%
Table Detection: XX%
Outcome Detection: XX%

Use the label:

**Estimated Extraction Confidence**

not "guaranteed accuracy".

==================================================
20. CHAT MEMORY
===============

After the PDF is uploaded, maintain conversation context.

Example:

User:
"What courses are available in Computer Science?"

Bot:
[answer]

User:
"Which one has the highest number of credits?"

Bot:
Use the already uploaded syllabus and the previous conversation context.

User:
"Show me its units."

Bot:
Use the course identified from the previous message.

The chatbot should understand pronouns and follow-up questions using conversation context.

==================================================
21. MULTI-COURSE DOCUMENTS
==========================

A PDF may contain multiple departments and many courses.

The application must handle this.

Create an internal document structure:

PDF
→ Department/Branch
→ Semester
→ Course
→ Unit
→ Topic
→ Subtopic

Do not assume there is only one department.

==================================================
22. SEARCH + CHAT
=================

Provide both:

**Chat mode**

and

**Search mode**

Search should allow direct searching through extracted syllabus content.

Display:

Search result
Relevant text
Course
Section
PDF page

==================================================
23. PDF VIEWER
==============

Keep a PDF viewer inside the application.

Suggested layout:

---

| PDF Viewer       | Chatbot            |
|                  |                    |
| Page 15          | User question      |
|                  |                    |
| PDF content      | AI answer          |
|                  |                    |
|                  | Source Page 15     |
-----------------------------------------

The PDF viewer should synchronize with chatbot citations.

==================================================
24. EXPORT
==========

Allow:

Download Extracted JSON
Download Extracted Text
Download Report

The JSON should contain page references.

Use a structure based on:

{
"document": "...",
"courses": [],
"selected_course": {},
"units": [],
"course_outcomes": [],
"programme_outcomes": [],
"co_po_matrix": {},
"books": [],
"not_extracted": []
}

The actual values must always come from the uploaded PDF.

==================================================
25. API / BACKEND
=================

Use:

Frontend:
HTML
CSS
JavaScript / React

Backend:
Python Flask or FastAPI

PDF processing:
PyMuPDF / pdfplumber

OCR:
EasyOCR or another reliable OCR library

Vector search:
FAISS / Chroma / another suitable vector database

LLM:
Use an appropriate API/model for document question answering if needed.

The LLM must receive retrieved information from the uploaded document.

Do NOT let the LLM freely answer syllabus questions from its general training knowledge.

==================================================
26. HALLUCINATION PROTECTION
============================

Before returning an answer:

1. Retrieve relevant PDF chunks.
2. Check that the answer is supported by retrieved text.
3. Attach source page number(s).
4. If evidence is insufficient, say:
   "This information could not be reliably extracted from the uploaded PDF."

Never generate unsupported syllabus information.

==================================================
27. SOURCE TRACEABILITY
=======================

For each answer maintain:

{
"answer": "...",
"sources": [
{
"page": 15,
"text": "...",
"section": "..."
}
],
"confidence": 0.XX
}

The UI should display these sources under the chatbot answer.

==================================================
28. TEST WITH THE UPLOADED PDF
==============================

Use the uploaded syllabus PDF only as a TEST INPUT during development.

Do NOT hardcode anything from it into the application.

The system should be able to process it dynamically and discover its content.

After testing, the application must also work when a completely different college syllabus PDF is uploaded.

==================================================
29. GENERALIZATION
==================

The evaluation document may have a completely different layout.

Therefore do NOT write:

if college == ...
if course == ...
if page == ...
if title == ...

Do not build rules specifically for one PDF.

Use general document understanding.

The problem statement explicitly requires the application to work with an unseen college/document format, and its extraction is judged for completeness and faithfulness.

==================================================
30. REQUIRED FINAL UI
=====================

The finished application should have:

HOME
↓
UPLOAD PDF
↓
PROCESS PDF
↓
SYLLABUS OVERVIEW
↓
CHAT WITH SYLLABUS

Main chatbot page:

---

AI SYLLABUS CHATBOT

Uploaded: [filename.pdf]

Courses: XX
Pages: XX
Estimated Extraction Confidence: XX%

---

PDF VIEWER                    CHAT

[PDF PAGE]                    Ask anything about your syllabus...

```
                          [User question]

                          [AI response]

                          Sources:
                          Page XX
                          Page XX
```

---

Buttons:

[View Full Syllabus]
[Courses]
[Search]
[Download JSON]
[Download Report]
[Upload New PDF]

==================================================
31. IMPORTANT FINAL INSTRUCTION
===============================

Do not create only a frontend prototype.

Build the complete functional system:

PDF upload
→ full PDF extraction
→ OCR when necessary
→ page-aware indexing
→ syllabus structure extraction
→ topic/subtopic extraction
→ searchable knowledge base
→ chatbot
→ user-query retrieval
→ grounded answer generation
→ source page citations
→ clickable PDF page navigation
→ confidence estimation
→ JSON export

The primary user experience must be:

**"Upload my syllabus PDF and ask questions about it."**

The chatbot must answer based on the uploaded syllabus and tell the user exactly which PDF page contains the information.

Do not use fabricated sample syllabus content anywhere in the working application.
**Add a New Feature to My Existing AI Syllabus PDF Chatbot: Smart Reference Book Topic Finder**

Important: Extend my existing application by adding this feature. Do not replace, rewrite, remove, or break my existing syllabus extraction functionality. Preserve the current UI, backend, working features, database, and project structure wherever possible. First inspect the existing project and understand how it works, then integrate this feature into it.

### 1. New feature objective

Add a feature called **Smart Reference Book Topic Finder**.

The application must allow users to upload a reference book or textbook PDF and search for any topic or subtopic within the document.

The topic may be listed in the book's printed index or table of contents, but it may also be completely absent from both. Even if the topic is not listed in the index, the system must search the actual content of the entire PDF and find the relevant explanation wherever it appears.

Example:

A user uploads a Mathematics reference book and searches for **"Eigenvalue"**.

If "Eigenvalue" is not mentioned in the printed index but its explanation appears in the body of the book, the system must locate the explanation, extract the relevant content, and identify the page on which the explanation starts and the page on which it ends.

This is an example of expected behaviour, not a hardcoded topic. The application must work with arbitrary topics and reference books.

### 2. Search the entire PDF, not just the index

When a reference book is uploaded:

- Process every page of the PDF.
- Extract text from the main body, headings, subheadings, paragraphs, tables, equations where possible, captions, and footnotes.
- Use OCR on scanned pages when normal text extraction is insufficient.
- Treat the printed index and table of contents as additional sources of clues, not as the only search source.
- Build a searchable, page-aware index of the entire document.
- Never assume that a topic does not exist merely because it is missing from the printed index.

### 3. Implement intelligent topic search

Use a combination of:

- Exact keyword search.
- Partial-word and phrase matching where appropriate.
- Synonym and related-term matching.
- Semantic search to identify passages discussing the requested concept even when the exact phrase is absent.
- Context-based ranking to identify the most relevant explanation.

Search results must be grounded in text extracted from the uploaded PDF.

For example, when searching for "Eigenvalue", the system may find an explanation under a related heading or within a paragraph that uses related mathematical terminology.

Do not automatically treat every mention of a topic as its full explanation. Distinguish between a brief mention, a definition, a detailed explanation, an example, and a separate occurrence elsewhere in the book.

### 4. Detect the complete explanation and its page range

For each relevant result, attempt to identify:

- Topic name as searched.
- Actual heading or section title, if present.
- Explanation start page.
- Explanation end page.
- Relevant extracted content.
- Confidence in the topic match.
- Confidence in the detected start and end boundaries.

Use headings, subheadings, paragraph continuity, page transitions, equations, examples, and the next section heading to estimate where the explanation begins and ends.

A topic may start in the middle of a page and continue across multiple pages. The system must support explanations spanning multiple pages.

Do not assume that a topic ends on the same page where it first appears. Do not include the entire remainder of the book as the explanation.

If the topic appears in multiple independent sections, return separate results for each occurrence rather than combining unrelated passages into one section.

If the exact boundaries cannot be determined reliably, show an estimated page range and clearly label it as uncertain. Never invent exact page boundaries.

### 5. Display the search results

For each matching section, display:

- Topic searched.
- Section or heading found.
- Short preview of the explanation.
- Start page.
- End page.
- Match confidence.
- A button or clickable page citation labelled **Open in PDF**.

Example interface:

Search: Eigenvalue

Result 1:
- Heading: [Actual heading extracted from the book]
- Explanation: [Actual extracted text]
- Starts at: PDF page XX
- Ends at: PDF page XX
- [Open in PDF]

The placeholder values above describe the interface only. Never display them as actual extracted results.

### 6. Clickable citations and PDF navigation

Integrate the feature with the existing PDF viewer.

When the user clicks a page citation or the "Open in PDF" control:

- Open the uploaded PDF in the existing viewer.
- Navigate to the correct physical PDF page.
- If the explanation spans multiple pages, allow the user to navigate to each page in the detected range.
- Highlight the relevant text on the page wherever reliable text coordinates are available.
- Preserve the distinction between the physical PDF page number and the printed page number shown in the book.
- If highlighting is unavailable for a scanned or poorly extracted page, still navigate to the correct page and display the relevant extracted passage separately.

Store page numbers and text-position metadata with each indexed passage so citations remain connected to their original locations.

### 7. Add a search interface without damaging the existing syllabus features

Keep the existing syllabus extraction and chatbot workflow unchanged.

Add an appropriate option to select the document task:

- Syllabus Extraction and Chat
- Reference Book Topic Finder

For reference book mode, provide:

- PDF upload.
- Topic search box.
- Search button.
- Search results.
- Extracted explanation.
- Start and end page numbers.
- Clickable citations.
- PDF viewer navigation and text highlighting.

Reuse the existing PDF-processing, OCR, indexing, retrieval, and PDF-viewer components wherever possible. Do not duplicate existing functionality unnecessarily.

### 8. Technical implementation

Adapt the implementation to the technologies already used by this project.

For PDF processing, use the existing PDF extraction library or a suitable library such as PyMuPDF.

For scanned documents, reuse the existing OCR system or add OCR only if necessary.

Use full-text keyword search alongside semantic retrieval. Preserve page-level metadata and, when possible, text-block coordinates.

Implement topic-boundary detection as a separate component so it can be improved and tested independently.

Use the existing chatbot or retrieval pipeline to display source-grounded explanations. Do not train a new AI model unless there is a demonstrated need.

### 9. Accuracy and reliability rules

- Never hardcode Eigenvalue or any other specific topic.
- Never hardcode a reference book, author, page number, or expected result.
- Never rely exclusively on the printed index or table of contents.
- Never fabricate extracted explanations, page ranges, or citations.
- Distinguish an exact match from a related-concept match.
- Return multiple relevant locations when appropriate.
- If a topic is genuinely not found, clearly report that it was not found in the searchable PDF content.
- If OCR or extraction quality is poor, disclose the limitation.
- Preserve the original wording of the source when displaying extracted passages.
- Do not claim that a topic is absent solely because exact keyword search returned no results.

### 10. Testing and acceptance criteria

Test the new feature using reference books that were not used during development.

Verify that:

1. A topic listed in the printed index can be found.
2. A topic missing from the printed index but present in the main content can be found.
3. A topic explained across multiple pages returns a reasonable start and end page.
4. A topic mentioned in multiple sections returns separate relevant locations.
5. Clicking a citation opens the correct PDF page.
6. Text highlighting works where reliable text-position information is available.
7. Scanned PDFs are processed using OCR when required.
8. A topic absent from the document is reported honestly.
9. The system does not return unrelated passages merely because they contain similar words.
10. The existing syllabus extraction and chatbot features continue to work.

First inspect the current codebase, then implement this feature within the existing project. Do not create a separate replacement application. After implementation, explain which files were changed, how the new feature works, and how I can test it using my own reference book PDF.