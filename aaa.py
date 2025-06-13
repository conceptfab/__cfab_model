import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QGridLayout,
    QMessageBox,
    QWidget,
)
from PyQt6.QtCore import Qt


class TicTacToe(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Kółko i Krzyżyk")
        self.setGeometry(100, 100, 300, 300)

        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.game_over = False

        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout()

        for i in range(3):
            for j in range(3):
                self.buttons[i][j] = QPushButton("")
                self.buttons[i][j].setMinimumSize(80, 80)
                self.buttons[i][j].setStyleSheet("font-size: 30px;")
                self.buttons[i][j].clicked.connect(
                    lambda checked, row=i, col=j: self.button_click(row, col)
                )
                self.layout.addWidget(self.buttons[i][j], i, j)

        self.central_widget.setLayout(self.layout)

    def button_click(self, row, col):
        if self.game_over or self.buttons[row][col].text() != "":
            return

        self.buttons[row][col].setText(self.current_player)
        self.buttons[row][col].setEnabled(False)

        if self.check_win():
            QMessageBox.information(
                self, "Zwycięstwo!", f"Gracz {self.current_player} wygrał!"
            )
            self.game_over = True
        elif self.check_draw():
            QMessageBox.information(self, "Remis!", "Gra zakończyła się remisem!")
            self.game_over = True
        else:
            self.switch_player()

    def check_win(self):
        # Sprawdzenie wierszy
        for i in range(3):
            if (
                self.buttons[i][0].text() == self.current_player
                and self.buttons[i][1].text() == self.current_player
                and self.buttons[i][2].text() == self.current_player
            ):
                return True

        # Sprawdzenie kolumn
        for j in range(3):
            if (
                self.buttons[0][j].text() == self.current_player
                and self.buttons[1][j].text() == self.current_player
                and self.buttons[2][j].text() == self.current_player
            ):
                return True

        # Sprawdzenie przekątnych
        if (
            self.buttons[0][0].text() == self.current_player
            and self.buttons[1][1].text() == self.current_player
            and self.buttons[2][2].text() == self.current_player
        ):
            return True

        if (
            self.buttons[0][2].text() == self.current_player
            and self.buttons[1][1].text() == self.current_player
            and self.buttons[2][0].text() == self.current_player
        ):
            return True

        return False

    def check_draw(self):
        for i in range(3):
            for j in range(3):
                if self.buttons[i][j].text() == "":
                    return False
        return True

    def switch_player(self):
        self.current_player = "O" if self.current_player == "X" else "X"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TicTacToe()
    window.show()
    sys.exit(app.exec())
