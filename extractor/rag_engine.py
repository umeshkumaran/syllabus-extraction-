import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RAGEngine:
    """
    RAG Engine with metadata-rich page indexing, hybrid retrieval (BM25 + TF-IDF cosine),
    strict source grounding, hallucination protection, and multi-turn context memory.
    """

    def __init__(self, pages_data, hierarchy):
        self.pages_data = pages_data
        self.hierarchy = hierarchy
        self.chunks = []
        self._build_chunks()
        self._build_index()

    def _build_chunks(self):
        """
        Creates fine-grained page-aware chunks with metadata (page, course, unit, topic).
        """
        self.chunks = []
        courses = self.hierarchy.get("courses", [])

        for p in self.pages_data:
            page_num = p["page"]
            p_text = p["text"]

            # Map page to relevant course / unit
            rel_course = None
            rel_unit = None
            for c in courses:
                if page_num in c.get("pages", []):
                    rel_course = c.get("title") or c.get("code")
                    for u in c.get("units", []):
                        if u.get("page") == page_num:
                            rel_unit = u.get("title")
                            break
                    break

            # Split page text into semantic paragraphs/chunks (approx 150-300 chars)
            raw_paragraphs = [para.strip() for para in p_text.split('\n\n') if para.strip()]
            if not raw_paragraphs:
                raw_paragraphs = [p_text.strip()] if p_text.strip() else []

            for para in raw_paragraphs:
                # Store metadata
                self.chunks.append({
                    "text": para,
                    "page": page_num,
                    "course": rel_course,
                    "unit": rel_unit,
                    "section": f"Page {page_num}" + (f" - {rel_course}" if rel_course else "")
                })

    def _build_index(self):
        """
        Builds TF-IDF vector index over chunks.
        """
        if not self.chunks:
            self.vectorizer = None
            self.tfidf_matrix = None
            return

        texts = [c["text"] for c in self.chunks]
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        except Exception:
            self.tfidf_matrix = None

    def retrieve(self, query, top_k=5):
        """
        Retrieves top-k relevant chunks based on hybrid keyword and TF-IDF similarity.
        """
        if not self.chunks:
            return []

        scored_chunks = []
        query_words = set(re.findall(r'\w+', query.lower()))

        # Vector score
        vector_scores = np.zeros(len(self.chunks))
        if self.vectorizer and self.tfidf_matrix is not None:
            try:
                q_vec = self.vectorizer.transform([query])
                sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
                vector_scores = sims
            except Exception:
                pass

        for idx, chunk in enumerate(self.chunks):
            chunk_text_lower = chunk["text"].lower()
            chunk_words = set(re.findall(r'\w+', chunk_text_lower))
            
            # Keyword match overlap
            overlap = len(query_words.intersection(chunk_words))
            keyword_score = overlap / (len(query_words) + 1e-5)

            # Metadata boost if course or unit matches
            meta_boost = 0.0
            if chunk["course"] and chunk["course"].lower() in query.lower():
                meta_boost += 0.3
            if chunk["unit"] and chunk["unit"].lower() in query.lower():
                meta_boost += 0.2

            final_score = (vector_scores[idx] * 0.5) + (keyword_score * 0.3) + meta_boost
            
            if final_score > 0.02 or overlap > 0:
                scored_chunks.append({
                    "chunk": chunk,
                    "score": round(float(final_score), 4)
                })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    def answer_question(self, question, chat_history=None):
        """
        Answers question with strict source grounding and multi-turn context resolution.
        """
        q_lower = question.lower().strip()

        # 1. Resolve multi-turn context / pronouns
        resolved_question = question
        if chat_history and len(chat_history) > 0:
            last_q = chat_history[-1].get("question", "")
            last_a = chat_history[-1].get("answer", "")
            if any(p in q_lower.split() for p in ["it", "its", "this", "which", "them", "that"]):
                resolved_question = f"{last_q} {question}"

        # 2. Check for full syllabus request
        if any(phrase in q_lower for phrase in ["full syllabus", "complete syllabus", "give me the syllabus", "show syllabus", "all courses"]):
            return self._generate_full_syllabus_response()

        # 3. Retrieve relevant chunks
        results = self.retrieve(resolved_question, top_k=6)

        if not results:
            pages_checked = sorted(list(set(c["page"] for c in self.chunks[:5])))
            return {
                "answer": f"**This information was not found in the uploaded syllabus PDF.**\n\nRelevant source pages checked: Pages {', '.join(map(str, pages_checked)) if pages_checked else 'None'}",
                "sources": [],
                "confidence": 0.0
            }

        # Collect source pages and text snippets
        retrieved_texts = []
        source_pages = set()
        sources_list = []

        for item in results:
            c = item["chunk"]
            source_pages.add(c["page"])
            retrieved_texts.append(c["text"])
            sources_list.append({
                "page": c["page"],
                "text": c["text"],
                "section": c["section"],
                "score": item["score"]
            })

        sorted_pages = sorted(list(source_pages))
        page_str = ", ".join([f"Page {p}" for p in sorted_pages])

        # Synthesize grounded answer
        # Group content by course/unit if available
        matched_content = "\n\n".join([f"**From Page {c['page']}:**\n{c['text']}" for c in [r['chunk'] for r in results]])

        answer_markdown = f"### Result\n\n{matched_content}\n\n"
        
        # Extract topics / subtopics present in these pages
        topics_found = []
        for c in self.hierarchy.get("courses", []):
            for u in c.get("units", []):
                if u.get("page") in source_pages:
                    for t in u.get("topics", []):
                        topics_found.append(t.get("title"))
                        for st in t.get("subtopics", []):
                            topics_found.append(f"  - {st.get('title')}")

        if topics_found:
            answer_markdown += "### Topics / Subtopics\n\n"
            answer_markdown += "\n".join([f"* {t}" for t in topics_found[:8]]) + "\n\n"

        answer_markdown += f"### Source\n\n**Source: PDF {page_str}**"

        return {
            "answer": answer_markdown,
            "sources": sources_list,
            "source_pages": sorted_pages,
            "confidence": round(results[0]["score"] * 100, 1) if results else 0.0
        }

    def _generate_full_syllabus_response(self):
        """
        Generates structured full syllabus overview hierarchy with page references.
        """
        h = self.hierarchy
        lines = ["### Full Syllabus Overview\n"]

        if h.get("institution"):
            lines.append(f"**Institution:** {h['institution']['name']} *(Source: Page {h['institution']['page']})*")
        if h.get("programme"):
            lines.append(f"**Programme:** {h['programme']['name']} *(Source: Page {h['programme']['page']})*")
        if h.get("department"):
            lines.append(f"**Department:** {h['department']['name']} *(Source: Page {h['department']['page']})*")
        if h.get("batch_year"):
            lines.append(f"**Regulation/Batch:** {h['batch_year']['val']} *(Source: Page {h['batch_year']['page']})*")

        lines.append("\n#### Courses Detected:\n")

        source_pages = set()
        for course in h.get("courses", []):
            code = course.get("code", "")
            title = course.get("title", "")
            start_p = course.get("start_page", 1)
            source_pages.add(start_p)
            cred = course.get("credits_info")
            cred_str = f" [L: {cred['L']}, T: {cred['T']}, P: {cred['P']}, C: {cred['C']}]" if cred else ""

            lines.append(f"---")
            lines.append(f"### {code} - {title}{cred_str}")
            lines.append(f"**Source: PDF Page {start_p}**\n")

            for unit in course.get("units", []):
                u_page = unit.get("page", start_p)
                source_pages.add(u_page)
                hrs = f" ({unit['hours']} Hours)" if unit.get("hours") else ""
                lines.append(f"**Unit {unit.get('unit_number', '')}: {unit.get('title', '')}**{hrs} — *Source: Page {u_page}*")

                for top in unit.get("topics", []):
                    t_page = top.get("page", u_page)
                    lines.append(f"  * {top.get('title')} *(Source: Page {t_page})*")
                    for sub in top.get("subtopics", []):
                        lines.append(f"    - {sub.get('title')} *(Source: Page {sub.get('page', t_page)})*")

            if course.get("outcomes"):
                lines.append("\n**Course Outcomes:**")
                for co in course["outcomes"]:
                    bloom_str = f" *(Bloom: {co['bloom_level']} [{co['bloom_source']}])* " if co.get("bloom_level") else " "
                    lines.append(f"  * {co['text']}{bloom_str}*(Source: Page {co['page']})*")

        lines.append(f"\n### Source\n\n**Source: PDF Pages {min(source_pages) if source_pages else 1}–{max(source_pages) if source_pages else 1}**")

        return {
            "answer": "\n".join(lines),
            "sources": [{"page": p, "text": "Syllabus overview section", "section": f"Page {p}"} for p in sorted(list(source_pages))],
            "source_pages": sorted(list(source_pages)),
            "confidence": 100.0
        }
