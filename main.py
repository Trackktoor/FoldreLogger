import difflib as df
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import yaml
from yaml.loader import SafeLoader
import time
from datetime import datetime
import os
import json
import os
import pwd


# Вовзаращает валидную строку изменений
# Принимает строку изменения аргументом из функции 
# get_change_on_text
def get_valid_changed_string(changed_string):
    return changed_string[2:].strip()

# В данном классе переопределён метод
# on_modified, который будет применяться при
# модификации файлов
class FolderLoggerHandler(FileSystemEventHandler):
    dirOutputFile = 'DEFAULT'

    def on_created(self, event):
        print("on_created", event.src_path)

    def on_deleted(self, event):
        print("on_deleted", event.src_path)

    def on_modified(self, event):
        if event.src_path.endswith('.txt'):
            target_file_name = get_file_name_for_absolute_path(event.src_path)

            text_on_changed_file = get_text_on_file(event.src_path)
            text_on_cache_file = get_text_on_file('./cache_folder/' + target_file_name)

            list_changes = list(map(get_valid_changed_string,get_change_on_text(text_on_cache_file,text_on_changed_file)))
            if len(list_changes) != 0:
                print("on_modified: ", list_changes)

                update_cache_file('./cache_folder/' + target_file_name, text_on_changed_file)

                print('CACHE FILE UPDATE')
                # Получаем информацию о файле
                st = os.stat(event.src_path)
                # Получаем ID процесса
                pid = os.getpid()
                # Получаем имя пользователя, который владеет файлом
                user = pwd.getpwuid(st.st_uid).pw_name

                change_log_file(list_changes, self.dirOutputFile, pid, user)
            else:
                pass
        
        else:
            pass

    def on_moved(self, event):
        print("on_moved", event.src_path)


# Добавляет информацию в лог-файл
# в change_list нужно передавать массив со строками изменений
# Не словарь (Который объект в JS)
def change_log_file(change_list, dirOutputFile, pid, user):
    # Читаем наш файл логов
    with open(dirOutputFile + 'source-file-name.json', 'r') as f:
        info = json.load(f)

    # Записываем новые значение в переменную с прочитанным файлом
    for i in  change_list:
        date_now = datetime.now()
        info['data'].append({"message":i, "timestamp":str(date_now),"process":pid,"user":user})
    
    # Перезаписываем файл 
    with open(dirOutputFile + 'source-file-name.json', 'w') as f:

        json.dump(info, f, sort_keys=True, indent=2)

# Получаем текст из файла
def get_text_on_file(absolute_path_on_file):

    with open(absolute_path_on_file, 'r') as f:
        return f.read()

# Обновление кеш-файла обноволённого файла
# Принимает абсолюный путь и новый текст для кеш-файла
def update_cache_file(absolute_path_on_file, new_text):
    with open(absolute_path_on_file, 'w') as f:
        f.write(new_text)

# Получает имя файла из абсолютного пути к файлу
def get_file_name_for_absolute_path(absolute_path):
    absolute_path_split = absolute_path.split('/')
    return absolute_path_split[-1:][0]

# Возвращает список имён файлов директории (без рекурсии)
def get_name_files_in_folder(path):
    res = []
    for root, dirs, files in os.walk(path):  
        for filename in files:
            res.append(str(filename))
    
    return res

# Функция копирует все файлы указанной дериктории
# в папку cache_folder для дальнейшего выявления
# изменений в файлах
def create_cache_files(path_on_target_folder):
    file_names = get_name_files_in_folder(path_on_target_folder)

    for file_name in file_names:
        src_on_test_folder = './cache_folder'

        with open(path_on_target_folder +  '/' + file_name, 'r') as f:
            data_target_file = f.read()

        with open(src_on_test_folder +  '/' + file_name, 'w') as f:
            f.write(data_target_file)

# Функция принимает 2 аргумента типа str
# Возврашает list с разницей в формате ['\n+изменённая строка', ...]
def get_change_on_text(text1='default', text2='default'):
    # Проверки аргументов
    if text1 == 'default' or text2 == 'default':
        print('ERROR: один или несколько параметров не заданы')
        if type(text1) is not str or type(text2) is not str:
            print('ERROR: один или несколько параметров не являются строками')
    else:
        # Применяем splitlines для удобочиатемости при выводе
        # иначе вывод будет по одной букве.
        text1 = text1.splitlines()
        text2 = text2.splitlines()

        # Инициализируем экземпляр объекта для операция
        d = df.Differ()

        # Сам процесс сравнениея
        # Строки с префиксом - присутствуют в первой последовательности, но не во второй.
        # Строки с префиксом + присутствуют во второй последовательности, но не в первой.
        diff = df.unified_diff(text1, text2, lineterm='')

        # Превращаем наш результат в удобочитаемый текст
        diff_string = '\n'.join(diff)

        # С помощью регулярных выражений собираем все нужные нам строки
        change_list = re.findall(r'\n[?+].*', diff_string)

        # Вывод разницы между строками (Фиксируется только добавление/изменение строк)
        return change_list[1:]

# Функция для получения аргументво из файла config.yml
# Файл должен располгаться вместе с main.py в одной дериктории!!
def get_config_info():
    with open('config.yml') as f:
        data = yaml.load(f, Loader=SafeLoader)
        dirLogFile = data['DirLogFile']
        dirOutputFile = data['dirOutputFile']
        return {'dirLogFile':dirLogFile, 'dirOutputFile':dirOutputFile}

# функция-менеджер которая собирает все созданные функции
# конфигурирует их и запускает
def _main(dirLogFile,dirOutputFile):
    # Создаём кеш-файлы для будующего сравнения
    create_cache_files(dirLogFile)
    
    # Инициализируем хендлер для обработки событий налюдения
    event_handler = FolderLoggerHandler()

    # Передаём расположение выходного JSON файла
    FolderLoggerHandler.dirOutputFile = dirOutputFile

    # Инициализируем наблюдателя
    observer = Observer()
    # Конфигурируем наш наблюдатель
    observer.schedule(event_handler, path=dirLogFile, recursive=False)
    # Создаем новый поток в котором будет бесконечно наблюдаться изменения за файлами
    observer.start()

    # Бесконечный цикл для возможности закрытия потока с наблюдением
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        # В слуачае ручной отмены закрываем поток
        observer.stop()
    observer.join()

if __name__ == '__main__':
    # Получаем конфигурацию
    arr_info = get_config_info()

    # Запуск наблюдения
    _main(arr_info['dirLogFile'],arr_info['dirOutputFile'])
