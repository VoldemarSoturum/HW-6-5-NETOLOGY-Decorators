# Импорт необходимых библиотек
import requests                     # Для отправки HTTP-запросов
from bs4 import BeautifulSoup       # Для парсинга HTML
from urllib.parse import urljoin    # Для объединения URL
from fake_headers import Headers    # Для генерации фейковых заголовков
from selenium import webdriver      # Для работы с браузером
from webdriver_manager.chrome import ChromeDriverManager         # Для управления ChromeDriver
from selenium.webdriver.chrome.service import Service            # Для настройки сервиса Chrome
from datetime import datetime                                    # Для работы с датами

import time  # Для задержек между запросами

#+++++++++++++++++++++++++++++ЛОГИРОВАНЕ ПО ЗАДАНИЮ+++++++++++++++++++++++++++++++

#Создаём декоратор и описываем тело декоратора
def logger(path):
    def __logger(old_function):
        def new_function(*args, **kwargs):
            result = old_function(*args, **kwargs)
            with open(path, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] {old_function.__name__} | args: {args}, kwargs: {kwargs} | result: {result}\n")
            return result
        return new_function
    return __logger
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Конфигурационные константы
BASE_URL = "https://habr.com/ru/articles/"  # Базовый URL для парсинга
KEYWORDS = ['python', 'анализ данных', 'машинное обучение', 'IT', 'найм']  # Ключевые слова для поиска

MAX_ARTICLES = 5  # Ограничение количества анализируемых статей
DELAY = 5  # Задержка между запросами (секунды)

# ===================== ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ПОЛНОГО ТЕКСТА СТАТЬИ =====================
@logger('habr_parser.log') # !!!!ДЕКОРАТОР ДЛЯ СБОРА ЛОГОВ ВЫПОЛНЕНИЯ ФУНКЦИИ!!!!
def get_full_article_text(url):
    """Получает полный текст статьи по URL"""
    try:
        # Генерируем случайные заголовки для запроса
        headers = Headers(headers=True).generate()
        
        # Отправляем запрос к статье
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Проверяем успешность запроса
        
        # Парсим HTML статьи
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Находим основной текст статьи (селектор для Хабра)
        article_body = soup.find('div', class_='tm-article-body')
        
        if article_body:
            # Удаляем ненужные элементы (код, цитаты и т.д.)
            for element in article_body.find_all(['pre', 'blockquote', 'code']):
                element.decompose()
            
            # Возвращаем чистый текст в нижнем регистре
            return article_body.get_text(separator=' ', strip=True).lower()
        return ""
    except Exception as e:
        print(f"Ошибка при получении статьи {url}: {e}")
        return ""

# ===================== ОСНОВНАЯ ФУНКЦИЯ ПАРСИНГА =====================
@logger('habr_parser.log') # !!!!ДЕКОРАТОР ДЛЯ СБОРА ЛОГОВ ВЫПОЛНЕНИЯ ФУНКЦИИ!!!!
def get_habr_articles():
    try:
        # Генерируем случайные заголовки для запроса
        header = Headers(headers=True).generate()
        
        # Отправляем GET-запрос к целевому сайту
        response = requests.get(BASE_URL, headers=header)
        response.raise_for_status()  # Проверяем успешность запроса
        
        # Создаем объект BeautifulSoup с парсером lxml
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Ищем все элементы статей на странице
        articles = soup.find_all('article', class_='tm-articles-list__item')
        
        if not articles:
            print("Не удалось найти статьи с помощью requests. Пробуем Selenium...")
            return get_habr_articles_selenium()
        
        results = []  # Список для хранения результатов
        
        # Перебираем найденные статьи
        for article in articles:
            # ============= АНАЛИЗ ПРЕВЬЮ СТАТЬИ =============
            # Ищем заголовок статьи
            title_elem = article.find('h2', class_='tm-title')
            if not title_elem:
                continue  # Пропускаем если заголовок не найден
                
            # Извлекаем текст заголовка
            title = title_elem.text.strip()
            
            # Формируем полную ссылку на статью
            link = urljoin(BASE_URL, title_elem.find('a')['href'])
            
            # Ищем элемент с датой публикации
            time_elem = article.find('time')
            date = time_elem['datetime'] if time_elem else 'Дата не указана'
            
            # Ищем текст превью статьи
            preview = article.find('div', class_='article-formatted-body')
            preview_text = preview.text.lower() if preview else ''
            
            # ============= АНАЛИЗ ПОЛНОГО ТЕКСТА СТАТЬИ =============
            # Получаем полный текст статьи
            full_text = get_full_article_text(link)
            time.sleep(DELAY)  # Задержка между запросами
            
            # Проверяем наличие ключевых слов:
            # Во первых в заголовке
            # Во вторых в превью
            # И напоследок в полном тексте
            if any(keyword.lower() in title.lower() or 
                   keyword.lower() in preview_text or 
                   keyword.lower() in full_text for keyword in KEYWORDS):
                # Форматируем результат и добавляем в список
                results.append(f"{date} – {title} – {link}")
        
        return results
        
    except requests.exceptions.RequestException:
        print("Ошибка запроса. Пробуем Selenium...")
        return get_habr_articles_selenium()

