import json
import logging  # Upewnij się, że logging jest skonfigurowany
import os
import struct
import sys
import time
import zipfile

import rarfile  # Pamiętaj o potencjalnej potrzebie instalacji (pip install rarfile) i unrar
from PyQt6.QtCore import Qt  # Upewniono się, że Qt jest importowane
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Konfiguracja loggingu
# Ustaw poziom logowania, format i miejsce docelowe (np. plik lub konsola)
# Można to zrobić bardziej globalnie, jeśli aplikacja ma wiele modułów
log_file_path = os.path.join(
    os.path.dirname(__file__) if __file__ else ".", "model_creator.log"
)
logging.basicConfig(
    level=logging.DEBUG,  # Zapisuj logi od poziomu DEBUG wzwyż
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(
            log_file_path, encoding="utf-8"
        ),  # Logi do pliku z kodowaniem UTF-8
        logging.StreamHandler(sys.stdout),  # Opcjonalnie: logi również do konsoli
    ],
)

logger = logging.getLogger(__name__)  # Utwórz instancję loggera dla tego modułu


class ModelCreator(QWidget):
    def __init__(self):
        super().__init__()
        logger.info("Inicjalizacja ModelCreator UI.")
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Tworzenie/Weryfikacja pliku .model (z indekssem)")
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

        # Przycisk wczytywania danych z pliku .model
        self.load_button = QPushButton("Wczytaj Info z .model")
        self.load_button.clicked.connect(self.loadAndDisplayInfoFromModel)
        main_layout.addWidget(self.load_button)  # Dodajemy nowy przycisk do layoutu

        self.setLayout(main_layout)

        self.preview_path = ""
        self.info_path = ""
        self.archive_path = ""
        self.output_path = ""
        logger.debug("Zmienne ścieżek zainicjalizowane.")

    def _verify_and_extract_info_json(self, info_data_bytes, model_file_path):
        logger.debug(
            f"Rozpoczęcie weryfikacji i ekstrakcji info.json z pliku: {model_file_path}"
        )
        try:
            info_content_str = info_data_bytes.decode("utf-8")
            logger.debug("Pomyślnie zdekodowano info_data_bytes jako UTF-8.")
            info_json = json.loads(info_content_str)
            logger.debug("Pomyślnie sparsowano info.json.")
        except UnicodeDecodeError as e:
            logger.error(
                f"Błąd dekodowania UTF-8 dla info.json z {model_file_path}: {e}",
                exc_info=True,
            )
            self.status_label.setText(
                "Weryfikacja nieudana: Nie można zdekodować info.json (oczekiwano UTF-8)."
            )
            QMessageBox.critical(
                self,
                "Błąd weryfikacji",
                f"Plik info.json w '{model_file_path}' ma nieprawidłowe kodowanie (oczekiwano UTF-8).",
            )
            return None
        except json.JSONDecodeError as e:
            logger.error(
                f"Błąd parsowania JSON dla info.json z {model_file_path}: {e}",
                exc_info=True,
            )
            self.status_label.setText(
                "Weryfikacja nieudana: Plik info.json nie jest poprawnym JSON."
            )
            QMessageBox.critical(
                self,
                "Błąd weryfikacji",
                f"Plik info.json w '{model_file_path}' nie jest poprawnym formatem JSON.",
            )
            return None

        if not isinstance(info_json, dict):
            logger.error(
                f"Weryfikacja nieudana: Główna struktura info.json nie jest obiektem w {model_file_path}."
            )
            self.status_label.setText(
                "Weryfikacja nieudana: Główna struktura info.json nie jest obiektem."
            )
            QMessageBox.critical(
                self,
                "Błąd weryfikacji",
                f"Główna struktura pliku info.json w '{model_file_path}' nie jest obiektem (słownikiem).",
            )
            return None

        # Przykładowa weryfikacja wymaganych kluczy
        required_keys = [
            "nazwa_modelu",
            "wersja",
        ]  # Można dodać więcej np. "autor", "opis"
        for key in required_keys:
            if key not in info_json:
                logger.error(
                    f"Weryfikacja nieudana: Brak klucza '{key}' in info.json w {model_file_path}."
                )
                self.status_label.setText(
                    f"Weryfikacja nieudana: Brak klucza '{key}' w info.json."
                )
                QMessageBox.critical(
                    self,
                    "Błąd weryfikacji",
                    f"Brak wymaganego klucza '{key}' w pliku info.json w '{model_file_path}'.",
                )
                return None

        # Tutaj można dodać więcej szczegółowych weryfikacji, np. typów wartości
        # Przykład:
        # if not isinstance(info_json.get("wersja"), str):
        #     self.status_label.setText("Weryfikacja nieudana: Klucz 'wersja' w info.json nie jest tekstem.")
        #     QMessageBox.critical(self, "Błąd weryfikacji", f"Klucz 'wersja' w info.json w '{model_file_path}' musi być tekstem.")
        #     return None

        logger.info(
            f"Pomyślnie zweryfikowano i sparsowano info.json z {model_file_path}."
        )
        return info_json

    def selectPreviewFile(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik preview.jpg", "", "Pliki JPG (*.jpg *.jpeg)"
        )
        if fname:
            logger.info(f"Wybrano plik preview: {fname}")
            self.preview_path = fname
            self.preview_path_edit.setText(fname)
        else:
            logger.debug("Nie wybrano pliku preview.")

    def selectInfoFile(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik info.json", "", "Pliki JSON (*.json)"
        )
        if fname:
            logger.info(f"Wybrano plik info: {fname}")
            self.info_path = fname
            self.info_path_edit.setText(fname)
        else:
            logger.debug("Nie wybrano pliku info.")

    def selectArchiveFile(self):
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik archiwum (.zip/.rar)",
            "",
            "Pliki ZIP (*.zip);;Pliki RAR (*.rar)",
        )
        if fname:
            logger.info(f"Wybrano plik archiwum: {fname}")
            self.archive_path = fname
            self.archive_path_edit.setText(fname)
        else:
            logger.debug("Nie wybrano pliku archiwum.")

    def saveOutputFile(self):
        fname, _ = QFileDialog.getSaveFileName(
            self, "Zapisz plik .model", "", "Pliki .model (*.model)"
        )
        if fname:
            if not fname.lower().endswith(".model"):
                fname += ".model"
            logger.info(f"Wybrano plik wyjściowy .model: {fname}")
            self.output_path = fname
            self.output_path_edit.setText(fname)
        else:
            logger.debug("Nie wybrano pliku wyjściowego .model.")

    def createModelFile(self):
        logger.info("Rozpoczęto tworzenie pliku .model.")
        if not all(
            [self.preview_path, self.info_path, self.archive_path, self.output_path]
        ):
            logger.warning(
                "Nie wszystkie wymagane pliki zostały wybrane do utworzenia .model."
            )
            QMessageBox.critical(
                self,
                "Błąd",
                "Proszę wybrać wszystkie wymagane pliki (preview.jpg, info.json, archiwum) i plik wyjściowy.",
            )
            return

        start_time = time.time()
        self.status_label.setText("Tworzenie pliku .model...")
        self.time_label.setText("")

        try:
            # 1. Wczytaj wszystkie komponenty do pamięci
            with open(self.preview_path, "rb") as f_preview:
                preview_data = f_preview.read()
            preview_size = len(preview_data)
            logger.debug(f"Wczytano preview.jpg, rozmiar: {preview_size} bajtów.")

            with open(self.info_path, "rb") as f_info:
                info_data = f_info.read()
            info_size = len(info_data)
            logger.debug(f"Wczytano info.json, rozmiar: {info_size} bajtów.")
            try:
                json.loads(info_data.decode("utf-8"))
                logger.debug(
                    "info.json pomyślnie zdekodowane i sparsowane (wstępna weryfikacja)."
                )
            except Exception as e:
                logger.error(
                    f"Plik info.json ({self.info_path}) jest niepoprawny lub ma złe kodowanie: {e}",
                    exc_info=True,
                )
                QMessageBox.critical(
                    self, "Błąd", f"Plik info.json jest niepoprawny: {e}"
                )
                self.status_label.setText(f"Błąd: Plik info.json jest niepoprawny.")
                self.time_label.setText("")
                return

            with open(self.archive_path, "rb") as f_archive:
                archive_data = f_archive.read()
            archive_size = len(archive_data)
            archive_filename = os.path.basename(self.archive_path)
            logger.debug(
                f"Wczytano archiwum {archive_filename}, rozmiar: {archive_size} bajtów."
            )

            # 2. Przygotuj ostateczny indeks JSON i jego zakodowaną postać
            logger.debug("Przygotowywanie ostatecznego indeksu JSON...")

            # Początkowy offset dla danych po 2-bajtowym prefiksie długości i samym indeksie
            # Na tym etapie nie znamy jeszcze dokładnej długości indeksu JSON, więc użyjemy placeholderów
            # i zaktualizujemy po serializacji indeksu.

            # Iteracja w celu stabilizacji rozmiaru indeksu JSON
            # Długość prefiksu (2 bajty) jest stała.
            len_prefix_bytes = 2
            len_index_json_bytes = 0  # Początkowa estymacja

            for i in range(5):  # Ograniczenie do kilku iteracji dla bezpieczeństwa
                current_offset_after_header = len_prefix_bytes + len_index_json_bytes

                index_data_for_calc = {
                    "preview": {
                        "offset": current_offset_after_header,
                        "size": preview_size,
                    },
                }
                current_offset_for_data = current_offset_after_header + preview_size
                index_data_for_calc["info"] = {
                    "offset": current_offset_for_data,
                    "size": info_size,
                }
                current_offset_for_data += info_size
                index_data_for_calc["archive"] = {
                    "filename": archive_filename,
                    "offset": current_offset_for_data,
                    "size": archive_size,
                }

                # Użyj indent=None dla najbardziej kompaktowego JSONa, aby zminimalizować zmiany długości
                # lub indent=4 jeśli czytelność w pliku jest ważniejsza i akceptujesz większy nagłówek.
                # Dla spójności z poprzednimi logami, użyjemy indent=4.
                temp_final_index_json_bytes = json.dumps(
                    index_data_for_calc, indent=4
                ).encode("utf-8")
                new_len_index_json_bytes = len(temp_final_index_json_bytes)

                logger.debug(
                    f"Iteracja {i+1} stabilizacji indeksu: poprzedni rozmiar JSON = {len_index_json_bytes}, nowy rozmiar JSON = {new_len_index_json_bytes}"
                )

                if new_len_index_json_bytes == len_index_json_bytes:
                    logger.debug(
                        f"Rozmiar indeksu JSON ustabilizowany na {new_len_index_json_bytes} bajtów."
                    )
                    break
                len_index_json_bytes = new_len_index_json_bytes
            else:
                logger.error(
                    "Nie udało się ustabilizować rozmiaru indeksu JSON po kilku iteracjach."
                )
                raise AssertionError(
                    "Nie udało się ustabilizować rozmiaru indeksu JSON."
                )

            # Mamy ustabilizowany len_index_json_bytes, teraz tworzymy finalny indeks
            final_offset_preview = len_prefix_bytes + len_index_json_bytes
            final_offset_info = final_offset_preview + preview_size
            final_offset_archive = final_offset_info + info_size

            final_index_data = {
                "preview": {"offset": final_offset_preview, "size": preview_size},
                "info": {"offset": final_offset_info, "size": info_size},
                "archive": {
                    "filename": archive_filename,
                    "offset": final_offset_archive,
                    "size": archive_size,
                },
            }
            final_index_json_bytes = json.dumps(final_index_data, indent=4).encode(
                "utf-8"
            )

            # Sprawdzenie, czy po finalnym utworzeniu długość się nie zmieniła (nie powinna, jeśli indent jest stały)
            if len(final_index_json_bytes) != len_index_json_bytes:
                logger.error(
                    f"Niespójność! Ostateczny rozmiar indeksu JSON ({len(final_index_json_bytes)}) różni się od ustabilizowanego ({len_index_json_bytes})."
                )
                # Można by tu dodać ponowną próbę lub zgłosić błąd
                # Na razie zakładamy, że to się nie zdarzy przy stałym indent.
                len_index_json_bytes = len(
                    final_index_json_bytes
                )  # Użyj aktualnej długości

            logger.info(
                f"Ostateczny indeks JSON przygotowany (rozmiar: {len_index_json_bytes} bajtów)."
            )
            logger.debug(
                f"Ostateczny indeks JSON: {final_index_json_bytes.decode('utf-8', errors='replace')[:500]}..."
            )

            # 3. Przygotuj 2-bajtowy prefiks długości dla indeksu JSON
            # Używamy formatu '>H' (big-endian unsigned short)
            packed_index_len_bytes = struct.pack(">H", len_index_json_bytes)
            logger.debug(
                f"Przygotowano 2-bajtowy prefiks długości indeksu: {packed_index_len_bytes.hex()} (wartość: {len_index_json_bytes})."
            )

            # 4. Zapisz plik .model w poprawnej kolejności
            logger.debug(f"Rozpoczynanie zapisu do pliku: {self.output_path}")
            with open(self.output_path, "wb") as f_out:
                # a. Zapisz 2-bajtowy prefiks długości indeksu
                f_out.write(packed_index_len_bytes)
                logger.debug("Zapisano 2-bajtowy prefiks długości indeksu.")

                # b. Zapisz zakodowany indeks JSON
                f_out.write(final_index_json_bytes)
                logger.debug(f"Zapisano indeks JSON ({len_index_json_bytes} bajtów).")

                # c. Zapisz preview.jpg
                f_out.write(preview_data)
                logger.debug(f"Zapisano preview.jpg ({preview_size} bajtów).")

                # d. Zapisz info.json
                f_out.write(info_data)
                logger.debug(f"Zapisano info.json ({info_size} bajtów).")

                # e. Zapisz archiwum
                f_out.write(archive_data)
                logger.debug(
                    f"Zapisano archiwum {archive_filename} ({archive_size} bajtów)."
                )

            logger.info("Zakończono zapis wszystkich komponentów do pliku .model.")

            # 5. Weryfikacja zapisu (opcjonalna, ale zalecana)
            # Można tutaj dodać logikę odczytu i weryfikacji pliku,
            # podobną do tej w `verifyModelFile` lub `read_json_index_from_model_file`,
            # aby upewnić się, że plik został zapisany poprawnie.
            # Na przykład, odczytaj pierwsze 2 bajty, potem indeks, sprawdź offsety.
            try:
                logger.debug("Rozpoczęcie weryfikacji po zapisie...")
                # Użyjemy istniejącej funkcji read_json_index_from_model_file do weryfikacji
                # Należy ją dostosować, aby była metodą klasy lub przekazać 'self' jeśli to konieczne
                # Dla uproszczenia zakładamy, że jest dostępna jako funkcja statyczna/globalna
                # lub zaimportowana poprawnie.
                # Jeśli read_json_index_from_model_file jest metodą, to:
                # read_index = self.read_json_index_from_model_file(self.output_path)
                # Jeśli jest funkcją globalną:
                read_index = self.read_json_index_from_model_file(
                    self.output_path
                )  # ZMIANA TUTAJ

                if read_index:
                    logger.info(
                        f"WERYFIKACJA PO ZAPISIE: Pomyślnie odczytano indeks: {read_index}"
                    )
                    # Można dodać więcej asercji, np. porównanie z `final_index_data`
                    if read_index == final_index_data:
                        logger.info(
                            "WERYFIKACJA PO ZAPISIE: Odczytany indeks zgadza się z zapisanym."
                        )
                    else:
                        logger.warning(
                            "WERYFIKACJA PO ZAPISIE: Odczytany indeks RÓŻNI SIĘ od zapisanego."
                        )
                        logger.warning(f"Oczekiwano: {final_index_data}")
                        logger.warning(f"Odczytano: {read_index}")
                else:
                    logger.error(
                        "WERYFIKACJA PO ZAPISIE: Nie udało się odczytać indeksu z nowo utworzonego pliku."
                    )
                    # To jest krytyczny błąd, jeśli wystąpi
                    raise Exception(
                        "Weryfikacja po zapisie nie powiodła się: nie można odczytać indeksu."
                    )

            except Exception as e_verify_after_write:
                logger.error(
                    f"Błąd podczas weryfikacji pliku po zapisie: {e_verify_after_write}",
                    exc_info=True,
                )
                # Można zdecydować, czy to ma być błąd krytyczny dla użytkownika
                QMessageBox.warning(
                    self,
                    "Ostrzeżenie",
                    f"Wystąpił błąd podczas weryfikacji pliku po zapisie: {e_verify_after_write}. Plik mógł zostać utworzony, ale jego poprawność nie jest gwarantowana.",
                )
                # Nie przerywamy, plik został zapisany, ale z ostrzeżeniem.

            # Usunięto blok 'try...except' dotyczący iteracyjnej aktualizacji indeksu,
            # ponieważ indeks jest teraz finalizowany przed głównym zapisem.
            # Usunięto również kod weryfikacyjny, który był w tym bloku,
            # ponieważ nowa weryfikacja jest powyżej.

            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(
                f"Plik .model '{self.output_path}' utworzony pomyślnie w {elapsed_time:.4f} s."
            )
            self.status_label.setText("Plik .model utworzony pomyślnie!")
            self.time_label.setText(f"Czas utworzenia: {elapsed_time:.4f} s")
            QMessageBox.information(
                self,
                "Sukces",
                f"Plik '{self.output_path}' został utworzony pomyślnie.\\nCzas utworzenia: {elapsed_time:.4f} s",
            )

        except AssertionError as ae:
            logger.critical(
                f"Błąd krytyczny podczas przygotowywania indeksu: {ae}", exc_info=True
            )
            self.status_label.setText(f"Błąd krytyczny: {ae}")
            self.time_label.setText("")
            QMessageBox.critical(
                self,
                "Błąd krytyczny",
                f"Wystąpił błąd podczas przygotowywania indeksu pliku .model:\\n{ae}",
            )
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time if "start_time" in locals() else 0
            self.status_label.setText(f"Błąd podczas tworzenia: {e}")
            self.time_label.setText(
                f"Czas próby: {elapsed_time:.4f} s" if elapsed_time > 0 else ""
            )
            logger.error(
                f"Wystąpił błąd podczas tworzenia pliku .model '{self.output_path}': {e}",
                exc_info=True,
            )
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas tworzenia pliku .model:\\n{e}\\nCzas próby: {elapsed_time:.4f} s",
            )

    def verifyModelFile(self):
        model_file_to_verify = (
            self.output_path_edit.text()
        )  # Użyj ścieżki z pola edycji
        logger.info(
            f"Rozpoczęto weryfikację pliku .model: {model_file_to_verify if model_file_to_verify else 'Nie wybrano pliku'}"
        )
        if not model_file_to_verify:
            logger.debug(
                "Pole pliku .model do weryfikacji jest puste, otwieranie dialogu wyboru pliku."
            )
            model_file_to_verify, _ = QFileDialog.getOpenFileName(
                self, "Wybierz plik .model do weryfikacji", "", "Pliki .model (*.model)"
            )
            if not model_file_to_verify:
                logger.debug("Anulowano wybór pliku .model do weryfikacji.")
                return  # Użytkownik anulował
            logger.info(
                f"Wybrano plik .model do weryfikacji przez dialog: {model_file_to_verify}"
            )

        if not os.path.exists(model_file_to_verify):
            logger.error(
                f"Plik .model do weryfikacji '{model_file_to_verify}' nie istnieje."
            )
            QMessageBox.critical(
                self, "Błąd", f"Plik '{model_file_to_verify}' nie istnieje."
            )
            return

        start_time = time.time()
        self.status_label.setText("Weryfikacja pliku .model...")
        self.time_label.setText("")

        try:
            # Użyj ujednoliconej metody do odczytu indeksu
            index_data = self.read_json_index_from_model_file(model_file_to_verify)

            if not index_data:
                logger.error(
                    f"VERIFY: Nie udało się odczytać/sparsować indeksu JSON z pliku '{model_file_to_verify}' przy użyciu self.read_json_index_from_model_file."
                )
                self.status_label.setText(
                    "Weryfikacja nieudana: Nie udało się odczytać/sparsować indeksu JSON."
                )
                QMessageBox.critical(
                    self,
                    "Błąd",
                    f"Nie udało się odczytać/sparsować indeksu JSON z pliku '{model_file_to_verify}'. Plik może być uszkodzony lub mieć nieprawidłowy format.",
                )
                return

            logger.info(f"VERIFY: Pomyślnie odczytano indeks JSON: {index_data}")

            # Po odczytaniu indeksu, potrzebujemy długości samego bloku indeksu JSON,
            # aby poprawnie obliczyć/zweryfikować offsety, jeśli są one względem końca nagłówka.
            # Funkcja read_json_index_from_model_file zwraca tylko sparsowany słownik.
            # Musimy ponownie otworzyć plik, aby uzyskać długość nagłówka (prefix + JSON).
            # Alternatywnie, read_json_index_from_model_file mogłaby zwracać również tę długość.
            # Na razie, dla prostoty, odczytamy ją ponownie, ale to nie jest optymalne.

            # --- Początek bloku do uzyskania len_header_bytes ---
            len_header_bytes = 0
            with open(model_file_to_verify, "rb") as f_temp_len:
                packed_len = f_temp_len.read(2)
                if len(packed_len) < 2:
                    raise ValueError(
                        "Nie można odczytać długości nagłówka (za krótki plik)."
                    )
                actual_index_len = struct.unpack(">H", packed_len)[0]
                len_header_bytes = 2 + actual_index_len
            logger.debug(
                f"VERIFY: Obliczona długość nagłówka (prefix+JSON) to: {len_header_bytes}"
            )
            # --- Koniec bloku do uzyskania len_header_bytes ---

            # Sprawdzenie, czy odczytany indeks ma prawidłową strukturę i offsety
            # Offsety w zapisanym indeksie są absolutne, więc len_header_bytes nie jest tu bezpośrednio potrzebne
            # do walidacji wartości offsetów, ale jest dobre do zrozumienia struktury.

            # 2. Sprawdź, czy indeks zawiera wymagane klucze
            logger.debug("VERIFY: Weryfikacja struktury odczytanego indeksu JSON.")
            if not (
                all(k in index_data for k in ["preview", "info", "archive"])
                and all(k in index_data["preview"] for k in ["offset", "size"])
                and all(k in index_data["info"] for k in ["offset", "size"])
                and all(
                    k in index_data["archive"] for k in ["offset", "size", "filename"]
                )
            ):
                logger.error(
                    "VERIFY: Indeks JSON nie zawiera wszystkich wymaganych informacji lub ma niepoprawną strukturę."
                )
                self.status_label.setText(
                    "Weryfikacja nieudana: Indeks nie zawiera wszystkich wymaganych informacji lub ma niepoprawną strukturę."
                )
                QMessageBox.critical(
                    self,
                    "Błąd",
                    f"Indeks w pliku '{model_file_to_verify}' nie zawiera wszystkich wymaganych informacji lub ma niepoprawną strukturę.",
                )
                return

            # Otwieramy plik do odczytu danych binarnych na podstawie offsetów
            with open(model_file_to_verify, "rb") as f_in:
                # 3. Odczytaj preview.jpg
                preview_offset = index_data["preview"]["offset"]
                preview_size = index_data["preview"]["size"]
                logger.debug(
                    f"VERIFY: Odczytywanie preview.jpg: offset={preview_offset}, size={preview_size}"
                )
                f_in.seek(preview_offset)
                preview_data = f_in.read(preview_size)
                if len(preview_data) != preview_size:
                    logger.error(
                        f"VERIFY: Błąd odczytu preview.jpg: oczekiwano {preview_size}, odczytano {len(preview_data)}."
                    )
                    self.status_label.setText(
                        "Weryfikacja nieudana: Błąd podczas odczytu preview.jpg."
                    )
                    QMessageBox.critical(
                        self,
                        "Błąd",
                        f"Błąd podczas odczytu preview.jpg z pliku '{model_file_to_verify}'.",
                    )
                    return

                # 4. Odczytaj info.json
                info_offset = index_data["info"]["offset"]
                info_size = index_data["info"]["size"]
                logger.debug(
                    f"VERIFY: Odczytywanie info.json: offset={info_offset}, size={info_size}"
                )
                f_in.seek(info_offset)
                info_data_bytes = f_in.read(info_size)
                if len(info_data_bytes) != info_size:
                    logger.error(
                        f"VERIFY: Błąd odczytu info.json: oczekiwano {info_size}, odczytano {len(info_data_bytes)}."
                    )
                    self.status_label.setText(
                        "Weryfikacja nieudana: Błąd podczas odczytu danych dla info.json."
                    )
                    QMessageBox.critical(
                        self,
                        "Błąd",
                        f"Błąd podczas odczytu danych dla info.json z pliku '{model_file_to_verify}'. Oczekiwano {info_size} bajtów, odczytano {len(info_data_bytes)}.",
                    )
                    return

                verified_info_json = self._verify_and_extract_info_json(
                    info_data_bytes, model_file_to_verify
                )
                if not verified_info_json:
                    return

                # 5. Odczytaj archiwum (częściowa weryfikacja)
                archive_filename = index_data["archive"]["filename"]
                archive_offset = index_data["archive"]["offset"]
                archive_size = index_data["archive"]["size"]
                logger.debug(
                    f"VERIFY: Odczytywanie archiwum '{archive_filename}': offset={archive_offset}, size={archive_size}"
                )
                f_in.seek(archive_offset)
                archive_data = f_in.read(archive_size)
                if len(archive_data) != archive_size:
                    logger.error(
                        f"VERIFY: Błąd odczytu archiwum '{archive_filename}': oczekiwano {archive_size}, odczytano {len(archive_data)}."
                    )
                    self.status_label.setText(
                        f"Weryfikacja nieudana: Błąd podczas odczytu pliku archiwum {archive_filename}."
                    )
                    QMessageBox.critical(
                        self,
                        "Błąd",
                        f"Błąd podczas odczytu pliku archiwum '{archive_filename}' z pliku '{model_file_to_verify}'.",
                    )
                    return

                # Opcjonalnie: Spróbuj otworzyć archiwum w pamięci jako ZIP/RAR
                try:
                    import io

                    archive_buffer = io.BytesIO(archive_data)
                    logger.debug(
                        f"VERIFY: Próba weryfikacji archiwum '{archive_filename}' jako ZIP."
                    )
                    with zipfile.ZipFile(archive_buffer, "r") as temp_zip:
                        temp_zip.namelist()
                        logger.debug(
                            f"VERIFY: Archiwum '{archive_filename}' pomyślnie zweryfikowane jako ZIP."
                        )
                except zipfile.BadZipFile:
                    logger.warning(
                        f"VERIFY: Archiwum '{archive_filename}' nie jest prawidłowym plikiem ZIP. Próba jako RAR."
                    )
                    try:
                        archive_buffer.seek(0)  # Wróć na początek bufora dla RAR
                        logger.debug(
                            f"VERIFY: Próba weryfikacji archiwum '{archive_filename}' jako RAR."
                        )
                        with rarfile.RarFile(archive_buffer, "r") as temp_rar:
                            temp_rar.namelist()
                            logger.debug(
                                f"VERIFY: Archiwum '{archive_filename}' pomyślnie zweryfikowane jako RAR."
                            )
                    except rarfile.NotRarFile:
                        logger.error(
                            f"VERIFY: Plik archiwum '{archive_filename}' nie jest prawidłowym ZIP ani RAR.",
                            exc_info=True,
                        )
                        self.status_label.setText(
                            f"Weryfikacja nieudana: Plik archiwum '{archive_filename}' nie jest prawidłowym ZIP ani RAR."
                        )
                        QMessageBox.critical(
                            self,
                            "Błąd",
                            f"Plik archiwum '{archive_filename}' w pliku '{model_file_to_verify}' nie jest prawidłowym ZIP ani RAR.",
                        )
                        return
                    except Exception as e:
                        logger.error(
                            f"Błąd podczas otwierania archiwum RAR '{archive_filename}': {e}",
                            exc_info=True,
                        )
                        self.status_label.setText(
                            f"Weryfikacja nieudana: Błąd podczas otwierania archiwum RAR {archive_filename}: {e}"
                        )
                        QMessageBox.critical(
                            self,
                            "Błąd",
                            f"Wystąpił błąd podczas weryfikacji archiwum RAR '{archive_filename}':\n{e}",
                        )
                        return
                except Exception as e:
                    logger.error(
                        f"Błąd podczas otwierania archiwum ZIP '{archive_filename}': {e}",
                        exc_info=True,
                    )
                    self.status_label.setText(
                        f"Weryfikacja nieudana: Błąd podczas otwierania archiwum ZIP {archive_filename}: {e}"
                    )
                    QMessageBox.critical(
                        self,
                        "Błąd",
                        f"Wystąpił błąd podczas weryfikacji archiwum ZIP '{archive_filename}':\n{e}",
                    )
                    return

                end_time = time.time()
                elapsed_time = end_time - start_time

                # Odczyt danych z zweryfikowanego info.json
                model_name = verified_info_json.get("nazwa_modelu", "Nieznana nazwa")
                model_version = verified_info_json.get("wersja", "Nieznana wersja")

                success_message = (
                    f"Plik '{model_file_to_verify}' został zweryfikowany pomyślnie.\\n"
                    f"Zawiera preview.jpg, info.json i plik archiwum '{archive_filename}'.\\n\\n"
                    f"Informacje o modelu:\\n"
                    f"  Nazwa: {model_name}\\n"
                    f"  Wersja: {model_version}\\n\\n"
                    f"Czas weryfikacji: {elapsed_time:.4f} s"
                )
                logger.info(
                    f"Weryfikacja pliku .model '{model_file_to_verify}' zakończona pomyślnie w {elapsed_time:.4f} s."
                )
                self.status_label.setText(
                    "Weryfikacja pliku .model zakończona pomyślnie!"
                )
                self.time_label.setText(f"Czas weryfikacji: {elapsed_time:.4f} s")
                QMessageBox.information(
                    self,
                    "Sukces",
                    success_message,
                )

        except ValueError as ve:  # Dla błędów parsowania indeksu lub struktury
            logger.error(
                f"Błąd weryfikacji pliku .model '{model_file_to_verify}': {ve}",
                exc_info=True,
            )
            self.status_label.setText(f"Weryfikacja nieudana: {ve}")
            self.time_label.setText("")
            QMessageBox.critical(
                self,
                "Błąd weryfikacji",
                f"Plik .model ('{model_file_to_verify}') jest nieprawidłowy: {ve}",
            )
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time if "start_time" in locals() else 0
            self.status_label.setText(f"Weryfikacja nieudana: Błąd: {e}")
            self.time_label.setText(
                f"Czas próby: {elapsed_time:.4f} s" if elapsed_time > 0 else ""
            )
            logger.error(
                f"Nieoczekiwany błąd podczas weryfikacji pliku .model '{model_file_to_verify}': {e}",
                exc_info=True,
            )
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił nieoczekiwany błąd podczas weryfikacji pliku .model ('{model_file_to_verify}'):\\n{e}\\nCzas próby: {elapsed_time:.4f} s",
            )

    def loadAndDisplayInfoFromModel(self):
        model_path = self.output_path_edit.text()
        logger.info(
            f"Rozpoczęto wczytywanie info.json z pliku .model: {model_path if model_path else 'Nie wybrano pliku'}"
        )
        if not model_path:  # Jeśli pole jest puste, poproś o wybór pliku
            logger.debug(
                "Pole pliku .model do wczytania jest puste, otwieranie dialogu wyboru pliku."
            )
            model_path, _ = QFileDialog.getOpenFileName(
                self, "Wybierz plik .model do wczytania", "", "Pliki .model (*.model)"
            )
            if not model_path:
                logger.debug("Anulowano wybór pliku .model do wczytania.")
                return  # Użytkownik anulował
            logger.info(f"Wybrano plik .model do wczytania przez dialog: {model_path}")

        if not os.path.exists(model_path):
            logger.error(f"Plik .model do wczytania '{model_path}' nie istnieje.")
            QMessageBox.critical(self, "Błąd", f"Plik '{model_path}' nie istnieje.")
            return

        self.status_label.setText(
            f"Wczytywanie danych z {os.path.basename(model_path)}..."
        )
        self.time_label.setText("")
        start_time = time.time()

        try:
            # Użyj ujednoliconej metody do odczytu indeksu
            index_data = self.read_json_index_from_model_file(model_path)

            if not index_data:
                logger.error(
                    f"LOAD_INFO: Nie udało się odczytać/sparsować indeksu JSON z pliku '{model_path}' przy użyciu self.read_json_index_from_model_file."
                )
                raise ValueError(
                    "Nie udało się odczytać/sparsować indeksu JSON z początku pliku."
                )

            logger.info(f"LOAD_INFO: Pomyślnie odczytano indeks JSON: {index_data}")

            # Sprawdź podstawową strukturę indeksu
            logger.debug("LOAD_INFO: Weryfikacja struktury odczytanego indeksu JSON.")
            if not (
                all(k in index_data for k in ["preview", "info", "archive"])
                and all(k_comp in index_data["info"] for k_comp in ["offset", "size"])
            ):
                logger.error(
                    "LOAD_INFO: Indeks JSON nie zawiera wymaganych informacji o sekcji 'info' lub ma niepoprawną strukturę."
                )
                raise ValueError(
                    "Indeks nie zawiera wymaganych informacji o sekcji 'info' lub ma niepoprawną strukturę."
                )

            # Otwieramy plik do odczytu danych binarnych na podstawie offsetów
            with open(model_path, "rb") as f_in:
                # 2. Wyodrębnij dane info.json na podstawie indeksu
                info_offset = index_data["info"]["offset"]
                info_size = index_data["info"]["size"]
                logger.debug(
                    f"LOAD_INFO: Odczytywanie danych info.json: offset={info_offset}, size={info_size}."
                )

                f_in.seek(info_offset)
                info_data_bytes = f_in.read(info_size)

                if len(info_data_bytes) != info_size:
                    logger.error(
                        f"LOAD_INFO: Błąd odczytu sekcji info.json: oczekiwano {info_size}, odczytano {len(info_data_bytes)}."
                    )
                    raise ValueError(
                        f"Błąd odczytu sekcji info.json: oczekiwano {info_size} bajtów, odczytano {len(info_data_bytes)}."
                    )

                # 3. Zweryfikuj i sparsuj zawartość info.json
                logger.debug(
                    "LOAD_INFO: Rozpoczęcie weryfikacji i ekstrakcji wczytanych danych info.json."
                )
                verified_info_json = self._verify_and_extract_info_json(
                    info_data_bytes, model_path
                )

                if verified_info_json:
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    logger.info(
                        f"Dane info.json z '{model_path}' wczytane i zweryfikowane pomyślnie w {elapsed_time:.4f} s."
                    )
                    self.status_label.setText(
                        "Dane info.json wczytane i zweryfikowane pomyślnie."
                    )
                    self.time_label.setText(f"Czas wczytywania: {elapsed_time:.4f} s")

                    # Wyświetl zawartość info.json
                    pretty_info = json.dumps(
                        verified_info_json, indent=4, ensure_ascii=False
                    )

                    # Użyj QMessageBox do wyświetlenia, można dostosować rozmiar jeśli potrzeba
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle(
                        f"Zawartość info.json z {os.path.basename(model_path)}"
                    )
                    msg_box.setTextFormat(
                        Qt.TextFormat.PlainText
                    )  # Aby poprawnie wyświetlić formatowanie JSON
                    msg_box.setText(pretty_info)
                    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                    # msg_box.setStyleSheet("QTextEdit{min-width: 500px; min-height: 300px;}") # Opcjonalne stylowanie
                    msg_box.exec()

                    # Możesz zwrócić te dane lub zapisać w instancji klasy, jeśli potrzebne gdzie indziej
                    # self.loaded_model_info = verified_info_json
                    return verified_info_json
                else:
                    logger.warning(
                        f"Weryfikacja danych info.json z pliku '{model_path}' nie powiodła się."
                    )
                    # _verify_and_extract_info_json już wyświetlił błąd
                    self.status_label.setText(
                        "Weryfikacja danych info.json nie powiodła się."
                    )
                    self.time_label.setText(
                        ""  # Reset czasu, bo operacja nie zakończyła się pełnym sukcesem
                    )
                    return None

        except FileNotFoundError:
            logger.error(
                f"Plik .model '{model_path}' nie został znaleziony podczas próby wczytania info.",
                exc_info=True,
            )
            self.status_label.setText(
                f"Błąd: Plik '{model_path}' nie został znaleziony."
            )
            self.time_label.setText("")
            QMessageBox.critical(
                self, "Błąd", f"Plik '{model_path}' nie został znaleziony."
            )
        except (
            ValueError
        ) as ve:  # Dla błędów parsowania indeksu, struktury, odczytu sekcji
            logger.error(
                f"Błąd wczytywania pliku .model '{model_path}': {ve}", exc_info=True
            )
            self.status_label.setText(f"Błąd wczytywania pliku .model: {ve}")
            self.time_label.setText("")
            QMessageBox.critical(
                self,
                "Błąd wczytywania",
                f"Nie można wczytać pliku '{model_path}':\\n{ve}",
            )
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time if "start_time" in locals() else 0
            self.status_label.setText(f"Błąd podczas wczytywania: {e}")
            self.time_label.setText(
                f"Czas próby: {elapsed_time:.4f} s" if elapsed_time > 0 else ""
            )
            logger.error(
                f"Nieoczekiwany błąd podczas wczytania pliku .model '{model_path}': {e}",
                exc_info=True,
            )
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił nieoczekiwany błąd podczas wczytania pliku .model ('{model_path}'):\\n{e}",
            )

        logger.debug(
            "Zakończono próbę wczytania info.json, zwracanie None z powodu błędu."
        )
        return None

    def read_json_index_from_model_file(
        self,
        file_path,
    ):  # Jeśli to funkcja statyczna/globalna
        logging.info(
            f"READ_INDEX (metoda): Próba odczytu indeksu JSON z pliku: {file_path}"
        )
        try:
            with open(file_path, "rb") as f:
                # Zaloguj pierwsze kilkaset bajtów, aby zobaczyć, z czym mamy do czynienia
                f.seek(0)
                initial_bytes = f.read(512)  # Odczytaj fragment na potrzeby diagnostyki
                f.seek(0)  # Zresetuj wskaźnik pliku do początku

                if not initial_bytes:
                    logging.warning(
                        f"READ_INDEX: Plik {file_path} jest pusty lub nie udało się odczytać początkowych bajtów."
                    )
                else:
                    logging.info(
                        f"READ_INDEX: Pierwsze 512 bajtów pliku {file_path} (hex): {initial_bytes.hex()}"
                    )
                    try:
                        # Ostrożnie dekoduj dla celów logowania, unikając przerwania w razie błędów
                        decoded_initial_bytes = initial_bytes.decode(
                            "utf-8", errors="replace"
                        )
                        logging.info(
                            f"READ_INDEX: Pierwsze 512 bajtów pliku {file_path} (jako tekst, błędy zastąpione): {decoded_initial_bytes[:200]}..."
                        )  # Pokaż początek
                    except Exception as e_decode_log:
                        logging.error(
                            f"READ_INDEX: Błąd podczas dekodowania początkowych bajtów na potrzeby logowania: {e_decode_log}"
                        )

                # --- STRATEGIA 1: Odczyt na podstawie 2-bajtowego prefiksu długości ---
                logging.info(
                    "READ_INDEX: Strategia 1: Próba odczytu z 2-bajtowym prefiksem długości."
                )
                packed_index_len_bytes = f.read(2)

                if len(packed_index_len_bytes) < 2:
                    logging.error(
                        "READ_INDEX: Strategia 1: Nie udało się odczytać 2 bajtów na długość indeksu. Plik może być za krótki."
                    )
                    # Tutaj można by spróbować innej strategii, jeśli istnieje, lub zwrócić None
                    # Na razie zakładamy, że to główna strategia
                    return None

                logging.info(
                    f"READ_INDEX: Strategia 1: Odczytane bajty długości: {packed_index_len_bytes.hex()}"
                )

                try:
                    index_len = struct.unpack(">H", packed_index_len_bytes)[0]
                    logging.info(
                        f"READ_INDEX: Strategia 1: Rozpakowana długość indeksu: {index_len}"
                    )

                    if index_len == 0:
                        logging.warning(
                            "READ_INDEX: Strategia 1: Długość indeksu wynosi 0. Może to być problem lub pusty indeks."
                        )
                        # Można zwrócić pusty słownik lub None, w zależności od logiki aplikacji
                        # return {} # lub return None

                    # Sprawdzenie, czy index_len nie jest absurdalnie duży (np. > 1MB, co byłoby nietypowe dla indeksu)
                    MAX_EXPECTED_INDEX_LEN = 1 * 1024 * 1024  # 1MB
                    if index_len > MAX_EXPECTED_INDEX_LEN:
                        logging.error(
                            f"READ_INDEX: Strategia 1: Rozpakowana długość indeksu ({index_len}) jest podejrzanie duża."
                        )
                        return None  # Prawdopodobnie błąd odczytu długości

                    json_bytes = f.read(index_len)
                    logging.info(
                        f"READ_INDEX: Strategia 1: Odczytano {len(json_bytes)} bajtów na zawartość JSON (oczekiwano {index_len}). Hex: {json_bytes[:256].hex()}..."
                    )  # Loguj tylko część, jeśli długie

                    if len(json_bytes) < index_len:
                        logging.error(
                            f"READ_INDEX: Strategia 1: Oczekiwano {index_len} bajtów JSON, odczytano {len(json_bytes)}."
                        )
                        return None

                    json_str = ""
                    try:
                        json_str = json_bytes.decode("utf-8", errors="replace")
                        # Usuń ewentualne znaki NUL na końcu, które mogłyby powstać przez 'replace' i psuć parsowanie JSON
                        json_str = json_str.rstrip("\\x00").strip()
                        logging.info(
                            f"READ_INDEX: Strategia 1: Zdekodowany ciąg JSON (błędy zastąpione, oczyszczony): '{json_str}'"
                        )

                        if not json_str:
                            logging.error(
                                "READ_INDEX: Strategia 1: Zdekodowany ciąg JSON jest pusty po oczyszczeniu."
                            )
                            return None

                        index_dict = json.loads(json_str)
                        logging.info(
                            f"READ_INDEX: Strategia 1: Pomyślnie sparsowano indeks JSON: {index_dict}"
                        )
                        return index_dict
                    except json.JSONDecodeError as e_json:
                        logging.error(
                            f"READ_INDEX: Strategia 1: Błąd dekodowania JSON: {e_json}. Ciąg był: '{json_str}'"
                        )
                        logging.error(
                            f"READ_INDEX: Strategia 1: Szczegóły błędu JSON: msg={e_json.msg}, doc={e_json.doc}, pos={e_json.pos}, lineno={e_json.lineno}, colno={e_json.colno}"
                        )
                    except (
                        UnicodeDecodeError
                    ) as e_unicode:  # Teoretycznie obsłużone przez errors='replace'
                        logging.error(
                            f"READ_INDEX: Strategia 1: Błąd dekodowania Unicode: {e_unicode}. Bajty: {json_bytes.hex()}"
                        )
                    except Exception as e_s1_parse:
                        logging.error(
                            f"READ_INDEX: Strategia 1: Inny błąd podczas parsowania JSON: {e_s1_parse}. Ciąg był: '{json_str}'"
                        )

                except struct.error as e_struct:
                    logging.error(
                        f"READ_INDEX: Strategia 1: Błąd rozpakowania (struct.error): {e_struct}. Bajty długości: {packed_index_len_bytes.hex()}"
                    )
                except Exception as e_s1_outer:
                    logging.error(
                        f"READ_INDEX: Strategia 1: Ogólny błąd: {e_s1_outer}",
                        exc_info=True,
                    )

                # Jeśli dotarliśmy tutaj, strategia 1 zawiodła.
                # Można dodać logikę dla STRATEGII 2, jeśli istnieje w kodzie.
                # logging.info("READ_INDEX: Strategia 1 nie powiodła się, próba strategii 2 (jeśli zaimplementowana)...")
                # ... kod dla strategii 2 ...

                logging.error(
                    "READ_INDEX: Wszystkie strategie odczytu indeksu JSON zawiodły."
                )
                return None

        except FileNotFoundError:
            logging.error(f"READ_INDEX: Plik nie znaleziony: {file_path}")
        except Exception as e_open:
            logging.error(
                f"READ_INDEX: Ogólny błąd podczas otwierania/odczytu pliku {file_path}: {e_open}",
                exc_info=True,
            )

        return None  # Ostateczny zwrot None w przypadku niepowodzenia


if __name__ == "__main__":
    # Upewnij się, że konfiguracja loggingu jest wywoływana przed utworzeniem aplikacji,
    # jeśli chcesz logować również wczesne etapy inicjalizacji (choć tutaj jest już na poziomie modułu).
    logger.info("Uruchamianie aplikacji ModelCreator.")
    app = QApplication(sys.argv)
    window = ModelCreator()
    window.show()
    sys.exit(app.exec())
