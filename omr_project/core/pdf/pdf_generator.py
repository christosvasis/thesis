from config.app_config import AppConfig
from config.font_config import FONT
from i18n.translator import get_option_letter
from i18n import translator
from config.logger_config import get_logger, PDF_LOGGER_NAME

# ReportLab core
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.pdfgen import canvas
 
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


from utils.page_size import get_reportlab_pagesize


class PDFGeneratorMixin:
    """Mixin for PDF generation functionality"""

    def _generate_pdf(self, filename: str):
        """Generate student answer PDF."""
        log = get_logger(PDF_LOGGER_NAME)
        margins = AppConfig.PDF_MARGINS
        doc = SimpleDocTemplate(
            filename,
            pagesize=get_reportlab_pagesize(),
            rightMargin=margins['right'] * inch,
            leftMargin=margins['left'] * inch,
            topMargin=margins['top'] * inch,
            bottomMargin=margins['bottom'] * inch,
        )
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'Title', parent=styles['Heading1'], fontSize=AppConfig.FONT_SIZES['title'],
            fontName=FONT, spaceAfter=12, alignment=1
        )
        safe_title = str(self.form.title).replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(safe_title, title_style))
        story.append(Spacer(1, 12))

        # Instructions
        if self.form.instructions:
            inst_style = ParagraphStyle(
                'Instructions', parent=styles['Normal'], fontSize=AppConfig.FONT_SIZES['normal'],
                fontName=FONT, spaceAfter=18, alignment=1
            )
            story.append(Paragraph(self.form.instructions, inst_style))
            story.append(Spacer(1, 18))

        # Questions
        for i, q in enumerate(self.form.questions):
            elements = []
            q_style = ParagraphStyle(
                'Question', parent=styles['Normal'], fontSize=AppConfig.FONT_SIZES['normal'],
                fontName=FONT, spaceAfter=8
            )
            elements.append(Paragraph(f"{i+1}. {q.text}", q_style))

            non_empty_options = q.get_non_empty_options()
            options = [[f"○ {get_option_letter(j)}.", opt] for j, opt in enumerate(non_empty_options)]
            table = Table(options, colWidths=[0.5*inch, 5.5*inch])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('LEFTPADDING', (0, 0), (0, -1), 20),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(table)
            story.append(KeepTogether(elements))
            if i < len(self.form.questions) - 1:
                story.append(Spacer(1, 18))

        try:
            doc.build(story)
            log.info("Generated PDF: %s (questions=%d)", filename, len(self.form.questions))
        except Exception as e:  # noqa: BLE001
            log.exception("Error generating PDF '%s': %s", filename, e)

    def _generate_omr_sheet(self, filename: str):
        """Generate OMR answer sheet PDF."""
        log = get_logger(PDF_LOGGER_NAME)
        try:
            c = canvas.Canvas(filename, pagesize=get_reportlab_pagesize())
            width, height = get_reportlab_pagesize()
            y = self._draw_omr_header(c, width, height)
            y = self._draw_student_info_section(c, width, y)
            y = self._draw_instructions_section(c, width, y)
            self._draw_questions_section(c, width, height, y)
            self._draw_omr_footer(c, width)
            c.save()
            log.info("Generated OMR sheet: %s (questions=%d)", filename, len(self.form.questions))
        except Exception as e:  # noqa: BLE001
            log.exception("Error generating OMR sheet '%s': %s", filename, e)

    def _draw_omr_header(self, c, width, height):
        c.setFont(FONT, AppConfig.FONT_SIZES['title'])
        c.drawCentredString(width/2, height - AppConfig.PDF_HEADER_TITLE_Y_OFFSET * inch, self.form.title)
        c.setFont(FONT, AppConfig.FONT_SIZES['normal'] + 2)
        c.drawCentredString(width/2, height - AppConfig.PDF_HEADER_SUBTITLE_Y_OFFSET * inch, translator.t('answer_sheet'))
        c.line(AppConfig.PDF_SIDE_MARGIN_INCH * inch, height - AppConfig.PDF_HEADER_SEPARATOR_Y_OFFSET * inch,
               width - AppConfig.PDF_SIDE_MARGIN_INCH * inch, height - AppConfig.PDF_HEADER_SEPARATOR_Y_OFFSET * inch)
        self._draw_alignment_points(c, width, height)
        return height - AppConfig.PDF_HEADER_RETURN_Y_OFFSET * inch

    def _draw_student_info_section(self, c, width, y):
        c.setFont(FONT, AppConfig.FONT_SIZES['normal'] - 1)
        name_text = translator.t('student_name')
        name_x = AppConfig.PDF_SIDE_MARGIN_INCH * inch
        c.drawString(name_x, y, name_text)
        name_width = c.stringWidth(name_text, FONT, AppConfig.FONT_SIZES['normal'] - 1)
        c.line(name_x + name_width + 0.1 * inch, y - 3, AppConfig.PDF_STUDENT_NAME_UNDERLINE_END * inch, y - 3)
        id_text = translator.t('student_id')
        id_x = AppConfig.PDF_STUDENT_ID_X * inch
        c.drawString(id_x, y, id_text)
        id_width = c.stringWidth(id_text, FONT, AppConfig.FONT_SIZES['normal'] - 1)
        c.line(id_x + id_width + 0.1 * inch, y - 3, AppConfig.PDF_STUDENT_ID_UNDERLINE_END * inch, y - 3)
        return y - AppConfig.PDF_STUDENT_SECTION_Y_REDUCTION * inch

    def _draw_instructions_section(self, c, width, y):
        c.setFont(FONT, AppConfig.FONT_SIZES['instruction'])
        c.drawString(AppConfig.PDF_SIDE_MARGIN_INCH * inch, y, translator.t('omr_instruction1'))
        y -= AppConfig.PDF_INSTRUCTION_LINE_SPACING1 * inch
        c.drawString(AppConfig.PDF_SIDE_MARGIN_INCH * inch, y, translator.t('omr_instruction2'))
        y -= AppConfig.PDF_INSTRUCTION_LINE_SPACING2 * inch
        c.line(AppConfig.PDF_SIDE_MARGIN_INCH * inch, y, width - AppConfig.PDF_SIDE_MARGIN_INCH * inch, y)
        return y - AppConfig.PDF_INSTRUCTION_SECTION_SPACING * inch

    def _draw_questions_section(self, c, width, height, y):
        min_bottom_margin = AppConfig.MIN_BOTTOM_MARGIN * inch
        question_height = AppConfig.QUESTION_HEIGHT * inch
        for i, _ in enumerate(self.form.questions):
            if y - question_height < min_bottom_margin:
                c.showPage()
                y = self._draw_continuation_header(c, width, height)
            y = self._draw_single_question(c, i, y, question_height)

    def _draw_continuation_header(self, c, width, height):
        c.setFont(FONT, AppConfig.FONT_SIZES['header'])
        c.drawCentredString(width/2, height - AppConfig.PDF_CONTINUATION_HEADER_Y_OFFSET * inch,
                            f"{self.form.title} ({translator.t('continued')})")
        c.line(AppConfig.PDF_SIDE_MARGIN_INCH * inch, height - AppConfig.PDF_CONTINUATION_SEPARATOR_Y_OFFSET * inch,
               width - AppConfig.PDF_SIDE_MARGIN_INCH * inch, height - AppConfig.PDF_CONTINUATION_SEPARATOR_Y_OFFSET * inch)
        return height - AppConfig.PDF_CONTINUATION_RETURN_Y_OFFSET * inch

    def _draw_single_question(self, c, question_index, y, question_height):
        c.setFont(FONT, AppConfig.FONT_SIZES['normal'])
        question_num = f"{question_index + 1}."
        c.drawRightString(AppConfig.PDF_QUESTION_NUMBER_RIGHT_X * inch, y + 2, question_num)
        bubble_radius = AppConfig.BUBBLE_RADIUS
        bubble_spacing = AppConfig.BUBBLE_SPACING * inch
        start_x = AppConfig.PDF_QUESTION_BUBBLE_START_X * inch
        question = self.form.questions[question_index]
        option_count = question.get_option_count()
        for j in range(option_count):
            x = start_x + j * bubble_spacing
            c.circle(x, y + 5, bubble_radius, fill=0, stroke=1)
            c.setFont(FONT, AppConfig.FONT_SIZES['instruction'])
            c.drawCentredString(x, y - 0.25 * inch, get_option_letter(j))
        return y - question_height

    def _draw_alignment_points(self, c, width, height):
        square_size = AppConfig.PDF_ALIGNMENT_SQUARE_SIZE
        positions = [
            (AppConfig.PDF_ALIGNMENT_SQUARE_OFFSET * inch, height - AppConfig.PDF_ALIGNMENT_SQUARE_OFFSET * inch, "TL"),
            (width - AppConfig.PDF_ALIGNMENT_SQUARE_OFFSET * inch - square_size, height - AppConfig.PDF_ALIGNMENT_SQUARE_OFFSET * inch, "TR"),
            (AppConfig.PDF_ALIGNMENT_SQUARE_OFFSET * inch, AppConfig.PDF_ALIGNMENT_SQUARE_OFFSET * inch + square_size, "BL"),
            (width - AppConfig.PDF_ALIGNMENT_SQUARE_OFFSET * inch - square_size, AppConfig.PDF_ALIGNMENT_SQUARE_OFFSET * inch + square_size, "BR")
        ]
        for x, y_pos, label in positions:
            c.rect(x, y_pos, square_size, -square_size, fill=1, stroke=1)
            c.setFont(FONT, 8)
            if label.endswith('L'):
                c.drawString(x + 20, y_pos - 10 if label.startswith('T') else y_pos + 5, label)
            else:
                c.drawRightString(x - 5, y_pos - 10 if label.startswith('T') else y_pos + 5, label)

    def _draw_omr_footer(self, c, width):
        c.setFont(FONT, AppConfig.FONT_SIZES['small'])
        footer_text = f"{translator.t('total_questions')} {len(self.form.questions)} | {translator.t('total_points')} {sum(q.points for q in self.form.questions)}"
        c.drawCentredString(width/2, AppConfig.PDF_FOOTER_Y * inch, footer_text)
