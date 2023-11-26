import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QDateEdit, QFormLayout, QMessageBox, QTabWidget
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QFile, QTextStream
import sqlite3
import os

class FinanceTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Трекер шекелей от Кианы')

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.tab_widget = QTabWidget(self)

        self.tab_load = QWidget(self)
        self.layout_load = QVBoxLayout()

        self.form_layout = QFormLayout()

        self.amount_label = QLabel('Сколько денег:')
        self.amount_input = QLineEdit(self)
        self.amount_input.setValidator(QtGui.QDoubleValidator())

        self.category_label = QLabel('Категории:')
        self.category_input = QComboBox(self)
        self.category_input.addItems(['Зарплата', 'Фриланс', 'Продукты', 'Транспорт', 'Жилье', 'Развлечения', 'Другое'])

        self.type_label = QLabel('Тип:')
        self.type_input = QComboBox(self)
        self.type_input.addItems(['Доход', 'Расход'])

        self.date_label = QLabel('Дата:')
        self.date_input = QDateEdit(self)
        self.date_input.setDate(QtCore.QDate.currentDate())

        self.description_label = QLabel('Описание:')
        self.description_input = QLineEdit(self)

        self.form_layout.addRow(self.amount_label, self.amount_input)
        self.form_layout.addRow(self.category_label, self.category_input)
        self.form_layout.addRow(self.type_label, self.type_input)
        self.form_layout.addRow(self.date_label, self.date_input)
        self.form_layout.addRow(self.description_label, self.description_input)

        self.add_button = QPushButton('Добавить транзакцию', self)
        self.add_button.clicked.connect(self.add_transaction)

        self.show_all_button = QPushButton('Показать все операции', self)
        self.show_all_button.clicked.connect(self.show_all_transactions)
        self.show_all_button.setEnabled(False)

        self.delete_selected_button = QPushButton('Удалить выделенные', self)
        self.delete_selected_button.clicked.connect(self.delete_selected_transactions)

        self.transactions_display = QTableWidget(self)
        self.transactions_display.setColumnCount(6)
        self.transactions_display.setHorizontalHeaderLabels(['ID', 'Amount', 'Category', 'Type', 'Date', 'Description'])
        self.transactions_display.setSelectionMode(QAbstractItemView.MultiSelection)

        self.layout_load.addLayout(self.form_layout)
        self.layout_load.addWidget(self.add_button)
        self.layout_load.addWidget(self.show_all_button)
        self.layout_load.addWidget(self.delete_selected_button)
        self.layout_load.addWidget(self.transactions_display)

        self.tab_load.setLayout(self.layout_load)

        self.tab_widget.addTab(self.tab_load, 'Загрузка данных')

        self.layout.addWidget(self.tab_widget)

        self.central_widget.setLayout(self.layout)

        self.create_db()
        self.load_data()

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'res/icon.ico')

        self.setWindowIcon(QIcon(icon_path))

    def delete_selected_transactions(self):
        try:
            selected_rows = self.transactions_display.selectionModel().selectedRows()

            if not selected_rows:
                QMessageBox.warning(self, 'Предупреждение', 'Выберите транзакции для удаления.')
                return

            ids_to_delete = [self.transactions_display.item(row.row(), 0).text() for row in selected_rows]

            conn = sqlite3.connect('finances.db')
            c = conn.cursor()
            for transaction_id in ids_to_delete:
                c.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
            conn.commit()
            conn.close()

            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при удалении транзакций: {str(e)}')

    def show_all_transactions(self):
        conn = sqlite3.connect('finances.db')
        c = conn.cursor()
        c.execute('SELECT id, amount, category, type, date, description FROM transactions')
        rows = c.fetchall()
        conn.close()

        self.transactions_display.setRowCount(0)

        for row_number, row_data in enumerate(rows):
            self.transactions_display.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.transactions_display.setItem(row_number, column_number, QTableWidgetItem(str(data)))

    def add_transaction(self):
        amount_text = self.amount_input.text()
        category = self.category_input.currentText()
        transaction_type = 'Доход' if self.type_input.currentText() == 'Доход' else 'Расход'
        date = self.date_input.date().toString('yyyy-MM-dd')
        description = self.description_input.text()

        if not amount_text or amount_text == '0':
            QMessageBox.warning(self, 'Ошибка', 'Введите корректную сумму транзакции (больше 0).')
            return

        amount = float(amount_text.replace(',', '.'))

        conn = sqlite3.connect('finances.db')
        c = conn.cursor()
        c.execute('INSERT INTO transactions (amount, category, type, date, description) VALUES (?, ?, ?, ?, ?)',
                  (amount, category, transaction_type, date, description))
        conn.commit()
        conn.close()

        self.load_data()

    def create_db(self):
        conn = sqlite3.connect('finances.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL,
                category TEXT,
                type TEXT,
                date TEXT,
                description TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def load_data(self):
        conn = sqlite3.connect('finances.db')
        c = conn.cursor()
        c.execute('SELECT id, amount, category, type, date, description FROM transactions')
        rows = c.fetchall()
        conn.close()

        self.finances = {
            'transactions': [{'id': row[0], 'amount': row[1], 'category': row[2], 'type': row[3], 'date': row[4], 'description': row[5]} for row in rows]
        }

        total_income = sum(item['amount'] for item in self.finances['transactions'] if item['type'] == 'Доход')
        total_expenses = sum(item['amount'] for item in self.finances['transactions'] if item['type'] == 'Расход')

        self.amount_input.clear()
        self.category_input.setCurrentIndex(0)
        self.type_input.setCurrentIndex(0)
        self.date_input.setDate(QtCore.QDate.currentDate())
        self.description_input.clear()

        self.show_all_button.setEnabled(True)

        self.setFixedSize(660, 600)

    def load_style_from_file(self, file_path):
        style_file = QFile(file_path)
        if style_file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(style_file)
            self.setStyleSheet(stream.readAll())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = FinanceTrackerApp()
    mainWin.show()
    sys.exit(app.exec_())