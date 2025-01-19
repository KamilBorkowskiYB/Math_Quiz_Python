import sys
import random
import threading
import time
import sympy as sp
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QProgressBar, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QPixmap, QIcon
import matplotlib.pyplot as plt
import io

class MathQuiz(QWidget):
    time_updated = Signal(int, int)

    def __init__(self):
        super().__init__()

        self.question_number = 1
        self.good_answers = 0
        self.answer = 0
        self.quiz_time = 70
        self.timer_thread = None
        self.stop_thread = False
        self.correct_answer = 0
        self.mode = 0 # 0-easy

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Math Quiz')
        self.setGeometry(100, 100, 900, 900)

        # Main layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Stacked widget to switch between screens
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Start screen
        self.start_screen = QWidget()
        self.start_layout = QVBoxLayout()
        self.start_screen.setLayout(self.start_layout)

        self.start_label = QLabel("You will answer 10 math\nquestions in a limited time.\nAre you ready?")
        self.start_label.setAlignment(Qt.AlignCenter)
        self.start_layout.addWidget(self.start_label)

        self.start_button = QPushButton("Play easy")
        self.start_button.clicked.connect(self.start_quiz)
        self.start_layout.addWidget(self.start_button)
        self.start_button.setDefault(True)

        self.start_hard = QPushButton("Play hard")
        self.start_hard.clicked.connect(self.start_quiz_hard)
        self.start_layout.addWidget(self.start_hard)

        self.stacked_widget.addWidget(self.start_screen)

        # Game screen
        self.game_screen = QWidget()
        self.game_layout = QHBoxLayout()
        self.game_screen.setLayout(self.game_layout)

        # Timer section (left side)
        self.timer_section = QVBoxLayout()
        self.timer_label = QLabel("Time Left")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 24px;")
        self.timer_section.addWidget(self.timer_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.quiz_time)
        self.progress_bar.setOrientation(Qt.Vertical)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.progress_bar.setMinimumWidth(100)
        self.progress_bar.setMaximumWidth(150)
        self.timer_section.addWidget(self.progress_bar)

        self.game_layout.addLayout(self.timer_section)

        # Game sections (Stacked game modes)
        self.stacked_game_modes = QStackedWidget()
        self.game_layout.addWidget(self.stacked_game_modes)

        # Easy mode game section
        self.game_content_layout_easy = QVBoxLayout()

        self.question_label = QLabel("Question 1")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.game_content_layout_easy.addWidget(self.question_label)

        self.equation_label = QLabel("Equation 1")
        self.equation_label.setAlignment(Qt.AlignCenter)
        self.equation_label.setStyleSheet("font-size: 30px;")
        self.game_content_layout_easy.addWidget(self.equation_label)

        self.answer_entry = QLineEdit()
        self.answer_entry.setAlignment(Qt.AlignCenter)
        self.answer_entry.setStyleSheet("font-size: 24px;")
        self.game_content_layout_easy.addWidget(self.answer_entry)

        self.next_question_button = QPushButton("Next Question")
        self.next_question_button.clicked.connect(self.submit_answer)
        self.game_content_layout_easy.addWidget(self.next_question_button)

        self.easy_game_section = QWidget()
        self.easy_game_section.setLayout(self.game_content_layout_easy)

        # Hard mode game section
        self.game_content_layout_hard = QVBoxLayout()

        self.question_label_hard = QLabel("Question 1")
        self.question_label_hard.setAlignment(Qt.AlignCenter)
        self.game_content_layout_hard.addWidget(self.question_label_hard)

        self.equation_label_hard = QLabel("Equation 1")
        self.equation_label_hard.setAlignment(Qt.AlignCenter)
        self.equation_label_hard.setStyleSheet("font-size: 30px;")
        self.game_content_layout_hard.addWidget(self.equation_label_hard)

        self.answer_button_1 = QPushButton("A")
        self.answer_button_1.clicked.connect(lambda: self.check_answer_hard(1))
        self.game_content_layout_hard.addWidget(self.answer_button_1)

        self.answer_button_2 = QPushButton("B")
        self.answer_button_2.clicked.connect(lambda: self.check_answer_hard(2))
        self.game_content_layout_hard.addWidget(self.answer_button_2)

        self.answer_button_3 = QPushButton("C")
        self.answer_button_3.clicked.connect(lambda: self.check_answer_hard(3))
        self.game_content_layout_hard.addWidget(self.answer_button_3)

        self.answer_button_4 = QPushButton("D")
        self.answer_button_4.clicked.connect(lambda: self.check_answer_hard(4))
        self.game_content_layout_hard.addWidget(self.answer_button_4)

        self.answer_button_5 = QPushButton("E")
        self.answer_button_5.clicked.connect(lambda: self.check_answer_hard(5))
        self.game_content_layout_hard.addWidget(self.answer_button_5)

        self.hard_game_section = QWidget()
        self.hard_game_section.setLayout(self.game_content_layout_hard)

        self.stacked_game_modes.addWidget(self.easy_game_section)
        self.stacked_game_modes.addWidget(self.hard_game_section)

        self.stacked_widget.addWidget(self.game_screen)

        # End screen
        self.end_screen = QWidget()
        self.end_layout = QVBoxLayout()
        self.end_screen.setLayout(self.end_layout)

        self.result_label = QLabel("Good answers: 0/10")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 30px;")
        self.end_layout.addWidget(self.result_label)

        self.restart_button = QPushButton("Play Again")
        self.restart_button.clicked.connect(self.restart)
        self.end_layout.addWidget(self.restart_button)
        self.restart_button.setDefault(True)

        self.back_to_menu_button = QPushButton("Back to menu")
        self.back_to_menu_button.clicked.connect(self.back_to_menu)
        self.end_layout.addWidget(self.back_to_menu_button)

        self.stacked_widget.addWidget(self.end_screen)

        self.stacked_widget.setCurrentWidget(self.start_screen)

        self.time_updated.connect(self.update_timer)

    def start_quiz(self):
        self.stacked_game_modes.setCurrentWidget(self.easy_game_section)
        self.stacked_widget.setCurrentWidget(self.game_screen)
        self.answer_entry.setFocus()
        self.start_timer()
        self.get_equation()
        self.answer_entry.returnPressed.connect(self.submit_answer)
        self.mode = 0

    def start_quiz_hard(self):
        self.stacked_game_modes.setCurrentWidget(self.hard_game_section)
        self.stacked_widget.setCurrentWidget(self.game_screen)
        self.start_timer()
        self.get_equation_hard()
        self.mode = 1

    def submit_answer(self):
        if self.question_number == 10:
            self.check_equation()
            self.end_quiz()
        else:
            self.check_equation()
            self.question_number += 1
            self.question_label.setText(f"Question {self.question_number}")
            self.get_equation()

        self.answer_entry.clear()

    def check_answer_hard(self, ans):
        if ans == self.correct_answer:
            print("Good guess")
            self.good_answers += 1
        else:
            print("Wrong")
        if self.question_number == 10:
            self.end_quiz()
        else:
            self.question_number += 1
            self.question_label_hard.setText(f"Question {self.question_number}")
            self.get_equation_hard()

    def get_equation(self):
        operation = random.randint(1, 4)
        if operation == 1:
            x = random.randint(1, 256)
            y = random.randint(0, 256)
            self.answer = x + y
            op_symbol = '+'
        elif operation == 2:
            x = random.randint(1, 256)
            y = random.randint(0, 256)
            self.answer = x - y
            op_symbol = '-'
        elif operation == 3:
            x = random.randint(1, 16)
            y = random.randint(0, 16)
            self.answer = x * y
            op_symbol = '*'
        elif operation == 4:
            y = random.randint(2, 20)
            x = y * random.randint(2, 20)
            self.answer = x / y
            op_symbol = '/'

        self.equation_label.setText(f"{x} {op_symbol} {y}")

    def generate_expression(self):
        x = sp.symbols('x')
        coeff_x2 = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
        coeff_x = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
        constant = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
        power_x2 = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
        power_x = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
        expr = coeff_x2 * x ** power_x2 + coeff_x * x ** power_x + constant
        return expr, x

    def generate_quadratic_expression(self):
        x = sp.symbols('x')
        coeff_x2 = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
        coeff_x = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
        constant = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
        delta = coeff_x2 ** 2 - 4 * coeff_x * constant
        while delta < 0:
            coeff_x2 = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
            coeff_x = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
            constant = sp.Rational(random.randint(1, 5), random.randint(1, 5)) * random.choice([1, -1])
            delta = coeff_x2 ** 2 - 4 * coeff_x * constant
        expr = coeff_x2 * x ** 2 + coeff_x * x + constant
        return expr, x

    def get_equation_hard(self):
        def compute_wrong_answer(expr, x, approach_value=None):
            if operation == 1:  # integral
                return sp.latex(sp.integrate(expr, x)) + r" + C"
            elif operation == 2:  # differential
                return sp.latex(sp.diff(expr, x))
            elif operation == 3:  # limit
                return sp.latex(sp.limit(expr, x, approach_value))
            elif operation == 4:  # quadratic equation
                return sp.latex(sp.solve(expr, x))

        operation = random.randint(1, 4)
        if operation == 1:  # integral
            expr, x = self.generate_expression()
            question = r"\int (" + sp.latex(expr) + r") \, dx"
            answer = sp.latex(sp.integrate(expr, x)) + r" + C"
        elif operation == 2:  # differential
            expr, x = self.generate_expression()
            question = r"\frac{d}{dx} \left(" + sp.latex(expr) + r"\right)"
            answer = sp.latex(sp.diff(expr, x))
        elif operation == 3:  # limit
            expr, x = self.generate_expression()
            approach_value = random.choice([0, sp.oo, -sp.oo, random.randint(-10, 10)])
            question = r"\lim_{" + sp.latex(x) + r"\to " + sp.latex(approach_value) + r"} \left(" + sp.latex(
                expr) + r"\right)"
            answer = sp.latex(sp.limit(expr, x, approach_value))
        elif operation == 4:  # quadratic equation
            expr, x = self.generate_quadratic_expression()
            question = sp.latex(expr) + r" = 0"
            answer = r"["+", ".join([sp.latex(sol) for sol in sp.solve(expr, x)]) +r"]"

        unique_answers = set()
        while len(unique_answers) < 4:
            if operation != 4:
                wrong_expr, wrong_x = self.generate_expression()
            else:
                wrong_expr, wrong_x = self.generate_quadratic_expression()
            if operation != 3:
                wrong_answer = compute_wrong_answer(wrong_expr, wrong_x)
            else:
                wrong_answer = compute_wrong_answer(wrong_expr, wrong_x, approach_value)
            if wrong_answer != answer and wrong_answer not in unique_answers:
                unique_answers.add(wrong_answer)
        wrong_answers = list(unique_answers)

        self.render_latex_to_label(question, self.equation_label_hard)
        correct_button = random.randint(1, 5)
        self.correct_answer = correct_button
        answers = wrong_answers[:]
        answers.insert(correct_button - 1, answer)
        for i, ans in enumerate(answers):
            self.render_latex_to_label(ans, getattr(self, f'answer_button_{i + 1}'))

    def render_latex_to_label(self, latex_str, widget):
        plt.figure(figsize=(5, 1))
        plt.text(0.5, 0.5, f"${latex_str}$", fontsize=20, ha='center', va='center')
        plt.axis('off')

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=200)
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        buffer.close()

        if isinstance(widget, QPushButton):
            icon = QIcon(pixmap)
            widget.setIcon(icon)
            widget.setIconSize(pixmap.size()/2)
        elif isinstance(widget, QLabel):
            widget.setPixmap(pixmap)

        plt.close()

    def check_equation(self):
        try:
            if int(self.answer_entry.text()) == self.answer:
                self.good_answers += 1
        except ValueError:
            pass

    def start_timer(self):
        if self.timer_thread and self.timer_thread.is_alive():
            self.stop_thread = True
            self.timer_thread.join()

        self.stop_thread = False
        self.timer_thread = threading.Thread(target=self.count_down, daemon=True)
        self.timer_thread.start()

    def count_down(self):
        for remaining_time in range(self.quiz_time, -1, -1):
            if self.stop_thread:
                break
            minutes, seconds = divmod(remaining_time, 60)
            self.time_updated.emit(minutes, seconds)
            time.sleep(1)

        if not self.stop_thread:
            self.end_quiz()

    def update_timer(self, minutes, seconds):
        self.timer_label.setText(f"{minutes:02}:{seconds:02}")
        self.progress_bar.setValue(minutes * 60 + seconds)

    def end_quiz(self):
        self.stop_thread = True
        self.stacked_widget.setCurrentWidget(self.end_screen)
        self.result_label.setText(f"Good answers: {self.good_answers}/10")

        try:
            self.answer_entry.returnPressed.disconnect(self.submit_answer)
        except TypeError:
            pass

    def restart(self):
        self.stop_thread = False
        self.question_number = 1
        self.good_answers = 0
        self.answer = 0
        self.progress_bar.setValue(self.quiz_time)
        if self.mode == 0:
            self.start_quiz()
            self.question_label.setText("Question 1")
        else:
            self.start_quiz_hard()
            self.question_label_hard.setText("Question 1")

    def back_to_menu(self):
        self.stacked_widget.setCurrentWidget(self.start_screen)
        self.stop_thread = False
        self.question_number = 1
        self.good_answers = 0
        self.answer = 0
        self.progress_bar.setValue(self.quiz_time)
        self.question_label.setText("Question 1")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    quiz = MathQuiz()
    quiz.show()
    sys.exit(app.exec())
