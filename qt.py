import sys
import random
import threading
import time
import sympy as sp
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QProgressBar, QStackedWidget, QSizePolicy, QSlider
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
        self.quesions = 10
        self.answer = 0
        self.quiz_time = 70
        self.timer_thread = None
        self.stop_thread = False
        self.correct_answer = 0
        self.mode = 0 # 0-easy

        self.initUI()


    def create_button(self, text, callback):
        button = QPushButton(text)
        button.setFixedHeight(80)
        button.setStyleSheet("""
            QPushButton {
                background-color: #006400;
                color: white;
                font-size: 25px;
                border: 2px solid #006400;
                border-radius: 10px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #008000;
            }
            QPushButton:pressed {
                background-color: #011d15;
            }
        """)
        button.clicked.connect(callback)
        return button


    def create_answer_button(self, label, answer_number):
        button = QPushButton(label)
        button.clicked.connect(lambda: self.check_answer_hard(answer_number))
        button.setStyleSheet("""
            QPushButton {
                background-color: #383e47;
                color: white;
                font-size: 18px;
                border: 2px solid #383e47;
                border-radius: 10px;
                padding: 8px;
            }
            QPushButton:hover {
                 background-color: #006400;
            }
            QPushButton:pressed {
                background-color: #011d15;
            }
        """)
        return button


    def initUI(self):
        self.setWindowTitle('Math Quiz')
        self.setGeometry(100, 100, 900, 900)
        self.setStyleSheet("background-color: #3b4049;")

        # Main layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Stacked widget to switch between screens
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Start screen
        self.start_screen = QWidget()
        self.start_screen.setStyleSheet("background-color: #3b4049;")
        self.start_layout = QVBoxLayout()
        self.start_screen.setLayout(self.start_layout)

        self.start_label = QLabel(f"You will answer 10 math\nquestions in 01:10 minutes.\nAre you ready?")
        self.start_label.setAlignment(Qt.AlignCenter)
        self.start_label.setStyleSheet("font-size: 24px; color: white;")
        self.start_layout.addWidget(self.start_label)

        self.questions_layout = QHBoxLayout()
        self.questions_layout.setSpacing(50)
        self.questions_slider_label = QLabel("Questions")
        self.questions_slider_label.setStyleSheet("font-size: 24px; color: white;")
        self.questions_slider = QSlider(Qt.Horizontal)
        self.questions_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #006400;
                border: 1px solid #FFFFFF;
                width: 20px;
                height: 20px;
            }
        """)
        self.questions_slider.setMinimum(1)
        self.questions_slider.setMaximum(100)
        self.questions_slider.setValue(10)
        self.questions_slider.valueChanged.connect(self.update_label)
        self.start_layout.addWidget(self.questions_slider)
        self.questions_layout.addWidget(self.questions_slider_label)
        self.questions_layout.addWidget(self.questions_slider)
        self.start_layout.addLayout(self.questions_layout)

        self.time_layout = QHBoxLayout()
        self.time_layout.setSpacing(103)
        self.time_slider_label = QLabel("Time")
        self.time_slider_label.setStyleSheet("font-size: 24px; color: white;")
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #006400;
                border: 1px solid #FFFFFF;
                width: 20px;
                height: 20px;
            }
        """)
        self.time_slider.setMinimum(10)
        self.time_slider.setMaximum(600)
        self.time_slider.setValue(70)
        self.time_slider.valueChanged.connect(self.update_label)
        self.start_layout.addWidget(self.time_slider)
        self.time_layout.addWidget(self.time_slider_label)
        self.time_layout.addWidget(self.time_slider)
        self.start_layout.addLayout(self.time_layout)

        self.btns_layout = QHBoxLayout()
        self.start_button = self.create_button("Play easy", self.start_quiz)
        self.btns_layout.addWidget(self.start_button)

        self.start_hard = self.create_button("Play hard", self.start_quiz_hard)
        self.btns_layout.addWidget(self.start_hard)

        self.start_layout.addLayout(self.btns_layout)
        self.stacked_widget.addWidget(self.start_screen)

        # Game screen
        self.game_screen = QWidget()
        self.game_layout = QHBoxLayout()
        self.game_screen.setStyleSheet("background-color: #3b4049;")
        self.game_screen.setLayout(self.game_layout)

        # Timer section (left side)
        self.timer_section = QVBoxLayout()
        self.timer_label = QLabel("Time Left")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 24px; color: white;")
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
        self.question_label.setStyleSheet("font-size: 40px; color: white;")
        self.game_content_layout_easy.addWidget(self.question_label)

        self.equation_label = QLabel("Equation 1")
        self.equation_label.setAlignment(Qt.AlignCenter)
        self.equation_label.setStyleSheet("font-size: 50px; color: white;")
        self.game_content_layout_easy.addWidget(self.equation_label)

        self.answer_entry = QLineEdit()
        self.answer_entry.setAlignment(Qt.AlignCenter)
        self.answer_entry.setStyleSheet("font-size: 24px; color: white;")
        self.game_content_layout_easy.addWidget(self.answer_entry)

        self.next_question_button = self.create_button("Next Question", self.submit_answer)
        self.game_content_layout_easy.addWidget(self.next_question_button)

        self.easy_game_section = QWidget()
        self.easy_game_section.setLayout(self.game_content_layout_easy)

        # Hard mode game section
        self.game_content_layout_hard = QVBoxLayout()

        self.question_label_hard = QLabel("Question 1")
        self.question_label_hard.setAlignment(Qt.AlignCenter)
        self.question_label_hard.setStyleSheet("font-size: 40px; color: white;")
        self.game_content_layout_hard.addWidget(self.question_label_hard)

        self.equation_label_hard = QLabel("Equation 1")
        self.equation_label_hard.setAlignment(Qt.AlignCenter)
        self.game_content_layout_hard.addWidget(self.equation_label_hard)

        buttons = [("A", 1), ("B", 2), ("C", 3), ("D", 4), ("E", 5)]
        for label, number in buttons:
            button = self.create_answer_button(label, number)
            setattr(self, f"answer_button_{number}", button)
            self.game_content_layout_hard.addWidget(button)

        self.hard_game_section = QWidget()
        self.hard_game_section.setLayout(self.game_content_layout_hard)

        self.stacked_game_modes.addWidget(self.easy_game_section)
        self.stacked_game_modes.addWidget(self.hard_game_section)

        self.stacked_widget.addWidget(self.game_screen)

        # End screen
        self.end_screen = QWidget()
        self.end_layout = QVBoxLayout()
        self.end_screen.setLayout(self.end_layout)
        self.end_screen.setStyleSheet("background-color: #3b4049;")

        self.result_label = QLabel("Good answers: 0/10")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 30px; color: white;")
        self.end_layout.addWidget(self.result_label)

        self.end_btns_layout = QHBoxLayout()
        self.restart_button = self.create_button("Play Again", self.restart)
        self.end_btns_layout.addWidget(self.restart_button)

        self.back_to_menu_button = self.create_button("Back to menu", self.back_to_menu)
        self.end_btns_layout.addWidget(self.back_to_menu_button)
        self.end_layout.addLayout(self.end_btns_layout)
        self.stacked_widget.addWidget(self.end_screen)

        self.stacked_widget.setCurrentWidget(self.start_screen)

        self.time_updated.connect(self.update_timer)

    def update_label(self):
        questions = self.questions_slider.value()
        time = self.time_slider.value()
        minutes, seconds = divmod(time, 60)
        self.start_label.setText(f"You will answer {questions} math\nquestions in {minutes:02}:{seconds:02} minutes.\nAre you ready?")


    def start_quiz(self):
        self.quesions = self.questions_slider.value()
        self.quiz_time = self.time_slider.value()
        self.progress_bar.setMaximum(self.quiz_time)
        self.stacked_game_modes.setCurrentWidget(self.easy_game_section)
        self.stacked_widget.setCurrentWidget(self.game_screen)
        self.answer_entry.setFocus()
        self.start_timer()
        self.get_equation()
        self.answer_entry.returnPressed.connect(self.submit_answer)
        self.mode = 0

    def start_quiz_hard(self):
        self.quesions = self.questions_slider.value()
        self.quiz_time = self.time_slider.value()
        self.progress_bar.setMaximum(self.quiz_time)
        self.stacked_game_modes.setCurrentWidget(self.hard_game_section)
        self.stacked_widget.setCurrentWidget(self.game_screen)
        self.start_timer()
        self.get_equation_hard()
        self.mode = 1

    def submit_answer(self):
        if self.question_number == self.quesions:
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
            #print("Good guess")
            self.good_answers += 1
        #else:
            #print("Wrong")
        if self.question_number == self.quesions:
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
        x1 = random.randint(-10, 10)
        x2 = random.randint(-10, 10)
        a = random.randint(1, 5) * random.choice([1, -1])
        expr = a * (x - x1) * (x - x2)
        expr = sp.expand(expr)

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
            approach_value = random.choice([0, sp.oo, random.randint(-10, 10)])
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
        if isinstance(widget, QPushButton):
            facecolor = '#006400'
        elif isinstance(widget, QLabel):
            facecolor = '#3b4049'

        plt.figure(figsize=(5, 1), facecolor=facecolor)
        plt.text(0.5, 0.5, f"${latex_str}$", fontsize=25, ha='center', va='center', color='white')
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
        self.result_label.setText(f"Good answers: {self.good_answers}/{self.quesions}")
        if self.mode == 0:
            self.answer_entry.returnPressed.disconnect(self.submit_answer)


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
