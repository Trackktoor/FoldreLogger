import difflib as df
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import time
import os




def get_valid_changed_string(changed_string):
    return changed_string[2:]

# В данном классе переопределён метод
# on_modified, который будет применяться при
# модификации файлов
class FolderLoggerHandler(FileSystemEventHandler):
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
            else:
                pass

        else:
            pass

    def on_moved(self, event):
        print("on_moved", event.src_path)

def get_text_on_file(absolute_path_on_file):

    with open(absolute_path_on_file, 'r') as f:
        return f.read()

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
    
# функция-менеджер которая собирает все созданные функции
# конфигурирует их и запускает
def _main():
    create_cache_files('/home/denis/Рабочий стол/1/test_folder')

    event_handler = FolderLoggerHandler()
    observer = Observer()
    observer.schedule(event_handler, path='/home/denis/Рабочий стол/1/test_folder/', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    _main()