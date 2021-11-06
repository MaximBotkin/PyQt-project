import sqlite3
import sys
import PyQt5
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtGui import QColor
import hashlib


# Основной класс
class MyWidget(PyQt5.QtWidgets.QMainWindow):
    def __init__(self, user_id, expenses_sum=0, income_sum=0):
        super().__init__()
        self.pass_dialog = Login_window()
        uic.loadUi('uic.ui', self)
        self.setWindowTitle('Программа для учета финансов')
        self.setFixedSize(self.size())

        # Проверка не закрыл ли пользователь программу
        self.closed = False
        # Обработка нажатия кнопки выхода из аккаунта
        self.exit.clicked.connect(self.quit_with_button)

        # Добавление параметров в ComboBox метода оплаты
        self.payment_method.addItem('карта')
        self.payment_method.addItem('наличные')

        # Отображение общей суммы расходов и доходов
        self.expenses_sum.display(expenses_sum)
        self.income_sum.display(income_sum)

        self.dictionary_of_expense = []

        # Добавление id аккаунта пользователя
        self.user_id = user_id

        # Подключаемся к базе данных
        self.con = sqlite3.connect("data.db")
        self.cursor = self.con.cursor()

        # Отображение сегодняшней даты
        self.spending_date.showToday()

        # Чтение базы данных с помощью класса Db_reader и вывод таблицы в TableWidget
        csv_reader = Db_reader(self.dictionary_of_expense, self.cursor, self.user_id, self.con)
        csv_reader.read_transactions_table()
        table_loader = LoadTable(self.dictionary_of_expense, self.transactions_table)
        table_loader.loadTable()

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
                expense_sum = self.expenses_sum.value()
                income_sum = self.income_sum.value()
                # Сохраняем суммы расходов и доходов пользователя
                self.cursor.execute(f'UPDATE user SET expense_sum = {expense_sum}, income_sum = {income_sum}'
                                    f' WHERE id = {self.user_id};')
                self.con.commit()
                # Закрываем базу данных
                self.con.close()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    # Предупреждение перед выходом из аккаунта
    def quit_with_button(self):
        reply = QMessageBox.question(self, 'Выход из аккаунта', 'Вы действительно хотите выйти из аккаунта?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.closed = True
            expense_sum = self.expenses_sum.value()
            income_sum = self.income_sum.value()
            # Сохраняем суммы расходов и доходов пользователя
            self.cursor.execute(f'UPDATE user SET expense_sum = {expense_sum}, income_sum = {income_sum}'
                                f' WHERE id = {self.user_id};')
            self.con.commit()
            # Закрываем базу данных
            self.con.close()
            MyWidget.close(self)
            # Открываем окно входа в аккаунт
            self.pass_dialog.show()
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
            # Запись данных в базу данных с помощью класса Db_writer
            writer = Db_writer(date, sum_of_expense, self.dictionary_of_expense, expense_description, self.cursor,
                               self.user_id, self.con, time, method_of_payment)
            self.dictionary_of_expense = writer.write_table()
            # Вывод таблицы
            table_loader = LoadTable(self.dictionary_of_expense, self.transactions_table)
            table_loader.loadTable()
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
            # Запись данных в базу данных с помощью класса Db_writer
            writer = Db_writer(date, sum_of_income, self.dictionary_of_expense, income_description, self.cursor,
                               self.user_id, self.con)
            self.dictionary_of_expense = writer.write_table()
            # Вывод таблицы
            table_loader = LoadTable(self.dictionary_of_expense, self.transactions_table)
            table_loader.loadTable()
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
        # Удаление всех транзакций данного пользователя из базы данных
        self.cursor.execute(f'DELETE FROM transactions WHERE user_id = {self.user_id};')
        self.cursor.execute(f'UPDATE user SET expense_sum = 0, income_sum = 0'
                            f' WHERE id = {self.user_id};')
        self.con.commit()
        # Создание пустой таблицы
        self.dictionary_of_expense = [{'Дата и время(для расходов)': '',
                                       'Сумма': '',
                                       'Метод оплаты(для расходов)': '',
                                       'Описание': ''}]
        # Вывод таблицы
        LoadTable.loadTable(self)


# Класс ошибки, если пользователь ввел число, меньшее или равное 0
class Zero_error(Exception):
    pass


# Класс чтения базы данных
class Db_reader:
    def __init__(self, dictionary_of_expense, cursor, user_id, con):
        self.dictionary_of_expense = dictionary_of_expense
        self.cursor = cursor
        self.user_id = user_id
        self.con = con

    def read_transactions_table(self):
        # Запись данных в список dictionary_of_expense строчками таблицы в виде словарей
        req = self.cursor.execute(f'SELECT * FROM transactions WHERE user_id = {self.user_id}')
        for row in req.fetchall():
            if row[1] != '':
                self.dictionary_of_expense.append({'Дата и время(для расходов)': row[1],
                                                   'Сумма': int(row[2]),
                                                   'Метод оплаты(для расходов)': row[3],
                                                   'Описание': row[4]})


# Класс записи в базу данных
class Db_writer:
    # Передача всех данных в init
    def __init__(self, date, sum_of_expense, dictionary_of_expense, description,
                 cursor, user_id, con, time='', method_of_payment=''):
        self.date = date
        self.time = time
        self.sum_of_expense = sum_of_expense
        self.method_of_payment = method_of_payment
        self.description = description
        self.dictionary = dictionary_of_expense
        self.cursor = cursor
        self.user_id = user_id
        self.con = con

    # Функция записи данных в базу данных
    def write_table(self):
        # Проверка первой строки таблицы
        if len(self.dictionary) == 1:
            # Если она пустая, то создается новая таблица, удаляя эту строку и добавляя новую
            if self.dictionary[0]['Дата и время(для расходов)'] == '':
                self.dictionary = []
        # Проверка: если не передано время, значит это доход
        if self.time is None:
            # Добавление новой строки в таблицу в виде словаря
            self.dictionary.append({'Дата и время(для расходов)': self.date,
                                    'Сумма': self.sum_of_expense,
                                    'Метод оплаты(для расходов)': self.method_of_payment,
                                    'Описание': self.description})
            self.cursor.execute(f'INSERT INTO transactions VALUES ({self.user_id}, "{self.date} {self.time}",'
                                f'{self.sum_of_expense}, "{self.method_of_payment}", "{self.description}")')
            self.con.commit()
        # Иначе - это расход
        else:
            self.cursor.execute(f'INSERT INTO transactions VALUES ({self.user_id}, "{self.date} {self.time}",'
                                f'{self.sum_of_expense}, "{self.method_of_payment}", "{self.description}")')
            self.con.commit()
            self.dictionary.append({'Дата и время(для расходов)': f'{self.date} {self.time}',
                                    'Сумма': self.sum_of_expense,
                                    'Метод оплаты(для расходов)': self.method_of_payment,
                                    'Описание': self.description})
        return self.dictionary


# Вывод таблицы
class LoadTable:
    def __init__(self, dictionary_of_expense, transactions_table):
        self.dictionary_of_expense = dictionary_of_expense
        self.transactions_table = transactions_table

    def loadTable(self):
        reader = self.dictionary_of_expense
        # Установка 4 столбца в таблицу
        self.transactions_table.setColumnCount(4)
        # Установка названия столбцов
        self.transactions_table.setHorizontalHeaderLabels(['Дата и время(для расходов)', 'Сумма',
                                                           'Метод оплаты(для расходов)', 'Описание'])
        rows = 0
        index_of_rows_expenses = []
        index_of_rows_income = []
        for index, row in enumerate(reader):
            # Добавление новой строки
            rows += 1
            self.transactions_table.setRowCount(rows)
            row = list(row.values())
            row[1] = str(row[1])
            if row != ['', '', '', '']:
                if float(row[1]) < 0:
                    index_of_rows_expenses.append(index)
                elif float(row[1]) > 0:
                    index_of_rows_income.append(index)
            for num in range(4):
                # Запись новой строки
                self.transactions_table.setItem(index, num, QTableWidgetItem(row[num]))
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


# Окно входа в аккаунт
class Login_window(PyQt5.QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.widget = None
        uic.loadUi('login_qt.ui', self)
        self.setWindowTitle('Вход/регистрация в аккаунт')
        self.setFixedSize(self.size())

        # Скрытие строки с паролем
        self.password.setEchoMode(2)

        # Обработка кнопок входа и регистрации
        self.login_button.clicked.connect(self.login_in)
        self.sign_up_button.clicked.connect(self.sign_up)

    # Функция открытия главного окна
    def openMyWidget(self, user_id, expenses_sum=0, income_sum=0):
        Login_window.close(self)
        self.widget = MyWidget(user_id, expenses_sum, income_sum)
        self.widget.show()

    # Функция входа в аккаунт
    def login_in(self):
        # Подключение к базе данных users.db
        con = sqlite3.connect("data.db")
        cursor = con.cursor()
        # Считывание логина и пароля
        login = self.login.text()
        password = self.password.text()
        # Проверка введены ли логин и пароль
        if not login or not password:
            QMessageBox.critical(self, 'Ошибка!', 'Вы заполнили не все поля!', QMessageBox.Ok)
        else:
            # Хеширование пароля с помощью библиотеки hashlib
            password = bytes(password, 'utf-8')
            hash_password = hashlib.sha1(password).hexdigest()
            # Ищем пользователя в таблице users в базе данных
            result_of_execute = cursor.execute("SELECT login, password FROM user WHERE login = ? AND password = ?",
                                               (login, hash_password))
            # Проверка - найден ли пользователь
            if result_of_execute.fetchall():
                # Если да, открываем главное окно и передаем user_id в класс MyWidget
                user_id = cursor.execute("SELECT id FROM user WHERE login = ? AND password = ?",
                                         (login, hash_password)).fetchall()
                expense_sum = cursor.execute("SELECT expense_sum FROM user WHERE login = ? AND password = ?",
                                             (login, hash_password)).fetchall()
                income_sum = cursor.execute("SELECT income_sum FROM user WHERE login = ? AND password = ?",
                                            (login, hash_password)).fetchall()
                # Открываем главное окно и передаем user_id в класс MyWidget
                self.openMyWidget(user_id[0][0], expense_sum[0][0], income_sum[0][0])
            else:
                # В противном случае выносим окно с ошибкой
                return QMessageBox.information(self, 'Внимание!', 'Неправильное имя пользователя или пароль')

    # Функция регистрации в аккаунт
    def sign_up(self):
        # Подключение к базе данных data.db
        con = sqlite3.connect("data.db")
        cursor = con.cursor()
        # Считывание логина и пароля
        login = self.login.text()
        password = self.password.text()
        # Проверка введены ли логин и пароль
        if not login or not password:
            QMessageBox.critical(self, 'Ошибка!', 'Вы заполнили не все поля!', QMessageBox.Ok)
        else:
            # Хеширование пароля с помощью библиотеки hashlib
            password = bytes(password, 'utf-8')
            hash_password = hashlib.sha1(password).hexdigest()
            # Проверяем нет ли пользователя в базе данных
            if_user_exist = cursor.execute(f'SELECT * FROM user WHERE login = {login}')
            if if_user_exist.fetchall():
                # Если пользователь с таким логином уже существует, то выносим окно с ошибкой
                QMessageBox.critical(self, 'Внимание!', 'Пользователь с таким логином уже зарегистрирован.',
                                     QMessageBox.Ok)
            else:
                # Если пользователя, нет заносим его в базу данных
                cursor.execute(f'INSERT INTO user(login,password) VALUES("{login}", "{hash_password}")')
                # Сохраняем таблицу
                con.commit()
                user_id = cursor.execute("SELECT id FROM user WHERE login = ? AND password = ?",
                                         (login, hash_password)).fetchall()
                expense_sum = cursor.execute("SELECT expense_sum FROM user WHERE login = ? AND password = ?",
                                             (login, hash_password)).fetchall()
                income_sum = cursor.execute("SELECT income_sum FROM user WHERE login = ? AND password = ?",
                                            (login, hash_password)).fetchall()
                # Открываем главное окно и передаем user_id в класс MyWidget
                self.openMyWidget(user_id[0][0], expense_sum[0][0], income_sum[0][0])


# Запуск программы
if __name__ == '__main__':
    app = QApplication(sys.argv)
    pass_dialog = Login_window()
    pass_dialog.show()
    sys.exit(app.exec_())
