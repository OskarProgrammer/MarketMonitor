import sys
import os

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QGridLayout, QCheckBox, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon

from gettingData import getData

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, "..")

class MonitorGieldowy(QWidget):
    
    symbolsList = []
    
    def __init__(self):
        super().__init__()

        appIcon_path = os.path.join(project_root, "Icons", "appIcon.ico")
        appIcon = QIcon(appIcon_path)
        
        self._original_flags = self.windowFlags()

        self.setWindowIcon(appIcon)
        self.setWindowTitle("Market monitor")
        self.setGeometry(100, 100, 600, 400)
        self.setFixedSize(600, 400)

        self.createInterface()
        self._getSymbolsFromFile()
        
        self.timer = QTimer(self)
        self.timer.setInterval(15000)
        self.timer.timeout.connect(self._updatePrices)
        self.timer.start()

        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self._updateCountdown)
        self.countdown_timer.start()
        
        self.countdown_counter = self.timer.interval() // 1000
        self._updateCountdown()

        self._updatePrices()

    def _getSymbolsFromFile(self):
        try:
            symbols_file_path = os.path.join(project_root, "symbols.txt")
            with open(symbols_file_path, "r") as file:
                self.symbolsList = [
                    line.strip().split(" ", 1) for line in file.readlines()
                ]
        except FileNotFoundError:
            symbols_file_path = os.path.join(project_root, "symbols.txt")
            with open(symbols_file_path, "w") as file:
                pass
            print("File symbols.txt does not exist. Creating.")
        except ValueError:
            print("Error reading symbols file. Please check file format.")
            self.symbolsList = []

    def _getSymbolFromInput(self):
        try:
            input_text = self.symbolInput.text().strip().upper()
            if not input_text:
                print("Input is empty.")
                return

            if " " not in input_text:
                print("Please enter symbol and alias (e.g., CDR.WA CDProjekt)")
                return
            
            symbol, alias = input_text.split(" ", 1)

            if symbol in [s[0] for s in self.symbolsList]:
                print(f"Symbol {symbol} already exists.")
                return
            
            print(f"Checking if symbol {symbol} is valid...")
            data = getData(symbol)

            if data and data.get('currentPrice') is not None:
                self.symbolsList.append([symbol, alias])
                try:
                    symbols_file_path = os.path.join(project_root, "symbols.txt")
                    with open(symbols_file_path, "a") as file:
                        file.write(f"{symbol} {alias}\n")
                    print(f"Symbol {symbol} added successfully.")
                except Exception as e:
                    print(f"Error during writing to file: {e}")
                
                self.symbolInput.clear()
                self._updatePrices()
            else:
                print(f"Symbol {symbol} does not exist or no data available.")
        except ValueError:
            print("Please enter symbol and alias (e.g., CDR.WA CDProjekt)")

    def _removeSymbol(self, symbol_to_remove):
        self.symbolsList = [s for s in self.symbolsList if s[0] != symbol_to_remove]
        self._saveSymbolsToFile()
        self._updatePrices()

    def _saveSymbolsToFile(self):
        try:
            symbols_file_path = os.path.join(project_root, "symbols.txt")
            with open(symbols_file_path, "w") as file:
                for symbol, alias in self.symbolsList:
                    file.write(f"{symbol} {alias}\n")
        except Exception as e:
            print(f"Error during writing to file: {e}")


    def _toggleAlwaysOnTop(self, checked):
        if checked:
            self.setWindowFlags(self._original_flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self._original_flags)
        
        self.show()

    def _updateCountdown(self):
        self.countdown_counter -= 1
        if self.countdown_counter < 0:
            self.countdown_counter = 0
            
        self.setWindowTitle(f"Market monitor | Refresh in {self.countdown_counter}s")

    def _updatePrices(self):
        
        self.countdown_counter = self.timer.interval() // 1000
        
        for i in reversed(range(self.symbolsLayout.count())):
            widget = self.symbolsLayout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not self.symbolsList:
            self.symbolsLayout.addWidget(QLabel("No symbols to display."), 0, 0, 1, 1, Qt.AlignmentFlag.AlignCenter)
            return
            
        row = 0
        for symbol, alias in self.symbolsList:
            data = getData(symbol)

            item_layout = QHBoxLayout()
            
            label = QLabel()
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 16pt; font-weight: bold;")
            
            if data and data.get('currentPrice') is not None:
                diff = data['currentPrice'] - data['lastClose']
                percent = ((data['currentPrice'] / data["lastClose"]) * 100 - 100)
                
                label_text = f"<b>{alias}({symbol})</b>: {data['currentPrice']} {data.get('currency', 'no data')} | {diff:.2f} | {percent:.2f} %"
                label.setText(label_text)
                
                if data['lastClose'] is not None:
                    if data['lastClose'] < data['currentPrice']:
                        label.setStyleSheet("font-size: 12pt; font-weight: bold; color: green;")
                    elif data['lastClose'] == data['currentPrice']:
                        label.setStyleSheet("font-size: 12pt; font-weight: bold; color: gray;")
                    else:
                        label.setStyleSheet("font-size: 12pt; font-weight: bold; color: red;")
                else:
                    label.setStyleSheet("font-size: 12pt; font-weight: bold; color: gray;")
            else:
                label.setText(f"<b>{alias}({symbol})</b>: No data")
                label.setStyleSheet("font-size: 12pt; font-weight: bold; color: gray;")

            item_layout.addWidget(label, 1)

            remove_button = QPushButton("Remove")
            remove_button.setFixedSize(60, 25)
            remove_button.clicked.connect(lambda _, s=symbol: self._removeSymbol(s))
            item_layout.addWidget(remove_button)

            container_widget = QWidget()
            container_widget.setLayout(item_layout)
            self.symbolsLayout.addWidget(container_widget, row, 0, 1, 1, Qt.AlignmentFlag.AlignTop)
            row += 1
            
        self.symbolsLayout.setSpacing(10)

    def createInterface(self):
        mainLayout = QVBoxLayout()
        mainLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inputLayout = QVBoxLayout()
        self.symbolInput = QLineEdit()
        inputLayout.addWidget(self.symbolInput)
        
        self.button = QPushButton("Add symbol")
        self.button.clicked.connect(self._getSymbolFromInput)
        inputLayout.addWidget(self.button)

        self.alwaysOnTop_checkbox = QCheckBox("Always on top")
        self.alwaysOnTop_checkbox.toggled.connect(self._toggleAlwaysOnTop)
        inputLayout.addWidget(self.alwaysOnTop_checkbox)

        mainLayout.addLayout(inputLayout)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        
        self.symbolsLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.symbolsLayout.setSpacing(20)
        
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        
        mainLayout.addWidget(self.scrollArea)
        self.setLayout(mainLayout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    okno = MonitorGieldowy()
    okno.show()
    sys.exit(app.exec())