"""
реализация БД с помощью CSV файлов.

каждый файл это таблица, папка символизирует БД
"""
import os
import shutil
import csv


class CSVDB:

    def full_path(self, name=''):
        return f"{self.name_db}/{name}.csv"

    def __init__(self, name_db='test_db', force=False):
        """
        инициализация БД
        force - если True, то создаем БД заново, удаляем старую
        тест ОК
        """
        self.name_db = name_db  # название БД
        self.tables = []  # файлы таблиц

        if os.path.exists(self.name_db):
            print("папка БД существует")
            if force:
                print("Удаляем папку БД")
                shutil.rmtree(self.name_db)
            else:
                return
        else:
            print("папки БД нет.")

        print("Создаем папку БД")
        os.mkdir(self.name_db)

    def create_table(self, name_table='NonameTable', colums=['col1', 'col2']):
        """
        создание таблицы в БД, проверяется есть ли файл
        сым файл разделен ;
        return: True - если успешно создан файл таблицы, иначе False
        тест ОК
        """
        # full_path = f"{self.name_db}/{name_table}.csv"
        if os.path.exists(self.full_path(name_table)):
            return False

        with open(self.full_path(name_table), mode="w", encoding='utf-8') as w_file:
            file_writer = csv.DictWriter(w_file, delimiter=";", fieldnames=colums)
            file_writer.writeheader()

        self.tables.append(name_table)
        return True

    def fieldnames(self, name_table):
        """
        вывод заголовков таблицы (названия столбцов) таблицы name_table
        :return:
        """
        filename = self.full_path(name_table)
        with open(filename) as f:
            reader = csv.DictReader(f, delimiter=";")
            headers = reader.fieldnames

        return headers

    def insert_data(self, name_table='NonameTable', data={}):
        """
        добавление данных data в конец файла-таблицы name_table
        :return: True - если успешно добавлены данные в таблицу, иначе False
        тест ОК
        """
        # full_path = f"{self.name_db}/{name_table}.csv"

        columns = self.fieldnames(name_table)

        with open(self.full_path(name_table), mode="a", encoding='utf-8') as w_file:
            file_writer = csv.DictWriter(w_file, delimiter=";", fieldnames=columns)
            file_writer.writerow(data)

        return True

    def getall(self, name_table='NonameTable'):
        """
        получение всех данных таблицы name_table
        :param name_table:
        :return:
        """
        full_path_table1 = self.full_path(name_table)
        result_data = []
        with open(full_path_table1) as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                result_data.append(row)
        return result_data
