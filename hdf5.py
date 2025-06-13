import sys
import os
import zipfile
import rarfile
import json
import time
import h5py
import io
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
        self.setWindowTitle("Tworzenie/Weryfikacja pliku .model (HDF5)")
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

        # Przycisk tworzenia i weryfikacji
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Utwórz plik .model (HDF5)")
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

        start_time = time.time()
        self.status_label.setText("Tworzenie pliku .model (HDF5)...")
        self.time_label.setText("")

        try:
            with h5py.File(self.output_path, "w") as h5f:
                # Zapisz preview.jpg
                with open(self.preview_path, "rb") as f_preview:
                    preview_data = f_preview.read()
                    h5f.create_dataset("preview.jpg", data=preview_data)

                # Zapisz info.json
                with open(self.info_path, "rb") as f_info:
                    info_data = f_info.read()
                    h5f.create_dataset("info.json", data=info_data)

                # Zapisz archiwum
                with open(self.archive_path, "rb") as f_archive:
                    archive_data = f_archive.read()
                    archive_filename = os.path.basename(self.archive_path)
                    h5f.create_dataset(f"archive/{archive_filename}", data=archive_data)

            end_time = time.time()
            elapsed_time = end_time - start_time
            self.status_label.setText("Plik .model (HDF5) utworzony pomyślnie!")
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
                f"Wystąpił błąd podczas tworzenia pliku .model (HDF5):\n{e}\nCzas próby: {elapsed_time:.4f} s",
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

        start_time = time.time()
        self.status_label.setText("Weryfikacja pliku .model (HDF5)...")
        self.time_label.setText("")

        try:
            with h5py.File(self.output_path, "r") as h5f:
                required_datasets = ["preview.jpg", "info.json"]
                found_datasets = list(h5f.keys())

                # Sprawdzenie, czy wymagane datasety istnieją
                missing_datasets = [
                    d for d in required_datasets if d not in found_datasets
                ]
                if missing_datasets:
                    self.status_label.setText(
                        f"Weryfikacja nieudana: Brakuje wymaganych datasetów: {', '.join(missing_datasets)}"
                    )
                    QMessageBox.warning(
                        self,
                        "Weryfikacja",
                        f"Plik '{self.output_path}' nie zawiera wszystkich wymaganych datasetów: {', '.join(missing_datasets)}",
                    )
                    return

                # Sprawdzenie i odczyt info.json
                try:
                    info_data = h5f["info.json"][:]  # Odczytanie całego datasetu
                    info_content = info_data.tobytes().decode("utf-8")
                    json.loads(info_content)
                    # Można dodać dodatkowe walidacje zawartości info.json
                    # print(f"Odczytano info.json: {info_data}")
                except json.JSONDecodeError:
                    self.status_label.setText(
                        "Weryfikacja nieudana: Plik info.json nie jest poprawnym JSON."
                    )
                    QMessageBox.warning(
                        self,
                        "Weryfikacja",
                        f"Plik info.json w pliku '{self.output_path}' nie jest poprawnym formatem JSON.",
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

                # Sprawdzenie obecności datasetu archiwum
                archive_datasets = [
                    d for d in found_datasets if d.startswith("archive/")
                ]
                if len(archive_datasets) != 1:
                    self.status_label.setText(
                        "Weryfikacja nieudana: Oczekiwano dokładnie jednego datasetu archiwum."
                    )
                    QMessageBox.warning(
                        self,
                        "Weryfikacja",
                        f"Oczekiwano dokładnie jednego datasetu archiwum w pliku '{self.output_path}'. Znaleziono {len(archive_datasets)}.",
                    )
                    return

                archive_dataset_name = archive_datasets[0]
                archive_data = h5f[archive_dataset_name][
                    :
                ]  # Odczytanie całego datasetu

                # Opcjonalnie: Spróbuj otworzyć archiwum w pamięci jako ZIP/RAR
                try:
                    import io

                    archive_buffer = io.BytesIO(archive_data)
                    with zipfile.ZipFile(archive_buffer, "r") as temp_zip:
                        temp_zip.namelist()
                except zipfile.BadZipFile:
                    try:
                        archive_buffer.seek(0)  # Wróć na początek bufora dla RAR
                        with rarfile.RarFile(archive_buffer, "r") as temp_rar:
                            temp_rar.namelist()
                    except rarfile.NotRarFile:
                        self.status_label.setText(
                            f"Weryfikacja nieudana: Plik archiwum '{archive_dataset_name}' nie jest prawidłowym ZIP ani RAR."
                        )
                        QMessageBox.warning(
                            self,
                            "Weryfikacja",
                            f"Plik archiwum '{archive_dataset_name}' w pliku '{self.output_path}' nie jest prawidłowym ZIP ani RAR.",
                        )
                        return
                    except Exception as e:
                        self.status_label.setText(
                            f"Weryfikacja nieudana: Błąd podczas otwierania archiwum RAR {archive_dataset_name}: {e}"
                        )
                        QMessageBox.warning(
                            self,
                            "Weryfikacja",
                            f"Wystąpił błąd podczas weryfikacji archiwum RAR '{archive_dataset_name}':\n{e}",
                        )
                        return
                except Exception as e:
                    self.status_label.setText(
                        f"Weryfikacja nieudana: Błąd podczas otwierania archiwum ZIP {archive_dataset_name}: {e}"
                    )
                    QMessageBox.warning(
                        self,
                        "Weryfikacja",
                        f"Wystąpił błąd podczas weryfikacji archiwum ZIP '{archive_dataset_name}':\n{e}",
                    )
                    return

                end_time = time.time()
                elapsed_time = end_time - start_time
                self.status_label.setText(
                    "Weryfikacja pliku .model (HDF5) zakończona pomyślnie!"
                )
                self.time_label.setText(f"Czas weryfikacji: {elapsed_time:.4f} s")
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Plik '{self.output_path}' został zweryfikowany pomyślnie. Zawiera preview.jpg, info.json i plik archiwum '{archive_dataset_name}'.\nCzas weryfikacji: {elapsed_time:.4f} s",
                )

        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.status_label.setText(f"Weryfikacja nieudana: Błąd: {e}")
            self.time_label.setText(f"Czas próby: {elapsed_time:.4f} s")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas weryfikacji pliku .model (HDF5):\n{e}\nCzas próby: {elapsed_time:.4f} s",
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModelCreator()
    window.show()
    sys.exit(app.exec())
