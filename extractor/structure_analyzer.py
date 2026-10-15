import re

class StructureAnalyzer:
    """
    Parses PDF page data into a rich hierarchical structure:
    Institution → Programme → Department/Branch → Semester → Course → Unit → Topics → Subtopics
    with Course Outcomes (Bloom's taxonomy), Books, and CO-PO Matrices.
    Guarantees exact page number attribution for every node.
    Works dynamically across diverse college syllabus formats without hardcoding.
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
        """
        Dynamically finds University / Institute / College name from initial pages.
        """
        patterns = [
            r'([A-Z\s,.-]+(?:UNIVERSITY|COLLEGE OF ENGINEERING|INSTITUTE OF TECHNOLOGY|POLYTECHNIC|ACADEMY)[A-Z\s,.-]*)',
            r'(AUTONOMOUS INSTITUTION[^\n]*)'
        ]
        for p in self.pages_data[:4]:
            text = p["text"]
            for line in text.split('\n'):
                line_str = line.strip()
                if any(k in line_str.upper() for k in ["UNIVERSITY", "INSTITUTE OF TECHNOLOGY", "COLLEGE OF ENGINEERING", "NATIONAL INSTITUTE", "INDIAN INSTITUTE"]):
                    if 5 < len(line_str) < 140 and not line_str.upper().startswith("COURSE"):
                        return {"name": line_str, "page": p["page"]}
        return None

    def _extract_programme(self):
        """
        Detects Programme (B.E., B.Tech, M.Tech, MCA, etc.) from initial pages.
        """
        patterns = [
            r'\b(B\.E\.|B\.Tech|M\.E\.|M\.Tech|B\.Sc|M\.Sc|BCA|MCA|B\.A\.|M\.A\.|B\.Com|M\.Com|BACHELOR OF [^\n]+|MASTER OF [^\n]+)\b',
        ]
        for p in self.pages_data[:5]:
            for pat in patterns:
                m = re.search(pat, p["text"], re.IGNORECASE)
                if m:
                    return {"name": m.group(0).strip(), "page": p["page"]}
        return None

    def _extract_department(self):
        """
        Detects Department / Branch.
        """
        patterns = [
            r'(DEPARTMENT OF [^\n]+)',
            r'(BRANCH / DISCIPLINE:\s*[^\n]+)',
            r'(COMPUTER SCIENCE[^\n]*|INFORMATION TECHNOLOGY[^\n]*|MECHANICAL[^\n]*|ELECTRICAL[^\n]*|ELECTRONICS[^\n]*|CIVIL[^\n]*|ARTIFICIAL INTELLIGENCE[^\n]*)'
        ]
        for p in self.pages_data[:5]:
            for pat in patterns:
                m = re.search(pat, p["text"], re.IGNORECASE)
                if m:
                    val = m.group(0).strip()
                    if len(val) < 100:
                        return {"name": val, "page": p["page"]}
        return None

    def _extract_batch_year(self):
        """
        Detects Regulation, Batch, or Academic Year.
        """
        pats = [
            r'(REGULATION[S]?\s*[:.-]?\s*\d{4})',
            r'(BATCH\s*[:.-]?\s*\d{4}\s*-\s*\d{4})',
            r'(ACADEMIC YEAR\s*[:.-]?\s*\d{4}\s*-\s*\d{4})',
            r'(CURRICULUM\s*&\s*SYLLABUS\s*[:.-]?\s*\d{4})'
        ]
        for p in self.pages_data[:4]:
            for pat in pats:
                m = re.search(pat, p["text"], re.IGNORECASE)
                if m:
                    return {"val": m.group(0).strip(), "page": p["page"]}
        return None

    def _extract_courses(self):
        """
        Detects all courses in the PDF with code, title, starting page, units, topics, subtopics,
        outcomes (Bloom levels), books, and CO-PO matrices.
        Supports varied college course code formats.
        """
        courses = []
        current_course = None

        # Regex for course codes:
        # 1. Letters then numbers: CS8591, MA3151, CS3451, CS-8591, CSE301
        # 2. Numbers then letters: 18CS51, 21CS42, 22MA101
        # 3. Explicit labels: COURSE CODE: CS3451, CODE: CS101, SUBJECT CODE: ...
        course_code_pat = re.compile(
            r'(?:COURSE CODE|CODE|SUBJECT CODE|PAPER CODE)?\s*[:.-]?\s*\b([A-Z]{2,5}[-\s]?\d{3,5}[A-Z]?|\d{2}[A-Z]{2,4}\s*\d{2,4}[A-Z]?)\b\s*[:.-]?\s*([^\n\d]+)?',
            re.IGNORECASE
        )
        
        # Explicit course title lines: COURSE: Data Structures, SUBJECT: Computer Networks
        explicit_title_pat = re.compile(
            r'^(?:COURSE TITLE|COURSE NAME|SUBJECT|COURSE)\s*[:.-]\s*([^\n]+)', re.IGNORECASE
        )

        # Unit / Module / Chapter header pattern
        unit_header_pat = re.compile(
            r'^(?:UNIT|MODULE|CHAPTER|PART)\s+([I|V|X\d]+)\s*[:.-]?\s*([^\n]*)', re.IGNORECASE
        )

        credit_pat = re.compile(
            r'\bL\s*[:.-]?\s*(\d+)\s+T\s*[:.-]?\s*(\d+)\s+P\s*[:.-]?\s*(\d+)\s+C\s*[:.-]?\s*(\d+(?:\.\d+)?)\b', re.IGNORECASE
        )
        alt_credit_pat = re.compile(
            r'\bCREDITS?\s*[:.-]?\s*(\d+(?:\.\d+)?)\b|\((\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)\)', re.IGNORECASE
        )
        hours_pat = re.compile(r'(\d+)\s*(?:PERIODS|HOURS|HRS)', re.IGNORECASE)

        for p in self.pages_data:
            page_num = p["page"]
            text = p["text"]
            lines = text.split('\n')

            for line in lines:
                line_s = line.strip()
                if not line_s:
                    continue

                # 1. Check for Unit/Module Header
                unit_match = unit_header_pat.match(line_s)
                if unit_match and current_course:
                    unit_num = unit_match.group(1)
                    unit_title = unit_match.group(2).strip() or f"Unit {unit_num}"
                    
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

                # 2. Check for Course Header
                c_match = course_code_pat.search(line_s)
                is_explicit = explicit_title_pat.match(line_s)
                
                detected_code = None
                detected_title = None

                if is_explicit:
                    detected_title = is_explicit.group(1).strip()
                    detected_code = f"CRS-{len(courses)+1:02d}"
                elif c_match:
                    code_cand = c_match.group(1).strip()
                    title_cand = (c_match.group(2) or "").strip()
                    
                    # Prevent false matches on standard terms like "UNIT 1", "PAGE 12", "REG 2021"
                    if len(code_cand) >= 4 and not any(code_cand.upper().startswith(k) for k in ["UNIT", "PAGE", "REG", "TABLE", "BATCH"]):
                        detected_code = code_cand
                        detected_title = title_cand

                if detected_code:
                    # Clean title if empty or too short
                    if not detected_title or len(detected_title) < 3:
                        # Try to look at line after or cleaned text
                        detected_title = f"Course {detected_code}"

                    # If this is a new course header
                    if not current_course or current_course["code"].replace(" ", "").upper() != detected_code.replace(" ", "").upper():
                        if current_course:
                            self._finalize_course(current_course)
                            courses.append(current_course)

                        current_course = {
                            "code": detected_code,
                            "title": detected_title,
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

                # 3. If inside a course
                if current_course:
                    if page_num not in current_course["pages"]:
                        current_course["pages"].append(page_num)
                    
                    if page_num not in current_course["raw_text_by_page"]:
                        current_course["raw_text_by_page"][page_num] = []
                    current_course["raw_text_by_page"][page_num].append(line_s)

                    # Look for credits
                    if not current_course["credits_info"]:
                        cred_m = credit_pat.search(line_s)
                        if cred_m:
                            current_course["credits_info"] = {
                                "L": cred_m.group(1),
                                "T": cred_m.group(2),
                                "P": cred_m.group(3),
                                "C": cred_m.group(4),
                                "credits_total": float(cred_m.group(4)),
                                "page": page_num
                            }
                        else:
                            alt_m = alt_credit_pat.search(line_s)
                            if alt_m:
                                if alt_m.group(1):
                                    tot_c = float(alt_m.group(1))
                                    current_course["credits_info"] = {
                                        "L": "-", "T": "-", "P": "-", "C": str(tot_c),
                                        "credits_total": tot_c,
                                        "page": page_num
                                    }
                                elif alt_m.group(2):
                                    current_course["credits_info"] = {
                                        "L": alt_m.group(2), "T": alt_m.group(3), "P": alt_m.group(4), "C": alt_m.group(5),
                                        "credits_total": float(alt_m.group(5)),
                                        "page": page_num
                                    }

                    # Add line to current unit if active
                    if current_course["units"]:
                        current_course["units"][-1]["raw_lines"].append((line_s, page_num))

        if current_course:
            self._finalize_course(current_course)
            courses.append(current_course)

        # Fallback if no specific course codes found
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

        # 1. Finalize topics & subtopics inside units
        for unit in course["units"]:
            raw_lines = unit.get("raw_lines", [])
            unit_topics = []
            current_topic = None

            for line_str, line_page in raw_lines:
                # Stop if textbook / outcomes section begins inside unit block
                if any(k in line_str.upper() for k in ["TEXTBOOK", "TEXT BOOK", "REFERENCES:", "COURSE OUTCOME", "OUTCOMES:"]):
                    break
                
                # Check for explicit subtopic indicators:
                # e.g., "1.1 Introduction", "a) Syntax", "• Relational Algebra", "- Subquery"
                subtopic_match = re.match(r'^(?:\d+\.\d+|\([a-z\d]+\)|[a-z\d]\)|[-•–*])\s*(.+)', line_str)
                if subtopic_match and current_topic:
                    current_topic["subtopics"].append({
                        "title": subtopic_match.group(1).strip(),
                        "page": line_page
                    })
                elif len(line_str.split()) > 1:
                    # Check if line contains topic with subtopics separated by colon or dash or semicolons
                    # e.g., "Relational Model: Schemas, Tuples, Integrity Constraints"
                    if ':' in line_str and not line_str.upper().startswith("UNIT") and not line_str.upper().startswith("HOURS"):
                        t_parts = line_str.split(':', 1)
                        top_name = t_parts[0].strip()
                        subs_str = t_parts[1].strip()
                        subs = [
                            {"title": s.strip(), "page": line_page}
                            for s in re.split(r'[,;-]', subs_str) if len(s.strip()) > 2
                        ]
                        current_topic = {
                            "title": top_name,
                            "page": line_page,
                            "subtopics": subs
                        }
                        unit_topics.append(current_topic)
                    elif ' - ' in line_str:
                        parts = [p.strip() for p in line_str.split(' - ') if p.strip()]
                        top_name = parts[0]
                        subs = [{"title": s, "page": line_page} for s in parts[1:]]
                        current_topic = {
                            "title": top_name,
                            "page": line_page,
                            "subtopics": subs
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
            if "raw_lines" in unit:
                del unit["raw_lines"]

        # 2. Parse Course Outcomes, Textbooks, Reference Books, and Tables across course pages
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

                if "COURSE OUTCOME" in l_upper or "OUTCOMES:" in l_upper or "CO1" in l_upper or "STUDENTS WILL BE ABLE TO" in l_upper:
                    mode = "OUTCOMES"
                elif "TEXT BOOK" in l_upper or "TEXTBOOK" in l_upper or "PRESCRIBED BOOK" in l_upper:
                    mode = "TEXTBOOKS"
                elif ("REFERENCE BOOK" in l_upper or "REFERENCES:" in l_upper) and not "CO" in l_upper:
                    mode = "REFERENCES"
                elif "UNIT " in l_upper or "MODULE " in l_upper:
                    mode = None

                if mode == "OUTCOMES" and ("CO" in l_upper or re.match(r'^(?:CO\s*\d+|\d+\.)', l_str, re.I)):
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

                elif mode == "TEXTBOOKS" and l_str and not any(k in l_upper for k in ["TEXT BOOK", "TEXTBOOK", "PRESCRIBED"]):
                    course["textbooks"].append({"title": l_str, "page": page_num})

                elif mode == "REFERENCES" and l_str and not any(k in l_upper for k in ["REFERENCE BOOK", "REFERENCES:"]):
                    course["reference_books"].append({"title": l_str, "page": page_num})

            # Check tables for CO-PO mapping
            for table in p_data["tables"]:
                if self._is_copo_table(table):
                    course["co_po_matrix"].append({
                        "page": page_num,
                        "matrix": table
                    })

    def _extract_units_fallback(self, course):
        unit_pat = re.compile(r'^(?:UNIT|MODULE|CHAPTER)\s+([I|V|X\d]+)[^\n]*', re.I)
        for p in self.pages_data:
            page_num = p["page"]
            lines = p["text"].split('\n')
            current_u = None
            for line in lines:
                m = unit_pat.match(line.strip())
                if m:
                    current_u = {
                        "unit_number": str(len(course["units"]) + 1),
                        "title": line.strip(),
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
                if re.match(r'^(?:CO\s*\d+|\d+\.\s*Explain|\d+\.\s*Design|\d+\.\s*Analyze)', line.strip(), re.I):
                    outcomes.append({"text": line.strip(), "page": p["page"]})
        return outcomes

    def _extract_programme_outcomes(self):
        pos = []
        for p in self.pages_data:
            lines = p["text"].split('\n')
            for line in lines:
                if re.match(r'^PO\s*\d+', line.strip(), re.I) or "PROGRAMME OUTCOME" in line.upper():
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
                elif "UNIT" in l_u or "MODULE" in l_u:
                    is_tb = False
                    is_rb = False

                if is_tb and line.strip() and not "TEXTBOOK" in line.upper():
                    textbooks.append({"title": line.strip(), "page": p["page"]})
                elif is_rb and line.strip() and not "REFERENCE" in line.upper():
                    refbooks.append({"title": line.strip(), "page": p["page"]})

        return textbooks, refbooks