# ===================== АЛЬТЕРНАТИВНО ВЫПОЛНЯЕМ ПОИСК ЧЕРЕЗ СЕЛЕНИУМ (так как содержимое может динамически наполняться) =====================
# @logger('habr_parser.log') # !!!!ДЕКОРАТОР ДЛЯ СБОРА ЛОГОВ ВЫПОЛНЕНИЯ ФУНКЦИИ(СЛИШКОМ МНОГО БУКАВ)!!!!
def get_habr_articles_selenium():
    try:
        # Настраиваем Selenium WebDriver
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Режим без графического интерфейса
        options.add_argument('--disable-blink-features=AutomationControlled')  # Скрываем автоматизацию
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(BASE_URL)
        time.sleep(DELAY)  # Ожидаем загрузки страницы, чтобы избежать проблем с динамическим контентом
        
        # Парсим HTML страницы
        soup = BeautifulSoup(driver.page_source, 'lxml')
        articles = soup.find_all('article', class_='tm-articles-list__item')[:MAX_ARTICLES]
        
        results = []
        
        for article in articles:
            # ============= АНАЛИЗ ПРЕВЬЮ СТАТЬИ =============
            title_elem = article.find('h2', class_='tm-title')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            link = urljoin(BASE_URL, title_elem.find('a')['href'])
            time_elem = article.find('time')
            date = time_elem['datetime'] if time_elem else 'Дата не указана'
            
            # ============= АНАЛИЗ ПОЛНОГО ТЕКСТА СТАТЬИ =============
            # Переходим на страницу статьи
            driver.get(link)
            time.sleep(DELAY)
            
            # Парсим полный текст статьи
            article_soup = BeautifulSoup(driver.page_source, 'lxml')
            article_body = article_soup.find('div', class_='tm-article-body')
            full_text = article_body.get_text(separator=' ', strip=True).lower() if article_body else ""
            
            # Проверяем ключевые слова:
            # В заголовке и в полном тексте
            
            if any(keyword.lower() in title.lower() or 
                   keyword.lower() in full_text for keyword in KEYWORDS):
                results.append(f"{date} – {title} – {link}")
            
            # Возвращаемся на главную страницу
            driver.back() # Возвращаемся к списку статей
            time.sleep(DELAY)
        
        driver.quit()
        return results
        
    except Exception as e:
        print(f"Ошибка в Selenium: {e}")
        if 'driver' in locals():
            driver.quit()
        return []

# ===================== MAIN EXECUTION =====================
if __name__ == "__main__":
#+++++++++++++++++++++++++СБОР ЛОГОВ СО ВСЕГО СКРИПТА (НАЧАЛЬНАЯ ТОЧКА - ЗАПУСК)++++    
    start_time = datetime.now()
    
    with open('habr_parser.log', 'a', encoding='utf-8') as f:
        f.write(f"\n=== Парсинг запущен {start_time} ===\n")
        f.write(f"Ключевые слова: {KEYWORDS}\n")
