# class CSVDB:

* def __init__(self, name_db='test_db', force=False):
        """
        инициализация БД
        force - если True, то создаем БД заново, удаляем старую
        тест ОК
        """

* def create_table(self, name_table='NonameTable', colums=['col1', 'col2']):
    """
    создание таблицы в БД, проверяется есть ли файл
    сым файл разделен ;
    return: True - если успешно создан файл таблицы, иначе False
    тест ОК
    """

* def fieldnames(self, name_table):
    """
    вывод заголовков таблицы (названия столбцов) таблицы name_table
    :return:
    """

* def insert_data(self, name_table='NonameTable', data={}):
    """
    добавление данных data в конец файла-таблицы name_table
    :return: True - если успешно добавлены данные в таблицу, иначе False
    тест ОК
    """

* def getall(self, name_table='NonameTable'):
    """
    получение всех данных таблицы name_table
    :param name_table:
    :return:
    """