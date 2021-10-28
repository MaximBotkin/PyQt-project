import sys
import PyQt5
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidgetItem
from PyQt5 import uic
import csv


class MyWidget(PyQt5.QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('uic.ui', self)
        self.setWindowTitle('Программа для учета финансов')
        self.setFixedSize(self.size())

        self.closed = False
        self.exit.clicked.connect(self.closeEvent_with_button)

        self.dictionary_of_expense = []

        self.payment_method.addItem('карта')
        self.payment_method.addItem('наличные')

        self.spending_date.showToday()

        csv_reader = Csv_reader(self.dictionary_of_expense)
        csv_reader.read_csv_table()
        LoadTable.loadTable(self)

        self.making_expense_btn.clicked.connect(self.expense_processing)
        self.making_income_btn.clicked.connect(self.income_processing)
        self.clear_history_btn.clicked.connect(self.clear_history)

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

    def closeEvent_with_button(self):
        reply = QMessageBox.question(self, 'Выход из программы', 'Вы действительно хотите закрыть программу?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.closed = True
            self.close()
        else:
            pass

    def expense_processing(self):
        date = self.spending_date.selectedDate().toString('dd-MM-yyyy')
        time = self.spending_time.time().toString('HH:mm')
        sum_of_expense = self.spending_sum.text()
        if sum_of_expense.isdigit():
            sum_of_expense = -int(self.spending_sum.text())
        else:
            print(type(sum_of_expense))
        value_of_expenses_sum = self.expenses_sum.value()
        self.expenses_sum.display(value_of_expenses_sum - sum_of_expense)
        method_of_payment = self.payment_method.currentText()
        expense_description = self.spending_description.toPlainText()
        writer = Csv_writer(date, sum_of_expense, self.dictionary_of_expense, expense_description,
                            time, method_of_payment)
        writer.write_table()
        LoadTable.loadTable(self)

    def income_processing(self):
        date = self.income_date.selectedDate().toString('dd-MM-yyyy')
        sum_of_income = self.sum_of_income.text()
        if sum_of_income.isdigit():
            sum_of_income = int(self.sum_of_income.text())
        else:
            print(type(sum_of_income))
        value_of_income_sum = self.income_sum.value()
        self.income_sum.display(value_of_income_sum + sum_of_income)
        expense_description = self.spending_description.toPlainText()
        writer = Csv_writer(date, sum_of_income, self.dictionary_of_expense, expense_description)
        writer.write_table()
        LoadTable.loadTable(self)

    def clear_history(self):
        self.income_sum.display(0)
        self.expenses_sum.display(0)
        self.dictionary_of_expense = []
        writer = Csv_writer('', '', self.dictionary_of_expense)
        writer.write_table()
        LoadTable.loadTable(self)


class Csv_reader:
    def __init__(self, dictionary_of_expense, name_of_file="transactions.csv"):
        self.name_of_file = name_of_file
        self.dictionary_of_expense = dictionary_of_expense

    def read_csv_table(self):
        with open("transactions.csv", encoding='utf-8', mode='r') as csv_file:
            reader = csv.DictReader(csv_file, delimiter=';', quotechar='"')
            for row in reader:
                self.dictionary_of_expense.append({'Дата и время(для расходов)': row['Дата и время(для расходов)'],
                                                   'Сумма': row['Сумма'],
                                                   'Метод оплаты(для расходов)': row['Метод оплаты(для расходов)'],
                                                   'Описание': row['Описание']})


class Csv_writer:
    def __init__(self, date, sum_of_expense, dictionary_of_expense, expense_description=None,
                 time=None, method_of_payment=None):
        self.date = date
        self.time = time
        self.sum_of_expense = sum_of_expense
        self.method_of_payment = method_of_payment
        self.expense_description = expense_description
        self.dictionary_of_expense = dictionary_of_expense

    def write_table(self):
        if self.date == '':
            self.dictionary_of_expense = [{'Дата и время(для расходов)': '',
                                           'Сумма': self.sum_of_expense,
                                           'Метод оплаты(для расходов)': self.method_of_payment,
                                           'Описание': self.expense_description}]
            with open("transactions.csv", encoding='utf-8', mode='w', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=list(self.dictionary_of_expense[0].keys()), delimiter=';',
                                        quotechar='"')
                writer.writeheader()
                for element in self.dictionary_of_expense:
                    writer.writerow(element)
        else:
            if len(self.dictionary_of_expense) > 1:
                if self.dictionary_of_expense[0]['Дата и время(для расходов)'] == '':
                    self.dictionary_of_expense = []
            self.dictionary_of_expense.append({'Дата и время(для расходов)': f'{self.date} {self.time}',
                                               'Сумма': self.sum_of_expense,
                                               'Метод оплаты(для расходов)': self.method_of_payment,
                                               'Описание': self.expense_description})
            with open("transactions.csv", encoding='utf-8', mode='w', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=list(self.dictionary_of_expense[0].keys()), delimiter=';',
                                        quotechar='"')
                writer.writeheader()
                for element in self.dictionary_of_expense:
                    writer.writerow(element)


class LoadTable:
    def __init__(self):
        self.transactions_table = None

    def loadTable(self):
        with open("transactions.csv", encoding='utf8') as csv_file:
            reader = csv.reader(csv_file, delimiter=';', quotechar='"')
            self.transactions_table.setColumnCount(4)
            self.transactions_table.setHorizontalHeaderLabels(['Дата и время(для расходов)', 'Сумма',
                                                               'Метод оплаты', 'Описание'])
            rows = 0
            reader = list(reader)[1:]
            for index, row in enumerate(reader):
                rows += 1
                self.transactions_table.setRowCount(rows)
                for num in range(4):
                    self.transactions_table.setItem(index, num, QTableWidgetItem(row[num]))
        csv_file.close()
        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec())