#++++++++++++++++++НИЖЕ СТРОКА БЕЗ ИЗМЕНЕНИЙ++++++++++++++++++++++++
    articles = get_habr_articles()
#++++++++++++++++++++++СБОР ЛОГОВ СО ВСЕГО СКРИПТА (РЕЗУЛЬТАТЫ)+++++++++++++++++++++++++++++++++++++++++++
    end_time = datetime.now()
    duration = end_time - start_time
    
    with open('habr_parser.log', 'a', encoding='utf-8') as f:
        f.write(f"Найдено статей: {len(articles)}\n")
        f.write(f"Время выполнения: {duration.total_seconds():.2f} сек\n")
        f.write(f"=== Парсинг завершен {end_time} ===\n\n")
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    if articles:
        print(f"Найдено {len(articles)} статей:")
        for article in articles:
            print(article)
    else:
        print("Статьи по заданным ключевым словам не найдены.")



# ДО ВНЕСЁННЫХ ИЗМЕНЕНИЙ (мало статей с ключевыми словами потому что ищем только в заголовке и превью):

# Найдено 2 статей:
# 2025-08-07T12:46:07.000Z – Крах найма в IT. Подделанные Паспорта и Трудовые книжки. Волки-менторы как раковая опухоль рынка – https://habr.com/ru/articles/935038/
# 2025-08-07T12:29:56.000Z – Когда if-else не нужен: знакомство с тернарным оператором и switch в JS – https://habr.com/ru/companies/selectel/articles/934850/

# ПОСЛЕ МОДИФИКАЦИИ (больше статей с ключевыми словами потому что теперь ищем в полном тексте):

# Найдено 12 статей:
# 2025-08-07T14:01:20.000Z – Google и Яндекс внедрили ИИ в поисковики — и это сильно меняет подход к SEO. Разработали план действий – https://habr.com/ru/companies/agima/articles/935044/
# 2025-08-07T13:59:52.000Z – Топ-17 самых прибыльных таск-трекеров. Сколько стоят и зарабатывают популярные сервисы – https://habr.com/ru/companies/yougile/articles/935074/  
# 2025-08-07T13:45:16.000Z – Как развивать DevRel без бюджета: личный опыт и практические советы – https://habr.com/ru/companies/pgk/articles/933770/
# 2025-08-07T13:43:34.000Z – Удалить полпроекта: как мы переписывали MobX‑сторы на React Query в большом Next.js‑проекте – https://habr.com/ru/companies/kts/articles/935086/ 
# 2025-08-07T13:39:11.000Z – 5 примеров запрета продажи электроники из-за патентного спора – https://habr.com/ru/companies/onlinepatent/articles/935078/
# 2025-08-07T13:37:06.000Z – Реальная безопасность корпоративной сети — роль брокеров сетевых пакетов в анализе угроз – https://habr.com/ru/companies/dsol/articles/935072/   
# 2025-08-07T13:22:51.000Z – Операционная система от А до Я: Таймер и HAL – https://habr.com/ru/articles/935058/
# 2025-08-07T13:15:12.000Z – Нейросетевой помощник для Catan Universe: как я научил ИИ считать карты соперников – https://habr.com/ru/articles/935054/
# 2025-08-07T13:07:04.000Z – Учимся разрабатывать для GPU на примере операции GEMM – https://habr.com/ru/companies/yadro/articles/934878/
# 2025-08-07T13:01:08.000Z – Личное облако Sandstorm. Платформа для опенсорсных веб-приложений – https://habr.com/ru/companies/ruvds/articles/934962/
# 2025-08-07T12:46:07.000Z – Крах найма в IT. Подделанные Паспорта и Трудовые книжки. Волки-менторы как раковая опухоль рынка – https://habr.com/ru/articles/935038/
# 2025-08-07T12:40:39.000Z – Прозрачное обнаружение предвзятости в ИИ: Новый подход с использованием аргументации – https://habr.com/ru/articles/935030/