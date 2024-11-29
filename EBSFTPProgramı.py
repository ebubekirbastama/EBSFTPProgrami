import os
import xml.etree.ElementTree as ET
from ftplib import FTP
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QWidget, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import base64


class FTPClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FTP Bağlantısı ve Dosya İndirme")
        self.setGeometry(100, 100, 700, 500)

        self.ftp = None  # FTP bağlantısı için değişken
        self.current_dir = '/'  # Başlangıçta kök dizini

        # Ana widget ve layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout()

        # Sunucu Adresi
        self.server_label = QLabel("Sunucu Adresi:")
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("ftp.example.com")

        # Kullanıcı Adı
        self.username_label = QLabel("Kullanıcı Adı:")
        self.username_input = QLineEdit()

        # Parola
        self.password_label = QLabel("Parola:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Bağlantı Noktası
        self.port_label = QLabel("Bağlantı Noktası:")
        self.port_input = QLineEdit()
        self.port_input.setText("21")  # Default port

        # Bağlan Butonu
        self.connect_button = QPushButton("Bağlan")
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        self.connect_button.clicked.connect(self.connect_to_ftp)

        # FTP Dosya Listesi
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.file_list.itemClicked.connect(self.change_directory)  # Tek tıklama ile klasör değişimi

        # İndir Butonu
        self.download_button = QPushButton("Seçili Dosyayı İndir")
        self.download_button.setStyleSheet("background-color: #2196F3; color: white; font-size: 14px;")
        self.download_button.clicked.connect(self.download_file)
        self.download_button.setEnabled(False)  # Başlangıçta devre dışı

        # Layout Düzeni
        self.layout.addWidget(self.server_label)
        self.layout.addWidget(self.server_input)
        self.layout.addWidget(self.username_label)
        self.layout.addWidget(self.username_input)
        self.layout.addWidget(self.password_label)
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(self.port_label)
        self.layout.addWidget(self.port_input)
        self.layout.addWidget(self.connect_button)
        self.layout.addWidget(self.file_list)
        self.layout.addWidget(self.download_button)

        self.main_widget.setLayout(self.layout)

        # XML dosyasından bilgileri yükle
        self.load_filezilla_profile()

    def load_filezilla_profile(self):
        """XML dosyasından FTP profil bilgilerini okur ve inputlara doldurur."""
        config_path = os.path.expanduser("~/.config/filezilla/recentservers.xml")  # Linux/Mac
        if not os.path.exists(config_path):  # Windows için varsayılan yolu kontrol edin
            config_path = os.path.expanduser("~\\AppData\\Roaming\\FileZilla\\recentservers.xml")

        if not os.path.exists(config_path):
            QMessageBox.warning(self, "FileZilla Config Bulunamadı", "FileZilla config dosyası bulunamadı.")
            return

        try:
            tree = ET.parse(config_path)
            root = tree.getroot()

            # İlk sunucu bilgilerini al
            server = root.find(".//Server")
            if server is not None:
                host = server.find("Host").text
                port = server.find("Port").text
                user = server.find("User").text
                encoded_pass = server.find("Pass").text

                # Şifreyi base64'ten çözme
                decoded_pass = base64.b64decode(encoded_pass).decode('utf-8') if encoded_pass else ""

                # Inputlara verileri yükle
                self.server_input.setText(host if host else "")
                self.port_input.setText(port if port else "21")
                self.username_input.setText(user if user else "")
                self.password_input.setText(decoded_pass if decoded_pass else "")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"FileZilla config dosyası okunurken hata oluştu: {e}")

    def connect_to_ftp(self):
        """FTP'ye bağlanır ve dosya listesini çeker."""
        server = self.server_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        port = int(self.port_input.text())

        try:
            self.ftp = FTP()
            self.ftp.connect(server, port)
            self.ftp.login(user=username, passwd=password)
            self.file_list.clear()
            self.list_files(self.current_dir)
            self.download_button.setEnabled(True)
            QMessageBox.information(self, "Bağlantı Başarılı", "FTP sunucusuna başarıyla bağlanıldı.")
        except Exception as e:
            QMessageBox.critical(self, "Bağlantı Hatası", f"Bağlantı başarısız oldu: {e}")

    def list_files(self, directory):
        """FTP sunucusundaki dosya ve klasörleri listeler ve uygun simgelerle ekler."""
        self.current_dir = directory
        try:
            items = self.ftp.mlsd(directory)
            for name, facts in items:
                item = None
                if facts["type"] == "file":
                    item = QListWidgetItem(name)
                    item.setIcon(QIcon("file_icon.png"))  # Dosya simgesi
                elif facts["type"] == "dir":
                    item = QListWidgetItem(name)
                    item.setIcon(QIcon("folder_icon.png"))  # Klasör simgesi
                if item:
                    self.file_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Dosya Listeleme Hatası", f"Dosya listesi alınırken hata oluştu: {e}")

    def change_directory(self, item):
        """Klasöre tıklanıldığında, içeriğini listele."""
        if item.icon().name() == "folder_icon.png":
            self.list_files(item.text())

    def download_file(self):
        """Seçilen dosyayı indirir."""
        selected_item = self.file_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Dosya Seçilmedi", "Lütfen indirilecek bir dosya seçin.")
            return
    
        file_name = selected_item.text()

        # Klasör mü dosya mı olduğuna bakılır
        if selected_item.icon().name() == "folder_icon.png":
            self.download_directory(file_name)  # Klasör indirilecektir
        else:
            self.download_single_file(file_name)  # Tek dosya indirilecektir
    
    def download_single_file(self, file_name):
        """Tek bir dosyayı indirir."""
        save_path, _ = QFileDialog.getSaveFileName(self, "Dosyayı Kaydet", file_name)
        if save_path:
            try:
                with open(save_path, "wb") as f:
                    self.ftp.retrbinary(f"RETR {file_name}", f.write)
                QMessageBox.information(self, "İndirme Tamamlandı", f"{file_name} başarıyla indirildi.")
            except Exception as e:
                QMessageBox.critical(self, "İndirme Hatası", f"Dosya indirilemedi: {e}")

    def download_directory(self, dir_name):
        """Bir klasörü indirir."""
        items = self.ftp.mlsd(dir_name)
        for name, facts in items:
            if facts["type"] == "file":
                self.download_single_file(name)  # Dosyaları indir
            elif facts["type"] == "dir":
                self.download_directory(name)  # Alt klasörlere gir ve indir

    def is_regular_file(self, file_name):
        """Dosyanın geçerli bir dosya olup olmadığını kontrol eder."""
        try:
            # FTP sunucusunda dosyanın tipini kontrol et
            items = self.ftp.mlsd(self.current_dir)
            for name, facts in items:
                if name == file_name and facts["type"] == "file":
                    return True
            return False
        except Exception as e:
            return False


if __name__ == "__main__":
    app = QApplication([])
    ftp_client = FTPClient()
    ftp_client.show()
    app.exec()
