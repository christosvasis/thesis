from typing import Dict, List, NamedTuple
from i18n import translator
import csv
from config.logger_config import get_logger, GRADING_LOGGER_NAME
from config.app_config import AppConfig
try:
    import pandas as pd  # type: ignore
    EXCEL_AVAILABLE = True
except ImportError:  # pragma: no cover
    EXCEL_AVAILABLE = False

class GradeResult(NamedTuple):
    student_name: str
    student_id: str
    answers: Dict[int, str]
    correct_answers: Dict[int, str]
    points_per_question: Dict[int, int]
    score: int
    total_possible: int
    percentage: float
    correct_count: int
    incorrect_count: int
    blank_count: int
    question_results: Dict[int, bool | None]

class GradingSystem:
    def __init__(self):
        self.results: List[GradeResult] = []
        self.log = get_logger(GRADING_LOGGER_NAME)

    def clear(self):
        self.results.clear()

    def calculate_grade(self, student_name: str, student_id: str,
                         student_answers: Dict[int, str],
                         answer_key: Dict[int, str],
                         points_per_question: Dict[int, int]) -> GradeResult:
        """Compatibility wrapper used by UI to compute and store a grade.

        Delegates to `add_result` and returns the created GradeResult.
        """
        return self.add_result(student_name, student_id, student_answers,
                               answer_key, points_per_question)

    def add_result(self, student_name: str, student_id: str, student_answers: Dict[int, str],
                   answer_key: Dict[int, str], points_per_question: Dict[int, int]) -> GradeResult:
        score = 0
        total_possible = sum(points_per_question.values())
        correct_count = incorrect_count = blank_count = 0
        question_results: Dict[int, bool | None] = {}
        for q_num, correct_answer in answer_key.items():
            points = points_per_question[q_num]
            student_answer = student_answers.get(q_num)
            if student_answer is None:
                question_results[q_num] = None
                blank_count += 1
            elif student_answer == correct_answer:
                question_results[q_num] = True
                score += points
                correct_count += 1
            else:
                question_results[q_num] = False
                incorrect_count += 1
        percentage = (score / total_possible * 100) if total_possible > 0 else 0.0
        result = GradeResult(student_name, student_id, student_answers.copy(), answer_key.copy(),
                              points_per_question.copy(), score, total_possible, percentage,
                              correct_count, incorrect_count, blank_count, question_results)
        self.results.append(result)
        return result

    @staticmethod
    def get_letter_grade(percentage: float) -> str:
        if percentage >= 90: return 'A'
        if percentage >= 80: return 'B'
        if percentage >= 70: return 'C'
        if percentage >= 60: return 'D'
        return 'F'

    def export_to_csv(self, filename: str) -> bool:
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                if not self.results:
                    return True
                first = self.results[0]
                questions = sorted(first.answers.keys())
                header = [
                    translator.t('csv_header_student_name'),
                    translator.t('csv_header_student_id'),
                    translator.t('csv_header_score'),
                    translator.t('csv_header_total_possible'),
                    translator.t('csv_header_percentage'),
                    translator.t('csv_header_letter_grade'),
                    translator.t('csv_header_correct'),
                    translator.t('csv_header_incorrect'),
                    translator.t('csv_header_blank'),
                ]
                for q in questions:
                    header.extend([
                        translator.t('csv_header_q_answer').format(q),
                        translator.t('csv_header_q_correct').format(q),
                        translator.t('csv_header_q_points').format(q),
                    ])
                writer.writerow(header)
                for r in self.results:
                    row = [
                        r.student_name,
                        r.student_id,
                        r.score,
                        r.total_possible,
                        f'{r.percentage:.1f}%',
                        self.get_letter_grade(r.percentage),
                        r.correct_count,
                        r.incorrect_count,
                        r.blank_count,
                    ]
                    for q in questions:
                        row.extend([r.answers.get(q, ''), r.correct_answers.get(q, ''), r.points_per_question.get(q, 0)])
                    writer.writerow(row)
            return True
        except Exception as e:  # noqa: BLE001
            self.log.exception('CSV export error: %s', e)
            return False

    def export_to_excel(self, filename: str) -> bool:
        if not EXCEL_AVAILABLE:
            return False
        try:
            rows = []
            for r in self.results:
                base = {
                    translator.t('csv_header_student_name'): r.student_name,
                    translator.t('csv_header_student_id'): r.student_id,
                    translator.t('csv_header_score'): r.score,
                    translator.t('csv_header_total_possible'): r.total_possible,
                    translator.t('csv_header_percentage'): r.percentage,
                    translator.t('csv_header_letter_grade'): self.get_letter_grade(r.percentage),
                    translator.t('csv_header_correct'): r.correct_count,
                    translator.t('csv_header_incorrect'): r.incorrect_count,
                    translator.t('csv_header_blank'): r.blank_count,
                }
                for q in sorted(r.answers.keys()):
                    base[translator.t('csv_header_q_answer').format(q)] = r.answers.get(q, '')
                    base[translator.t('csv_header_q_correct').format(q)] = r.correct_answers.get(q, '')
                    base[translator.t('csv_header_q_points').format(q)] = r.points_per_question.get(q, 0)
                rows.append(base)
            if rows:
                df = pd.DataFrame(rows)
                df.to_excel(filename, index=False, engine='openpyxl')
            return True
        except Exception as e:  # noqa: BLE001
            self.log.exception('Excel export error: %s', e)
            return False

    # Convenience stats helper to avoid duplicated logic
    def compute_stats(self) -> Dict[str, float]:
        if not self.results:
            return {"average": 0.0, "highest": 0.0, "lowest": 0.0, "pass_rate": 0.0}
        percentages = [r.percentage for r in self.results]
        avg_score = sum(percentages) / len(percentages)
        highest_score = max(percentages)
        lowest_score = min(percentages)
        pass_count = sum(1 for p in percentages if p >= AppConfig.PASSING_PERCENTAGE)
        pass_rate = (pass_count / len(percentages)) * 100
        return {
            "average": avg_score,
            "highest": highest_score,
            "lowest": lowest_score,
            "pass_rate": pass_rate,
        }
