from __future__ import annotations

from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
 
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from i18n import translator
from utils.page_size import get_reportlab_pagesize


def generate_class_report(grading_system, filename: str) -> bool:
    """Generate comprehensive class report PDF from a grading system.

    Args:
        grading_system: GradingSystem instance with populated results
        filename: Destination PDF path

    Returns:
        bool: True if generation succeeded, False otherwise
    """
    try:
        doc = SimpleDocTemplate(filename, pagesize=get_reportlab_pagesize())
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph(translator.t('omr_class_report'), title_style))
        story.append(Spacer(1, 20))

        # Class Statistics
        story.append(Paragraph(translator.t('class_statistics'), styles['Heading2']))

        stats = grading_system.compute_stats()

        stats_info = [
            [translator.t('total_students_label'), str(len(grading_system.results))],
            [translator.t('average_score_label'), f"{stats['average']:.1f}%"],
            [translator.t('highest_score_label'), f"{stats['highest']:.1f}%"],
            [translator.t('lowest_score_label'), f"{stats['lowest']:.1f}%"],
            [translator.t('pass_rate_label'), f"{stats['pass_rate']:.1f}%"],
            [translator.t('generated_label'), datetime.now().strftime("%Y-%m-%d %H:%M")]
        ]

        stats_table = Table(stats_info)
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
            ('BACKGROUND', (0, 0), (0, -1), '#f0f0f0'),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 20))

        # Student Results Table
        story.append(Paragraph(translator.t('individual_results'), styles['Heading2']))

        student_data = [[
            translator.t('student_name_field').replace(':',''),
            translator.t('student_id_field').replace(':',''),
            translator.t('score_label').replace(':',''),
            translator.t('total_label').replace(':',''),
            translator.t('percentage_label').replace(':',''),
            translator.t('grade_label').replace(':','')
        ]]

        for result in grading_system.results:
            student_data.append([
                result.student_name,
                result.student_id,
                str(result.score),
                str(result.total_possible),
                f"{result.percentage:.1f}%",
                grading_system.get_letter_grade(result.percentage)
            ])

        student_table = Table(student_data)
        student_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
            ('BACKGROUND', (0, 0), (-1, 0), '#cccccc'),  # Header
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        story.append(student_table)

        # Build PDF
        doc.build(story)
        return True

    except Exception:
        return False
