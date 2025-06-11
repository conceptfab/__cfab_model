import sys
import os
import zipfile
import rarfile
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt

class ModelCreator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Tworzenie pliku .model")
        self.setGeometry(200, 200, 500, 300)

        main_layout = QVBoxLayout()

        # Layout dla wyboru pliku preview
        preview_layout = QHBoxLayout()
        self.preview_label = QLabel("Plik preview.jpg:")
        self.preview_path_edit = QLineEdit()
        self.preview_path_edit.setReadOnly(True)
        self.preview_button = QPushButton("Wybierz...")
        self.preview_button.clicked.connect(self.selectPreviewFile)
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_path_edit)
        preview_layout.addWidget(self.preview_button)
        main_layout.addLayout(preview_layout)

        # Layout dla wyboru pliku info
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Plik info.json:")
        self.info_path_edit = QLineEdit()
        self.info_path_edit.setReadOnly(True)
        self.info_button = QPushButton("Wybierz...")
        self.info_button.clicked.connect(self.selectInfoFile)
        info_layout.addWidget(self.info_label)
        info_layout.addWidget(self.info_path_edit)
        info_layout.addWidget(self.info_button)
        main_layout.addLayout(info_layout)

        # Layout dla wyboru pliku archiwum
        archive_layout = QHBoxLayout()
        self.archive_label = QLabel("Plik archiwum (.zip/.rar):")
        self.archive_path_edit = QLineEdit()
        self.archive_path_edit.setReadOnly(True)
        self.archive_button = QPushButton("Wybierz...")
        self.archive_button.clicked.connect(self.selectArchiveFile)
        archive_layout.addWidget(self.archive_label)
        archive_layout.addWidget(self.archive_path_edit)
        archive_layout.addWidget(self.archive_button)
        main_layout.addLayout(archive_layout)

        # Layout dla zapisu pliku wyjściowego
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Plik wyjściowy .model:")
        self.output_path_edit = QLineEdit()
        self.output_button = QPushButton("Zapisz jako...")
        self.output_button.clicked.connect(self.saveOutputFile)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(self.output_button)
        main_layout.addLayout(output_layout)

        # Przycisk tworzenia
        self.create_button = QPushButton("Utwórz plik .model")
        self.create_button.clicked.connect(self.createModelFile)
        main_layout.addWidget(self.create_button)

        # Przycisk weryfikacji
        self.verify_button = QPushButton("Zweryfikuj plik .model")
        self.verify_button.clicked.connect(self.verifyModelFile)
        main_layout.addWidget(self.verify_button)

        # Label statusu
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

        self.preview_path = ""
        self.info_path = ""
        self.archive_path = ""
        self.output_path = ""

    def selectPreviewFile(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Wybierz plik preview.jpg", "", "Pliki JPG (*.jpg *.jpeg)")
        if fname:
            self.preview_path = fname
            self.preview_path_edit.setText(fname)

    def selectInfoFile(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Wybierz plik info.json", "", "Pliki JSON (*.json)")
        if fname:
            self.info_path = fname
            self.info_path_edit.setText(fname)

    def selectArchiveFile(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Wybierz plik archiwum (.zip/.rar)", "", "Pliki ZIP (*.zip);;Pliki RAR (*.rar)")
        if fname:
            self.archive_path = fname
            self.archive_path_edit.setText(fname)

    def saveOutputFile(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Zapisz plik .model", "", "Pliki .model (*.model)")
        if fname:
            if not fname.lower().endswith(".model"):
                fname += ".model"
            self.output_path = fname
            self.output_path_edit.setText(fname)

    def createModelFile(self):
        if not all([self.preview_path, self.info_path, self.archive_path, self.output_path]):
            QMessageBox.critical(self, "Błąd", "Proszę wybrać wszystkie wymagane pliki (preview.jpg, info.json, archiwum) i plik wyjściowy.")
            return

        try:
            self.status_label.setText("Tworzenie pliku .model...")
            with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_STORED) as model_zip:
                # Dodawanie pliku preview
                model_zip.write(self.preview_path, arcname="preview.jpg")

                # Dodawanie pliku info
                model_zip.write(self.info_path, arcname="info.json")

                # Dodawanie pliku archiwum
                archive_filename = os.path.basename(self.archive_path)
                model_zip.write(self.archive_path, arcname=archive_filename)

            self.status_label.setText("Plik .model utworzony pomyślnie!")
            QMessageBox.information(self, "Sukces", f"Plik '{self.output_path}' został utworzony pomyślnie.")

        except Exception as e:
            self.status_label.setText(f"Błąd podczas tworzenia: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas tworzenia pliku .model:\n{e}")

    def verifyModelFile(self):
        if not self.output_path:
            QMessageBox.critical(self, "Błąd", "Proszę wybrać plik .model do weryfikacji.")
            return

        if not os.path.exists(self.output_path):
            QMessageBox.critical(self, "Błąd", f"Plik '{self.output_path}' nie istnieje.")
            return

        try:
            self.status_label.setText("Weryfikacja pliku .model...")
            with zipfile.ZipFile(self.output_path, 'r') as model_zip:
                required_files = ["preview.jpg", "info.json"]
                found_files = model_zip.namelist()

                # Sprawdzenie, czy wymagane pliki istnieją
                missing_files = [f for f in required_files if f not in found_files]
                if missing_files:
                    self.status_label.setText(f"Weryfikacja nieudana: Brakuje wymaganych plików: {', '.join(missing_files)}")
                    QMessageBox.warning(self, "Weryfikacja", f"Plik '{self.output_path}' nie zawiera wszystkich wymaganych plików: {', '.join(missing_files)}")
                    return

                # Sprawdzenie i odczyt info.json
                try:
                    with model_zip.open("info.json") as info_file:
                        info_content = info_file.read().decode('utf-8')
                        info_data = json.loads(info_content)
                        # Można dodać dodatkowe walidacje zawartości info.json
                        # print(f"Odczytano info.json: {info_data}")
                except json.JSONDecodeError:
                    self.status_label.setText("Weryfikacja nieudana: Plik info.json nie jest poprawnym JSON.")
                    QMessageBox.warning(self, "Weryfikacja", f"Plik info.json nie jest poprawnym formatem JSON.")
                    return
                except Exception as e:
                    self.status_label.setText(f"Weryfikacja nieudana: Błąd podczas odczytu info.json: {e}")
                    QMessageBox.warning(self, "Weryfikacja", f"Wystąpił błąd podczas odczytu pliku info.json:\n{e}")
                    return

                # Sprawdzenie obecności pliku archiwum
                archive_files = [f for f in found_files if f not in required_files]
                if len(archive_files) != 1:
                    self.status_label.setText("Weryfikacja nieudana: Oczekiwano dokładnie jednego pliku archiwum.")
                    QMessageBox.warning(self, "Weryfikacja", f"Oczekiwano dokładnie jednego pliku archiwum wewnątrz '{self.output_path}'. Znaleziono {len(archive_files)}.")
                    return

                archive_filename_in_zip = archive_files[0]
                # Opcjonalnie: Sprawdzenie, czy plik archiwum wewnątrz jest faktycznie ZIP lub RAR
                # To jest bardziej skomplikowane, ponieważ wymaga próby otwarcia pliku archiwum
                # z wewnątrz ZIP. W tym prostym przykładzie, sprawdzamy tylko jego obecność.

                self.status_label.setText("Weryfikacja pliku .model zakończona pomyślnie!")
                QMessageBox.information(self, "Sukces", f"Plik '{self.output_path}' został zweryfikowany pomyślnie. Zawiera preview.jpg, info.json i plik archiwum '{archive_filename_in_zip}'.")

        except zipfile.BadZipFile:
            self.status_label.setText("Weryfikacja nieudana: Plik .model jest uszkodzony lub nie jest prawidłowym archiwum ZIP.")
            QMessageBox.critical(self, "Błąd", f"Plik '{self.output_path}' jest uszkodzony lub nie jest prawidłowym archiwum ZIP.")
        except Exception as e:
            self.status_label.setText(f"Weryfikacja nieudana: Błąd: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas weryfikacji pliku .model:\n{e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModelCreator()
    window.show()
    sys.exit(app.exec())