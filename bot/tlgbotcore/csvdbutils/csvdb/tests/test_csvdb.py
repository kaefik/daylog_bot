"""
провести в порядок тесты
"""

import unittest

import os
import shutil
import csv

from csvdb import CSVDB


class TestCSVDB(unittest.TestCase):
    """
        тесты для проверки работы объекта CSVDB
    """

    def remove_dbdir(self):
        """
        удаление БД папки даже она существует
        """
        if os.path.exists(self.tst_name_db):
            shutil.rmtree(self.tst_name_db)

    def create_dbdir(self):
        """
        создание БД папки если ёё нет, если есть то удаляется и заново создается
        """
        if os.path.exists(self.tst_name_db):
            shutil.rmtree(self.tst_name_db)

        os.mkdir(self.tst_name_db)
        print("File ", self.file1)
        # создаем простой файл внутри папки
        with open(self.file1, "w") as f:
            f.write("Tecт")

    def setUp(self) -> None:
        self.tst_name_db = "my_test_db"
        self.file1 = f"{self.tst_name_db}/file1.csv"
        self.tst_table1 = 'table1'

    def tearDown(self) -> None:
        self.remove_dbdir()

    def test_initdb_noexist_dirdb(self):
        """
            проверка правильно ли отрабатывается инициализация БД когда папки БД не существует
        """

        # инициализация тестового окружения
        self.remove_dbdir()

        db = CSVDB(name_db=self.tst_name_db)
        flag = os.path.exists(self.tst_name_db) and os.path.isdir(self.tst_name_db)
        self.assertEqual(True, flag)

    def test_initdb_exist_dirdb_force(self):
        """
            проверка правильно ли отрабатывается инициализация БД когда папки БД  существует и нужно перезаписать
        """

        # инициализация тестового окружения
        self.create_dbdir()

        db = CSVDB(name_db=self.tst_name_db, force=True)
        flag_dir = os.path.exists(self.tst_name_db) and os.path.isdir(self.tst_name_db)

        flag_file = os.path.exists(self.file1) and os.path.isfile(self.tst_name_db)

        self.assertEqual(True, flag_dir)
        self.assertEqual(False, flag_file)

    def test_initdb_exist_dirdb_noforce(self):
        """
            проверка правильно ли отрабатывается инициализация БД когда папки БД  существует и НЕ нужно перезаписать
        """

        # инициализация тестового окружения
        self.create_dbdir()

        db = CSVDB(name_db=self.tst_name_db, force=False)
        flag_dir = os.path.exists(self.tst_name_db) and os.path.isdir(self.tst_name_db)

        flag_file = os.path.exists(self.file1) and os.path.isfile(self.file1)

        self.assertEqual(True, flag_dir)
        self.assertEqual(True, flag_file)

    def test_create_table(self):
        """
        создание таблицы
        """
        self.remove_dbdir()

        db = CSVDB(name_db=self.tst_name_db, force=False)

        headers_original = ['NUMBER', 'FIO', 'ROLE']

        db.create_table(name_table=self.tst_table1, colums=headers_original)

        full_path_table1 = db.full_path(self.tst_table1)
        flag_name_table = db.tables[0]

        flag_exist_table = os.path.exists(full_path_table1)
        print(full_path_table1)

        # проверяем что файл присутствует
        self.assertEqual(True, flag_exist_table)

        # проверяем заголовки файла таблицы
        headers = []
        with open(full_path_table1) as f:
            reader = csv.DictReader(f, delimiter=";")
            headers = reader.fieldnames

        self.assertEqual(headers, headers_original)

    def test_create_table_exist_table(self):
        """
        создание таблицы, файл которой уже есть
        """
        self.remove_dbdir()

        db = CSVDB(name_db=self.tst_name_db, force=False)

        headers_original = ['NUMBER', 'FIO', 'ROLE']

        flag_noexist = db.create_table(name_table=self.tst_table1, colums=headers_original)
        flag_exist = db.create_table(name_table=self.tst_table1, colums=headers_original)

        self.assertEqual(True, flag_noexist)
        self.assertEqual(False, flag_exist)

    def test_insert_data(self):
        """
        тест вставки данных
        :return:
        """
        headers_original = ['NUMBER', 'FIO', 'ROLE']
        data_original = {'NUMBER': '1', 'FIO': 'Ivanov Fedor', 'ROLE': 'Admin'}

        self.remove_dbdir()

        db = CSVDB(name_db=self.tst_name_db, force=False)
        flag_noexist = db.create_table(name_table=self.tst_table1, colums=headers_original)

        full_path_table1 = db.full_path(self.tst_table1)

        db.insert_data(name_table=self.tst_table1, data=data_original)

        result_data = db.getall(name_table=self.tst_table1)
        self.assertEqual(result_data[0], data_original)
        #  проверяем что запись одна
        self.assertEqual(1, len(result_data))

        # добавляем ещё одну запись
        db.insert_data(name_table=self.tst_table1, data=data_original)

        result_data = db.getall(name_table=self.tst_table1)
        self.assertEqual(2, len(result_data))

    if __name__ == '__main__':
        unittest.main()
