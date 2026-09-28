import re

class StructureAnalyzer:
    """
    Parses page data into a rich hierarchical structure (Institution, Programme, Branch, Semester, Course, Unit, Topics, Subtopics, Outcomes, Books, Matrices).
    Guarantees page number attribution for every node.
    """

    def __init__(self, pages_data):
        self.pages_data = pages_data
        self.doc_text_full = "\n".join([f"--- PAGE {p['page']} ---\n" + p["text"] for p in pages_data])

    def analyze(self):
        institution = self._extract_institution()
        programme = self._extract_programme()
        department = self._extract_department()
        batch_year = self._extract_batch_year()

        courses = self._extract_courses()
        course_outcomes = self._extract_global_outcomes()
        programme_outcomes = self._extract_programme_outcomes()
        textbooks, reference_books = self._extract_books()

        # Build hierarchical representation
        hierarchy = {
            "institution": institution,
            "programme": programme,
            "department": department,
            "batch_year": batch_year,
            "total_courses": len(courses),
            "courses": courses,
            "global_course_outcomes": course_outcomes,
            "programme_outcomes": programme_outcomes,
            "global_textbooks": textbooks,
            "global_reference_books": reference_books
        }

        return hierarchy

    def _extract_institution(self):
        # Look in first 3 pages for common university / college header patterns
        patterns = [
            r'([A-Z\s,.-]+(?:UNIVERSITY|COLLEGE|INSTITUTE|ACADEMY|POLYTECHNIC)[A-Z\s,.-]*)',
            r'(AUTONOMOUS INSTITUTION[^\n]*)'
        ]
        for p in self.pages_data[:3]:
            text = p["text"]
            for line in text.split('\n'):
                line_str = line.strip()
                if any(k in line_str.upper() for k in ["UNIVERSITY", "INSTITUTE OF TECHNOLOGY", "COLLEGE OF ENGINEERING"]):
                    if len(line_str) > 5 and len(line_str) < 120:
                        return {"name": line_str, "page": p["page"]}
        return None

    def _extract_programme(self):
        patterns = [
            r'(B\.E\.|B\.Tech|M\.E\.|M\.Tech|B\.Sc|M\.Sc|BCA|MCA|B\.A\.|M\.A\.|BACHELOR OF [^\n]+|MASTER OF [^\n]+)',
        ]
        for p in self.pages_data[:4]:
            for pat in patterns:
                m = re.search(pat, p["text"], re.IGNORECASE)
                if m:
                    return {"name": m.group(0).strip(), "page": p["page"]}
        return None

    def _extract_department(self):
        patterns = [
            r'(DEPARTMENT OF [^\n]+)',
            r'(BRANCH / SUBJECT:\s*[^\n]+)',
            r'(COMPUTER SCIENCE[^\n]*|MECHANICAL[^\n]*|ELECTRICAL[^\n]*|CIVIL[^\n]*|INFORMATION TECHNOLOGY[^\n]*)'
        ]
        for p in self.pages_data[:5]:
            for pat in patterns:
                m = re.search(pat, p["text"], re.IGNORECASE)
                if m:
                    return {"name": m.group(0).strip(), "page": p["page"]}
        return None

    def _extract_batch_year(self):
        pats = [
            r'(REGULATION[S]?\s*:?\s*\d{4})',
            r'(BATCH\s*:?\s*\d{4}-\d{4})',
            r'(ACADEMIC YEAR\s*:?\s*\d{4}-\d{4})'
        ]
        for p in self.pages_data[:3]:
            for pat in pats:
                m = re.search(pat, p["text"], re.IGNORECASE)
                if m:
                    return {"val": m.group(0).strip(), "page": p["page"]}
        return None

    def _extract_courses(self):
        """
        Detects individual courses, course codes, course titles, credits, units, topics, subtopics, outcomes, books, and tables.
        """
        courses = []
        current_course = None

        # Regex for course header detection e.g., "CS8591 COMPUTER NETWORKS L T P C" or "COURSE CODE: CS3451"
        course_code_pat = re.compile(
            r'(?:COURSE CODE|CODE|SUBJECT CODE)?\s*[:.-]?\s*([A-Z]{2,4}\s*\d{3,5}[A-Z]?)\s*[:.-]?\s*([^\n\d]+)', re.IGNORECASE
        )
        unit_header_pat = re.compile(
            r'^(UNIT\s+([I|V|X\d]+)\s*[:.-]?\s*([^\n]+))', re.IGNORECASE
        )
        credit_pat = re.compile(
            r'\bL\s*[:.-]?\s*(\d+)\s+T\s*[:.-]?\s*(\d+)\s+P\s*[:.-]?\s*(\d+)\s+C\s*[:.-]?\s*(\d+(?:\.\d+)?)\b', re.IGNORECASE
        )
        hours_pat = re.compile(r'(\d+)\s*(?:PERIODS|HOURS|HRS)', re.IGNORECASE)

        bloom_levels = ["remember", "understand", "apply", "analyse", "analyze", "evaluate", "create"]

        for p in self.pages_data:
            page_num = p["page"]
            text = p["text"]
            lines = text.split('\n')

            for line in lines:
                line_s = line.strip()
                if not line_s:
                    continue

                # Check for unit header
                unit_match = unit_header_pat.match(line_s)
                if unit_match and current_course:
                    unit_num = unit_match.group(2)
                    unit_title = unit_match.group(3).strip()
                    
                    # Search for unit hours if present
                    u_hours = None
                    h_m = hours_pat.search(unit_title)
                    if h_m:
                        u_hours = h_m.group(1)

                    current_unit = {
                        "unit_number": unit_num,
                        "title": unit_title,
                        "hours": u_hours,
                        "page": page_num,
                        "topics": [],
                        "raw_lines": []
                    }
                    current_course["units"].append(current_unit)
                    continue

                # Check for course header
                c_match = course_code_pat.search(line_s)
                if c_match:
                    code = c_match.group(1).strip()
                    title = c_match.group(2).strip()
                    
                    # Avoid false positives like "UNIT 1" or dates
                    if len(code) >= 4 and not code.startswith("UNIT"):
                        # Save previous course if any
                        if current_course:
                            self._finalize_course(current_course)
                            courses.append(current_course)

                        current_course = {
                            "code": code,
                            "title": title,
                            "start_page": page_num,
                            "pages": [page_num],
                            "credits_info": None,
                            "semester": self._detect_semester_context(line_s, text),
                            "units": [],
                            "outcomes": [],
                            "textbooks": [],
                            "reference_books": [],
                            "tables": p["tables"],
                            "co_po_matrix": [],
                            "raw_text_by_page": {page_num: [line_s]}
                        }
                        continue

                # If inside a course
                if current_course:
                    if page_num not in current_course["pages"]:
                        current_course["pages"].append(page_num)
                    
                    if page_num not in current_course["raw_text_by_page"]:
                        current_course["raw_text_by_page"][page_num] = []
                    current_course["raw_text_by_page"][page_num].append(line_s)

                    # Look for L T P C credit pattern
                    if not current_course["credits_info"]:
                        cred_m = credit_pat.search(line_s)
                        if cred_m:
                            current_course["credits_info"] = {
                                "L": cred_m.group(1),
                                "T": cred_m.group(2),
                                "P": cred_m.group(3),
                                "C": cred_m.group(4),
                                "page": page_num
                            }

                    # Add line to current unit if active
                    if current_course["units"]:
                        current_course["units"][-1]["raw_lines"].append((line_s, page_num))

        if current_course:
            self._finalize_course(current_course)
            courses.append(current_course)

        # Fallback if no specific course code regex matched (e.g. simple syllabus without codes)
        if not courses and self.pages_data:
            fallback_course = {
                "code": "SYLLABUS-01",
                "title": "Extracted Syllabus Document",
                "start_page": 1,
                "pages": [p["page"] for p in self.pages_data],
                "credits_info": None,
                "semester": None,
                "units": [],
                "outcomes": [],
                "textbooks": [],
                "reference_books": [],
                "tables": [],
                "co_po_matrix": [],
                "raw_text_by_page": {}
            }
            self._extract_units_fallback(fallback_course)
            self._finalize_course(fallback_course)
            courses.append(fallback_course)

        return courses

    def _detect_semester_context(self, line, text):
        m = re.search(r'SEMESTER\s*[:.-]?\s*([I|V|X\d]+)', text, re.IGNORECASE)
        if m:
            return m.group(1)
        return None

    def _finalize_course(self, course):
        """
        Parses topics, subtopics, outcomes (with Bloom's taxonomy), books, and CO-PO matrix for a course.
        """
        bloom_keywords = {
            "remember": ["remember", "recall", "list", "define", "state", "identify", "k1"],
            "understand": ["understand", "explain", "describe", "discuss", "classify", "k2"],
            "apply": ["apply", "solve", "calculate", "compute", "use", "demonstrate", "k3"],
            "analyse": ["analyse", "analyze", "compare", "contrast", "differentiate", "k4"],
            "evaluate": ["evaluate", "assess", "judge", "critique", "k5"],
            "create": ["create", "design", "construct", "formulate", "develop", "k6"]
        }

        # Finalize topics & subtopics inside units
        for unit in course["units"]:
            raw_lines = unit["raw_lines"]
            unit_topics = []
            current_topic = None

            for line_str, line_page in raw_lines:
                # Filter out books/outcomes headers if they appear inside unit block
                if any(k in line_str.upper() for k in ["TEXTBOOK", "REFERENCES", "COURSE OUTCOME", "OUTCOMES:"]):
                    break
                
                # Dynamic Topic / Subtopic extraction:
                # If line starts with bullet, hyphen, semicolon split, or numbering like 1.1 or a)
                subtopic_match = re.match(r'^(?:\d+\.\d+|\([a-z]\)|[a-z]\)|[-•])\s*(.+)', line_str)
                if subtopic_match and current_topic:
                    current_topic["subtopics"].append({
                        "title": subtopic_match.group(1).strip(),
                        "page": line_page
                    })
                elif len(line_str.split()) > 1:
                    # Treat line or comma-separated fragments as topic / subtopics
                    parts = [p.strip() for p in line_str.split(' - ') if p.strip()]
                    if len(parts) > 1:
                        top_title = parts[0]
                        sub_titles = [{"title": s, "page": line_page} for s in parts[1:]]
                        current_topic = {
                            "title": top_title,
                            "page": line_page,
                            "subtopics": sub_titles
                        }
                        unit_topics.append(current_topic)
                    else:
                        current_topic = {
                            "title": line_str,
                            "page": line_page,
                            "subtopics": []
                        }
                        unit_topics.append(current_topic)

            unit["topics"] = unit_topics
            del unit["raw_lines"]

        # Parse Course Outcomes, Textbooks, Reference Books, and Tables across course pages
        for page_num in course["pages"]:
            p_data = next((p for p in self.pages_data if p["page"] == page_num), None)
            if not p_data:
                continue

            text = p_data["text"]
            lines = text.split('\n')

            mode = None
            for line in lines:
                l_str = line.strip()
                l_upper = l_str.upper()

                if "COURSE OUTCOME" in l_upper or "OUTCOMES:" in l_upper or "CO1" in l_upper:
                    mode = "OUTCOMES"
                elif "TEXT BOOK" in l_upper or "TEXTBOOK" in l_upper:
                    mode = "TEXTBOOKS"
                elif "REFERENCE" in l_upper and "BOOK" in l_upper:
                    mode = "REFERENCES"
                elif "UNIT " in l_upper:
                    mode = None

                if mode == "OUTCOMES" and ("CO" in l_upper or re.match(r'^CO\d+', l_str, re.I) or re.match(r'^\d+\.', l_str)):
                    # Detect Bloom level
                    bloom_level = None
                    bloom_src = "none"
                    
                    for b_lvl, keywords in bloom_keywords.items():
                        for kw in keywords:
                            if re.search(r'\b' + kw + r'\b', l_str, re.IGNORECASE):
                                bloom_level = b_lvl
                                bloom_src = "printed" if kw in l_str.lower() else "inferred"
                                break
                        if bloom_level:
                            break

                    course["outcomes"].append({
                        "text": l_str,
                        "page": page_num,
                        "bloom_level": bloom_level,
                        "bloom_source": bloom_src
                    })

                elif mode == "TEXTBOOKS" and l_str and not "TEXT BOOK" in l_upper:
                    course["textbooks"].append({"title": l_str, "page": page_num})

                elif mode == "REFERENCES" and l_str and not "REFERENCE" in l_upper:
                    course["reference_books"].append({"title": l_str, "page": page_num})

            # Check tables for CO-PO mapping
            for table in p_data["tables"]:
                if self._is_copo_table(table):
                    course["co_po_matrix"].append({
                        "page": page_num,
                        "matrix": table
                    })

    def _extract_units_fallback(self, course):
        unit_pat = re.compile(r'^(UNIT\s+[I|V|X\d]+[^\n]*)', re.I)
        for p in self.pages_data:
            page_num = p["page"]
            lines = p["text"].split('\n')
            current_u = None
            for line in lines:
                m = unit_pat.match(line.strip())
                if m:
                    current_u = {
                        "unit_number": str(len(course["units"]) + 1),
                        "title": m.group(1).strip(),
                        "hours": None,
                        "page": page_num,
                        "topics": []
                    }
                    course["units"].append(current_u)
                elif current_u and line.strip():
                    current_u["topics"].append({
                        "title": line.strip(),
                        "page": page_num,
                        "subtopics": []
                    })

    def _is_copo_table(self, table):
        if not table or len(table) < 2:
            return False
        header = " ".join([str(c) for c in table[0]]).upper()
        return "CO" in header or "PO" in header or "PO1" in header

    def _extract_global_outcomes(self):
        outcomes = []
        for p in self.pages_data:
            lines = p["text"].split('\n')
            for line in lines:
                if "CO" in line or "Course Outcome" in line:
                    outcomes.append({"text": line.strip(), "page": p["page"]})
        return outcomes

    def _extract_programme_outcomes(self):
        pos = []
        for p in self.pages_data:
            lines = p["text"].split('\n')
            for line in lines:
                if re.match(r'^PO\d+', line.strip(), re.I) or "PROGRAMME OUTCOME" in line.upper():
                    pos.append({"text": line.strip(), "page": p["page"]})
        return pos

    def _extract_books(self):
        textbooks = []
        refbooks = []
        for p in self.pages_data:
            lines = p["text"].split('\n')
            is_tb = False
            is_rb = False
            for line in lines:
                l_u = line.upper()
                if "TEXTBOOK" in l_u or "TEXT BOOK" in l_u:
                    is_tb = True
                    is_rb = False
                    continue
                elif "REFERENCE BOOK" in l_u or "REFERENCES:" in l_u:
                    is_rb = True
                    is_tb = False
                    continue
                elif "UNIT" in l_u:
                    is_tb = False
                    is_rb = False

                if is_tb and line.strip():
                    textbooks.append({"title": line.strip(), "page": p["page"]})
                elif is_rb and line.strip():
                    refbooks.append({"title": line.strip(), "page": p["page"]})

        return textbooks, refbooks
