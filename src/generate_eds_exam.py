import pandas as pd
import json
import random

class EDSExamGenerator:
    def __init__(self, data_path='exam-data/test_integration_data.csv'):
        self.data_path = data_path
        # In a real app, this would load mapped_exams.json.
        # For now, we simulate a question bank mapping.
        self.mock_questions = {
            "Bc-Ⅳ-3": [
                {"q_id": "111-2", "text": "關於光合作用...", "options": ["A", "B", "C", "D"], "group_id": None},
                {"q_id": "115-25", "text": "此圖為葉綠體構造...", "options": ["A", "B", "C", "D"], "group_id": "group_1"}
            ],
            "Eb-Ⅳ-2": [
                {"q_id": "112-6", "text": "某地層發現化石...", "options": ["A", "B", "C", "D"], "group_id": None},
                {"q_id": "113-10", "text": "板塊構造學說指出...", "options": ["A", "B", "C", "D"], "group_id": None}
            ]
        }

        # Simulate question groups
        self.mock_groups = {
            "group_1": {
                "text": "閱讀下列文章並回答問題：\n植物利用葉綠素吸收太陽能...",
                "sub_questions": ["115-25"]
            }
        }

    def generate_balanced_exam(self, top_topics: list, num_questions: int = 5) -> dict:
        """
        Task 1: Generate an exam avoiding too many questions from the same code,
        and supporting question groups.
        """
        exam = {"title": "🎯 EDS 專屬特訓考卷", "questions": []}
        selected_q_ids = set()

        # Try to pull evenly from top_topics
        if not top_topics:
            return exam

        topics_pool = list(top_topics)

        while len(exam["questions"]) < num_questions and topics_pool:
            # Round-robin selection
            for topic in list(topics_pool):
                if len(exam["questions"]) >= num_questions:
                    break

                code = topic.get('X軸主代碼')
                available_qs = [q for q in self.mock_questions.get(code, []) if q["q_id"] not in selected_q_ids]

                if not available_qs:
                    topics_pool.remove(topic)
                    continue

                # Pick one question randomly from the available ones
                q = random.choice(available_qs)
                selected_q_ids.add(q["q_id"])

                # Check for group support
                if q["group_id"]:
                    group = self.mock_groups.get(q["group_id"])
                    if group:
                        exam["questions"].append({
                            "type": "group",
                            "group_text": group["text"],
                            "question": q
                        })
                else:
                    exam["questions"].append({
                        "type": "single",
                        "question": q
                    })

        return exam

    def generate_t2n_pop_quiz(self, eds_x_code: str, num_questions: int = 3) -> dict:
        """
        Task 2: Generate a small pop quiz for a specific topic after T2N parsing.
        """
        exam = {"title": f"📝 隨堂小考 ({eds_x_code})", "questions": []}
        available_qs = self.mock_questions.get(eds_x_code, [])

        if not available_qs:
            return exam

        # Shuffle and take up to num_questions
        selected_qs = random.sample(available_qs, min(num_questions, len(available_qs)))

        for q in selected_qs:
             if q["group_id"]:
                 group = self.mock_groups.get(q["group_id"])
                 if group:
                     exam["questions"].append({
                         "type": "group",
                         "group_text": group["text"],
                         "question": q
                     })
             else:
                 exam["questions"].append({
                     "type": "single",
                     "question": q
                 })

        return exam

# API endpoint mock for Streamlit or external caller
def get_exam_for_topics(topics: list, num_questions: int = 5) -> str:
    generator = EDSExamGenerator()
    exam_json = generator.generate_balanced_exam(topics, num_questions)
    return json.dumps(exam_json, indent=2, ensure_ascii=False)

def get_pop_quiz(eds_x_code: str, num_questions: int = 3) -> str:
    generator = EDSExamGenerator()
    exam_json = generator.generate_t2n_pop_quiz(eds_x_code, num_questions)
    return json.dumps(exam_json, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("Testing Balanced Exam:")
    print(get_exam_for_topics([{'X軸主代碼': 'Bc-Ⅳ-3'}, {'X軸主代碼': 'Eb-Ⅳ-2'}]))
    print("\nTesting Pop Quiz:")
    print(get_pop_quiz('Bc-Ⅳ-3'))
