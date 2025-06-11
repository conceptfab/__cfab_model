import sys
import os
import zipfile
import rarfile
import json
import time
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QInputDialog,
)
from PyQt6.QtCore import Qt


class ModelCreator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Tworzenie/Weryfikacja pliku .model")
        self.setGeometry(200, 200, 500, 400)

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
        self.output_path_edit.setReadOnly(True)
        self.output_button = QPushButton("Zapisz jako...")
        self.output_button.clicked.connect(self.saveOutputFile)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(self.output_button)
        main_layout.addLayout(output_layout)

        # Layout dla opcji szyfrowania
        encrypt_layout = QHBoxLayout()
        self.encrypt_checkbox = QPushButton("Szyfruj archiwum (ZipCrypto)")
        encrypt_layout.addWidget(self.encrypt_checkbox)
        main_layout.addLayout(encrypt_layout)

        # Przycisk tworzenia i weryfikacji
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Utwórz plik .model")
        self.create_button.clicked.connect(self.createModelFile)
        self.verify_button = QPushButton("Zweryfikuj plik .model")
        self.verify_button.clicked.connect(self.verifyModelFile)
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.verify_button)
        main_layout.addLayout(button_layout)

        # Label statusu i czasu
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        self.time_label = QLabel("")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.time_label)

        self.setLayout(main_layout)

        self.preview_path = ""
        self.info_path = ""
        self.archive_path = ""
        self.output_path = ""
        self.is_encrypted = False

    def selectPreviewFile(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik preview.jpg", "", "Pliki JPG (*.jpg *.jpeg)"
        )
        if fname:
            self.preview_path = fname
            self.preview_path_edit.setText(fname)

    def selectInfoFile(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik info.json", "", "Pliki JSON (*.json)"
        )
        if fname:
            self.info_path = fname
            self.info_path_edit.setText(fname)

    def selectArchiveFile(self):
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik archiwum (.zip/.rar)",
            "",
            "Pliki ZIP (*.zip);;Pliki RAR (*.rar)",
        )
        if fname:
            self.archive_path = fname
            self.archive_path_edit.setText(fname)

    def saveOutputFile(self):
        fname, _ = QFileDialog.getSaveFileName(
            self, "Zapisz plik .model", "", "Pliki .model (*.model)"
        )
        if fname:
            if not fname.lower().endswith(".model"):
                fname += ".model"
            self.output_path = fname
            self.output_path_edit.setText(fname)

    def toggleEncryption(self):
        self.is_encrypted = not self.is_encrypted
        if self.is_encrypted:
            self.encrypt_checkbox.setText("Archiwum szyfrowane (ZipCrypto)")
        else:
            self.encrypt_checkbox.setText("Szyfruj archiwum (ZipCrypto)")

    def createModelFile(self):
        if not all(
            [self.preview_path, self.info_path, self.archive_path, self.output_path]
        ):
            QMessageBox.critical(
                self,
                "Błąd",
                "Proszę wybrać wszystkie wymagane pliki (preview.jpg, info.json, archiwum) i plik wyjściowy.",
            )
            return

        password = None
        if self.is_encrypted:
            password, ok = QInputDialog.getText(
                self,
                "Hasło do szyfrowania",
                "Wprowadź hasło dla archiwum:",
                QLineEdit.Echo.Password,
            )
            if not ok or not password:
                QMessageBox.critical(
                    self,
                    "Błąd",
                    "Hasło jest wymagane dla szyfrowania i nie zostało poprawnie wprowadzone.",
                )
                return

        start_time = time.time()
        self.status_label.setText("Tworzenie pliku .model...")
        self.time_label.setText("")

        try:
            with zipfile.ZipFile(
                self.output_path, "w", zipfile.ZIP_STORED
            ) as model_zip:
                if password:
                    model_zip.setpassword(password.encode("utf-8"))

                # Dodawanie pliku preview
                model_zip.write(self.preview_path, arcname="preview.jpg")

                # Dodawanie pliku info
                model_zip.write(self.info_path, arcname="info.json")

                # Dodawanie pliku archiwum
                archive_filename = os.path.basename(self.archive_path)
                model_zip.write(self.archive_path, arcname=archive_filename)

            end_time = time.time()
            elapsed_time = end_time - start_time
            self.status_label.setText("Plik .model utworzony pomyślnie!")
            self.time_label.setText(f"Czas utworzenia: {elapsed_time:.4f} s")
            QMessageBox.information(
                self,
                "Sukces",
                f"Plik '{self.output_path}' został utworzony pomyślnie.\nCzas utworzenia: {elapsed_time:.4f} s",
            )

        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.status_label.setText(f"Błąd podczas tworzenia: {e}")
            self.time_label.setText(f"Czas próby: {elapsed_time:.4f} s")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas tworzenia pliku .model:\n{e}\nCzas próby: {elapsed_time:.4f} s",
            )

    def verifyModelFile(self):
        if not self.output_path:
            QMessageBox.critical(
                self, "Błąd", "Proszę wybrać plik .model do weryfikacji."
            )
            return

        if not os.path.exists(self.output_path):
            QMessageBox.critical(
                self, "Błąd", f"Plik '{self.output_path}' nie istnieje."
            )
            return

        password = None
        try:
            with zipfile.ZipFile(self.output_path, "r") as model_zip:
                # Sprawdzenie, czy archiwum wymaga hasła (próba odczytania listy plików)
                try:
                    model_zip.namelist()
                except RuntimeError:
                    # Jeśli namelist() rzuci RuntimeError, prawdopodobnie hasło jest wymagane
                    password, ok = QInputDialog.getText(
                        self,
                        "Hasło do odszyfrowania",
                        "Wprowadź hasło dla archiwum:",
                        QLineEdit.Echo.Password,
                    )
                    if not ok or not password:
                        QMessageBox.critical(
                            self,
                            "Błąd",
                            "Hasło jest wymagane do odszyfrowania i nie zostało poprawnie wprowadzone.",
                        )
                        return
        except zipfile.BadZipFile:
            QMessageBox.critical(
                self,
                "Błąd",
                f"Plik '{self.output_path}' jest uszkodzony lub nie jest prawidłowym archiwum ZIP.",
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self, "Błąd", f"Wystąpił błąd podczas próby otwarcia pliku:\n{e}"
            )
            return

        start_time = time.time()
        self.status_label.setText("Weryfikacja pliku .model...")
        self.time_label.setText("")

        try:
            with zipfile.ZipFile(self.output_path, "r") as model_zip:
                if password:
                    model_zip.setpassword(password.encode("utf-8"))

                required_files = ["preview.jpg", "info.json"]
                found_files = model_zip.namelist()

                # Sprawdzenie, czy wymagane pliki istnieją
                missing_files = [f for f in required_files if f not in found_files]
                if missing_files:
                    self.status_label.setText(
                        f"Weryfikacja nieudana: Brakuje wymaganych plików: {', '.join(missing_files)}"
                    )
                    QMessageBox.warning(
                        self,
                        "Weryfikacja",
                        f"Plik '{self.output_path}' nie zawiera wszystkich wymaganych plików: {', '.join(missing_files)}",
                    )
                    return

                # Sprawdzenie i odczyt info.json
                try:
                    with model_zip.open("info.json") as info_file:
                        info_content = info_file.read().decode("utf-8")
                        info_data = json.loads(info_content)
                        # Można dodać dodatkowe walidacje zawartości info.json
                        # print(f"Odczytano info.json: {info_data}")
                except json.JSONDecodeError:
                    self.status_label.setText(
                        "Weryfikacja nieudana: Plik info.json nie jest poprawnym JSON."
                    )
                    QMessageBox.warning(
                        self,
                        "Weryfikacja",
                        f"Plik info.json nie jest poprawnym formatem JSON.",
                    )
                    return
                except Exception as e:
                    self.status_label.setText(
                        f"Weryfikacja nieudana: Błąd podczas odczytu info.json: {e}"
                    )
                    QMessageBox.warning(
                        self,
                        "Weryfikacja",
                        f"Wystąpił błąd podczas odczytu pliku info.json:\n{e}",
                    )
                    return

                # Sprawdzenie obecności pliku archiwum
                archive_files = [f for f in found_files if f not in required_files]
                if len(archive_files) != 1:
                    self.status_label.setText(
                        "Weryfikacja nieudana: Oczekiwano dokładnie jednego pliku archiwum."
                    )
                    QMessageBox.warning(
                        self,
                        "Weryfikacja",
                        f"Oczekiwano dokładnie jednego pliku archiwum wewnątrz '{self.output_path}'. Znaleziono {len(archive_files)}.",
                    )
                    return

                archive_filename_in_zip = archive_files[0]

                end_time = time.time()
                elapsed_time = end_time - start_time
                self.status_label.setText(
                    "Weryfikacja pliku .model zakończona pomyślnie!"
                )
                self.time_label.setText(f"Czas weryfikacji: {elapsed_time:.4f} s")
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Plik '{self.output_path}' został zweryfikowany pomyślnie. Zawiera preview.jpg, info.json i plik archiwum '{archive_filename_in_zip}'.\nCzas weryfikacji: {elapsed_time:.4f} s",
                )

        except zipfile.BadZipFile:
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.status_label.setText(
                "Weryfikacja nieudana: Plik .model jest uszkodzony lub nie jest prawidłowym archiwum ZIP."
            )
            self.time_label.setText(f"Czas próby: {elapsed_time:.4f} s")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Plik '{self.output_path}' jest uszkodzony lub nie jest prawidłowym archiwum ZIP.\nCzas próby: {elapsed_time:.4f} s",
            )
        except RuntimeError as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.status_label.setText(f"Weryfikacja nieudana: Nieprawidłowe hasło. {e}")
            self.time_label.setText(f"Czas próby: {elapsed_time:.4f} s")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Nieprawidłowe hasło do odszyfrowania pliku .model.\n{e}\nCzas próby: {elapsed_time:.4f} s",
            )
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.status_label.setText(f"Weryfikacja nieudana: Błąd: {e}")
            self.time_label.setText(f"Czas próby: {elapsed_time:.4f} s")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas weryfikacji pliku .model:\n{e}\nCzas próby: {elapsed_time:.4f} s",
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModelCreator()
    window.show()
    sys.exit(app.exec())
