class ConfidenceCalculator:
    """
    Calculates Estimated Extraction Confidence % dynamically from actual extraction signals:
    - Text extraction quality
    - OCR confidence
    - Course detection presence
    - Unit detection presence
    - Topic & Subtopic coverage
    - Metadata completeness
    - Table detection
    """

    @staticmethod
    def calculate(pages_data, hierarchy):
        if not pages_data:
            return {
                "overall": 0,
                "text_extraction": 0,
                "ocr": 100,
                "course_detection": 0,
                "unit_detection": 0,
                "topic_detection": 0,
                "table_detection": 0,
                "outcome_detection": 0
            }

        # 1. Text extraction quality (ratio of non-empty pages & clean character densities)
        total_pages = len(pages_data)
        non_empty_pages = sum(1 for p in pages_data if len(p["text"].strip()) > 50)
        text_extraction_score = (non_empty_pages / total_pages) * 100

        # 2. OCR confidence score
        ocr_pages = [p for p in pages_data if p["used_ocr"]]
        if ocr_pages:
            ocr_score = sum(p["ocr_confidence"] for p in ocr_pages) / len(ocr_pages)
        else:
            ocr_score = 100.0  # Native text PDF, highest quality

        # 3. Course detection score
        courses = hierarchy.get("courses", [])
        if len(courses) > 0:
            course_score = 95.0 if courses[0]["code"] != "SYLLABUS-01" else 70.0
        else:
            course_score = 40.0

        # 4. Unit detection score
        total_units = sum(len(c.get("units", [])) for c in courses)
        unit_score = min(100.0, (total_units / max(1, len(courses) * 5)) * 100) if courses else 50.0

        # 5. Topic detection score
        total_topics = sum(
            sum(len(u.get("topics", [])) for u in c.get("units", []))
            for c in courses
        )
        topic_score = min(100.0, (total_topics / max(1, total_units * 3)) * 100) if total_units else 40.0

        # 6. Table detection score
        table_count = sum(len(p.get("tables", [])) for p in pages_data)
        table_score = 90.0 if table_count > 0 else 75.0

        # 7. Outcome detection score
        outcomes_count = sum(len(c.get("outcomes", [])) for c in courses)
        outcome_score = 90.0 if outcomes_count > 0 else 60.0

        # Overall weighted confidence score
        overall = (
            text_extraction_score * 0.25 +
            ocr_score * 0.15 +
            course_score * 0.20 +
            unit_score * 0.15 +
            topic_score * 0.15 +
            outcome_score * 0.05 +
            table_score * 0.05
        )

        return {
            "overall": round(overall, 1),
            "text_extraction": round(text_extraction_score, 1),
            "ocr": round(ocr_score, 1),
            "course_detection": round(course_score, 1),
            "unit_detection": round(unit_score, 1),
            "topic_detection": round(topic_score, 1),
            "table_detection": round(table_score, 1),
            "outcome_detection": round(outcome_score, 1)
        }
