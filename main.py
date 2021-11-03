import sys
import PyQt5
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtGui import QColor
import csv


# Основной класс с программой
class MyWidget(PyQt5.QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('uic.ui', self)
        self.setWindowTitle('Программа для учета финансов')
        self.setFixedSize(self.size())

        # Проверка не закрыл ли пользователь программу двумя способами
        self.closed = False
        # Обработка нажатия кнопки закрытия программы
        self.exit.clicked.connect(self.closeEvent_with_button)

        self.dictionary_of_expense = []

        # Добавление параметров в ComboBox метода оплаты
        self.payment_method.addItem('карта')
        self.payment_method.addItem('наличные')

        # Отображение сегодняшней даты
        self.spending_date.showToday()

        # Чтение csv файла с помощью класса Csv_reader и вывод таблицы в TableWidget
        csv_reader = Csv_reader(self.dictionary_of_expense)
        csv_reader.read_csv_table()
        LoadTable.loadTable(self)

        # Обработка нажатия остальных кнопок
        self.making_expense_btn.clicked.connect(self.expense_processing)
        self.making_income_btn.clicked.connect(self.income_processing)
        self.clear_history_btn.clicked.connect(self.clear_history)

    # Предупреждение перед закрытием программы
    def closeEvent(self, event):
        if self.closed is False:
            reply = QMessageBox.question(self, 'Выход из программы', 'Вы действительно хотите закрыть программу?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes and self.closed is False:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    # Предупреждение перед закрытием программы с помощью кнопки
    def closeEvent_with_button(self):
        reply = QMessageBox.question(self, 'Выход из программы', 'Вы действительно хотите закрыть программу?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.closed = True
            self.close()
        else:
            pass

    # Обработка кнопки "Внести расход"
    def expense_processing(self):
        # Чтение даты, времени, суммы, метода оплаты и описания
        date = self.spending_date.selectedDate().toString('dd-MM-yyyy')
        time = self.spending_time.time().toString('HH:mm')
        expense_description = self.spending_description.toPlainText()
        sum_of_expense = self.spending_sum.text()
        # Проверка правильности ввода данных
        try:
            sum_of_expense = -float(sum_of_expense)
            if sum_of_expense >= 0:
                raise Zero_error
            value_of_expenses_sum = self.expenses_sum.value()
            # Отображение общей суммы расходов на LCD Number
            self.expenses_sum.display(value_of_expenses_sum - sum_of_expense)
            method_of_payment = self.payment_method.currentText()
            # Запись данных в виде таблицы в csv файл с помощью класса Csv_writer
            writer = Csv_writer(date, sum_of_expense, self.dictionary_of_expense, expense_description,
                                time, method_of_payment)
            writer.write_table()
            # Вывод таблицы
            LoadTable.loadTable(self)
        # В случае ошибки вылезает QMessageBox.critical с описанием
        except ValueError:
            QMessageBox.critical(self, 'Ошибка!', 'Вы ввели не число', QMessageBox.Ok)
        except Zero_error:
            QMessageBox.critical(self, 'Ошибка!', 'Вы ввели число, меньшее или равное 0', QMessageBox.Ok)

    # Обработка кнопки "Внести расход"
    def income_processing(self):
        # Чтение даты, суммы и описания
        date = self.income_date.selectedDate().toString('dd-MM-yyyy')
        income_description = self.income_description.toPlainText()
        sum_of_income = self.sum_of_income.text()
        # Проверка правильности ввода данных
        try:
            sum_of_income = float(sum_of_income)
            if sum_of_income <= 0:
                raise Zero_error
            value_of_income_sum = self.income_sum.value()
            # Отображение общей суммы доходов на LCD Number
            self.income_sum.display(value_of_income_sum + sum_of_income)
            # Запись данных в виде таблицы в csv файл с помощью класса Csv_writer
            writer = Csv_writer(date, sum_of_income, self.dictionary_of_expense, income_description)
            writer.write_table()
            # Вывод таблицы
            LoadTable.loadTable(self)
        # В случае ошибки вылезает QMessageBox.critical с описанием
        except ValueError:
            QMessageBox.critical(self, 'Ошибка!', 'Вы ввели не число', QMessageBox.Ok)
        except Zero_error:
            QMessageBox.critical(self, 'Ошибка!', 'Вы ввели число, меньшее или равное 0', QMessageBox.Ok)

    # Функция окраски строки таблицы
    def color_row(self, row, color):
        for i in range(self.transactions_table.columnCount()):
            if self.transactions_table.item(row, i):
                self.transactions_table.item(row, i).setBackground(color)

    # Обработка кнопки "Очистить историю"
    def clear_history(self):
        # Отображение 0 на общих суммах и расходов, и доходов
        self.income_sum.display(0)
        self.expenses_sum.display(0)
        # Создание пустой таблицы
        self.dictionary_of_expense = []
        writer = Csv_writer('', '', self.dictionary_of_expense, '')
        writer.write_table()
        # Вывод таблицы
        LoadTable.loadTable(self)


# Класс ошибки, если пользователь ввел число, меньшее или равное 0
class Zero_error(Exception):
    pass


# Класс чтения csv файла
class Csv_reader:
    def __init__(self, dictionary_of_expense, name_of_file="transactions.csv"):
        self.name_of_file = name_of_file
        self.dictionary_of_expense = dictionary_of_expense

    def read_csv_table(self):
        # Запись данных в список dictionary_of_expense строчками таблицы в виде словарей
        with open(self.name_of_file, encoding='utf-8', mode='r') as csv_file:
            # Чтение с помощью DictReader
            reader = csv.DictReader(csv_file, delimiter=';', quotechar='"')
            for row in reader:
                self.dictionary_of_expense.append({'Дата и время(для расходов)': row['Дата и время(для расходов)'],
                                                   'Сумма': row['Сумма'],
                                                   'Метод оплаты(для расходов)': row['Метод оплаты(для расходов)'],
                                                   'Описание': row['Описание']})


# Класс записи в csv файл
class Csv_writer:
    # Передача всех данных в init
    def __init__(self, date, sum_of_expense, dictionary_of_expense, description,
                 time=None, method_of_payment=None):
        self.date = date
        self.time = time
        self.sum_of_expense = sum_of_expense
        self.method_of_payment = method_of_payment
        self.description = description
        self.dictionary_of_expense = dictionary_of_expense

    # Запись данных в виде таблицы в csv файл
    def write_table(self):
        if self.date == '':
            # Создание пустой таблицы, если была нажата кнопка "Очистить историю"
            self.dictionary_of_expense = [{'Дата и время(для расходов)': '',
                                           'Сумма': self.sum_of_expense,
                                           'Метод оплаты(для расходов)': self.method_of_payment,
                                           'Описание': self.description}]
            # Запись с помощью DictWriter
            with open("transactions.csv", encoding='utf-8', mode='w', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=list(self.dictionary_of_expense[0].keys()), delimiter=';',
                                        quotechar='"')
                writer.writeheader()
                for element in self.dictionary_of_expense:
                    writer.writerow(element)
        # При условии добавления новой транзакции в таблицу
        else:
            # Проверка первой строки таблицы
            if len(self.dictionary_of_expense) > 1:
                # Если она пустая, то создается новая таблица, удаляя эту строку
                if self.dictionary_of_expense[0]['Дата и время(для расходов)'] == '':
                    self.dictionary_of_expense = []
            # Проверка: если не передано время, значит это доход
            if self.time is None:
                # Добавление новой строки в таблицу в виде словаря
                self.dictionary_of_expense.append({'Дата и время(для расходов)': self.date,
                                                   'Сумма': self.sum_of_expense,
                                                   'Метод оплаты(для расходов)': self.method_of_payment,
                                                   'Описание': self.description})
            # Иначе - это расход
            else:
                self.dictionary_of_expense.append({'Дата и время(для расходов)': f'{self.date} {self.time}',
                                                   'Сумма': self.sum_of_expense,
                                                   'Метод оплаты(для расходов)': self.method_of_payment,
                                                   'Описание': self.description})
            # Запись с помощью DictWriter
            with open("transactions.csv", encoding='utf-8', mode='w', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=list(self.dictionary_of_expense[0].keys()), delimiter=';',
                                        quotechar='"')
                writer.writeheader()
                for element in self.dictionary_of_expense:
                    writer.writerow(element)


# Вывод таблицы
class LoadTable:
    def __init__(self):
        self.transactions_table = None

    def loadTable(self):
        # Чтение csv файла с помощью reader
        with open("transactions.csv", encoding='utf8') as csv_file:
            reader = csv.reader(csv_file, delimiter=';', quotechar='"')
            # Установка 4 столбца в таблицу
            self.transactions_table.setColumnCount(4)
            # Установка названия столбцов
            self.transactions_table.setHorizontalHeaderLabels(['Дата и время(для расходов)', 'Сумма',
                                                               'Метод оплаты', 'Описание'])
            rows = 0
            index_of_rows_expenses = []
            index_of_rows_income = []
            # Представление reader в виде списка
            reader = list(reader)[1:]
            for index, row in enumerate(reader):
                # Добавление новой строки
                rows += 1
                self.transactions_table.setRowCount(rows)
                if row != ['', '', '', '']:
                    if float(row[1]) < 0:
                        index_of_rows_expenses.append(index)
                    elif float(row[1]) > 0:
                        index_of_rows_income.append(index)
                for num in range(4):
                    # Запись новой строки
                    self.transactions_table.setItem(index, num, QTableWidgetItem(row[num]))

            # Закрытие csv файла
            csv_file.close()
            # Раскрашивание строки в зависимости расход это или доход
            for index in index_of_rows_expenses:
                # Функция из основного класса - color_row
                MyWidget.color_row(self, int(index), QColor(255, 99, 71))
            for index in index_of_rows_income:
                MyWidget.color_row(self, int(index), QColor(127, 255, 212))
            # Установка размера каждого столбца, чтобы заполнить доступное пространство
            header = self.transactions_table.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
            # В данном столбце размер регулируется по контенту
            header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)


# Запуск программы
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec())
