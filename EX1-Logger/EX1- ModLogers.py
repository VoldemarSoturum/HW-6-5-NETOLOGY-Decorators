# Доработать декоратор logger в коде ниже. Должен получиться 
# декоратор, который записывает в файл 'main.log' дату и время вызова 
# функции, имя функции, аргументы, с которыми вызвалась, и возвращаемое 
# значение. Функция test_1 в коде ниже также должна отработать без ошибок.



import os


def logger(old_function):
    # Основная логика декоратора
    def new_function(*args, **kwargs):
        #Вызываем старую функцию с аргументами
        result = old_function(*args, **kwargs)
        # Для логирования результат используем конструкцию для записи в файл
        with open('main.log', 'a') as log_file:
            log_file.write(f'{old_function.__name__} - args: {args}, kwargs: {kwargs}, result: {result}\n')
        # Возвращаем результат выполнения функции
        return result
    # Возвращаем функцию обёрнутую в декоратор logger
    return new_function

    # *args — чтобы декоратор работал с функциями, у которых 
    # разное количество позиционных аргументов (как в нашем случае 
    # когда тест передаёт именованные аргументы summator(4.3, b=2.2) 
    # и summator(a=0, b=0) — в первом случае два позиционных аргумента, 
    # а во втором — один позиционный и один именованный аргумент
    # ).

    # **kwargs — чтобы декоратор поддерживал именованные 
    # аргументы, "отлавливал" именованные аргументы.
    # (в нашем случае те данные, которые передаёт 
    # тест в строке summator(4.3, b=2.2), 4.3 -- не именованный, позиционный ргумент
    # b=2.2 -- именованны аргумент. Таким же образом в summator(a=0, b=0)).
# Из нашего примера:

# Декоратор logger перехватывает вызов и получает:
# 1) args = (4.3,) (позиционный аргумент 4.3).
# 2) kwargs = {'b': 2.2} (именованный аргумент b=2.2)ю

def test_1():

    path = 'main.log'
    if os.path.exists(path):
        os.remove(path)

    @logger
    def hello_world():
        return 'Hello World'

    @logger
    def summator(a, b=0):
        return a + b

    @logger
    def div(a, b):
        return a / b

    assert 'Hello World' == hello_world(), "Функция возвращает 'Hello World'"
    result = summator(2, 2)
    assert isinstance(result, int), 'Должно вернуться целое число'
    assert result == 4, '2 + 2 = 4'
    result = div(6, 2)
    assert result == 3, '6 / 2 = 3'
    
    assert os.path.exists(path), 'файл main.log должен существовать'

    summator(4.3, b=2.2)
    summator(a=0, b=0)

    with open(path) as log_file:
        log_file_content = log_file.read()

    assert 'summator' in log_file_content, 'должно записаться имя функции'
    for item in (4.3, 2.2, 6.5):
        assert str(item) in log_file_content, f'{item} должен быть записан в файл'


if __name__ == '__main__':
    test_1()