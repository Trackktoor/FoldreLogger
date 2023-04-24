import difflib as df
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import time

# В данном классе переопределён метод
# on_modified, который будет применяться при
# модификации файлов
class FolderLoggerHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print(event.event_type, event.src_path)

    def on_created(self, event):
        print("on_created", event.src_path)

    def on_deleted(self, event):
        print("on_deleted", event.src_path)

    def on_modified(self, event):
        print("on_modified", event.src_path)

    def on_moved(self, event):
        print("on_moved", event.src_path)



# Функция принимает 2 аргумента типа str
# Возврашает list с разницей в формате ['+ изменённая строка', ...]
def get_change_on_text(text1='default', text2='default'):
    # Проверки аргументов
    if text1 == 'default' or text2 == 'default':
        print('ERROR: один или несколько параметров не заданы')
        if type(text1) is not str or type(text2) is not str:
            print('ERROR: один или несколько параметров не являются строками')
    else:
        # Строки для примера
        #
        # Применяем splitlines для удобочиатемости при выводе
        # иначе вывод будет по одной букве.
        text1 = 'FILE:\n 1\n 2\n 3'.splitlines()
        text2 = 'FILE:\n 11231\n 22\n 3\n 4422'.splitlines()

        # Инициализируем экземпляр объекта для операция
        d = df.Differ()

        # Сам процесс сравнениея
        # Строки с префиксом - присутствуют в первой последовательности, но не во второй.
        # Строки с префиксом + присутствуют во второй последовательности, но не в первой.
        diff = df.unified_diff(text1, text2, lineterm='')

        # Превращаем наш результат в удобочитаемый текст
        diff_string = '\n'.join(diff)

        # С помощью регулярных выражений собираем все нужные нам строки
        change_list = re.findall(r'[?+] \S*', diff_string)

        # Вывод разницы между строками (Фиксируется только добавление/изменение строк)
        return change_list[1:]
    
def _main():
    event_handler = FolderLoggerHandler()
    observer = Observer()
    observer.schedule(event_handler, path='/home/denis/Рабочий стол/1/test_folder', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    _main()
