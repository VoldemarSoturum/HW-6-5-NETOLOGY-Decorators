# ЗАДАНИЕ: Применить написанный логгер к приложению из любого предыдущего д/з.

# ВСЁ ЧТО С ++++++++++++++++++++ --- Обрамление вставки для задания.

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

# Создаём декоратор и описываем тело декоратора
def logger(path):
    def __logger(old_function):
        def new_function(*args, **kwargs):
            try:
                result = old_function(*args, **kwargs)
                log_entry = (
                    f"[{datetime.now()}] {old_function.__name__} | "
                    f"args: {args}, kwargs: {kwargs} | "
                    f"result: {str(result)[:100]}...\n"  # ОБРЕЗАЕМ ПОТОМУ ЧТО ВЫВОД БУДЕТ ООООЧЕНЬ ДЛИННЫМ!!!
                )
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
                return result
            
            except Exception as e:
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] ⚠️ {old_function.__name__} | ERROR: {str(e)}\n")
                raise  # Перебрасываем ошибку дальше
                
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

# ===================== ОСНОВНАЯ ФУНКЦИЯ ПАРСИНГА (ГЕНЕРАТОР) =====================
def get_habr_articles_generator():
    """Генератор для постепенного получения статей"""
    try:
        header = Headers(headers=True).generate()
        response = requests.get(BASE_URL, headers=header)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        articles = soup.find_all('article', class_='tm-articles-list__item')
        
        if not articles:
            print("Не удалось найти статьи с помощью requests. Пробуем Selenium...")
            yield from get_habr_articles_selenium_generator()
            return
        
        keywords_lower = [kw.lower() for kw in KEYWORDS]
        
        for article in articles:
            title_elem = article.find('h2', class_='tm-title')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            link = urljoin(BASE_URL, title_elem.find('a')['href'])
            time_elem = article.find('time')
            date = time_elem['datetime'] if time_elem else 'Дата не указана'
            
            preview = article.find('div', class_='article-formatted-body')
            preview_text = preview.text.lower() if preview else ''
            
            full_text = get_full_article_text(link)
            time.sleep(DELAY)
            
            matched_keywords = [kw for kw in keywords_lower 
                              if kw in title.lower() 
                              or kw in preview_text 
                              or kw in full_text]
            
            if matched_keywords:
                result_entry = f"{date} – {title} – {link}"
                with open('habr_parser.log', 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] ✔ Найдена статья. Ключевые слова: {matched_keywords}\n")
                    f.write(f"    {result_entry}\n")
                yield result_entry
                
    except requests.exceptions.RequestException:
        print("Ошибка запроса. Пробуем Selenium...")
        yield from get_habr_articles_selenium_generator()

# ===================== ОСНОВНАЯ ФУНКЦИЯ ПАРСИНГА (СТАРАЯ ВЕРСИЯ) =====================
@logger('habr_parser.log')
def get_habr_articles():
    """Совместимость со старой версией"""
    return list(get_habr_articles_generator())

# ===================== ФУНКЦИЯ СЕЛЕНИУМ (ГЕНЕРАТОР) =====================
def get_habr_articles_selenium_generator():
    """Генератор для Selenium-парсинга"""
    try:
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(BASE_URL)
        time.sleep(DELAY)
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        articles = soup.find_all('article', class_='tm-articles-list__item')[:MAX_ARTICLES]
        
        keywords_lower = [kw.lower() for kw in KEYWORDS]
        
        for article in articles:
            title_elem = article.find('h2', class_='tm-title')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            link = urljoin(BASE_URL, title_elem.find('a')['href'])
            time_elem = article.find('time')
            date = time_elem['datetime'] if time_elem else 'Дата не указана'
            
            driver.get(link)
            time.sleep(DELAY)
            
            article_soup = BeautifulSoup(driver.page_source, 'lxml')
            article_body = article_soup.find('div', class_='tm-article-body')
            full_text = article_body.get_text(separator=' ', strip=True).lower() if article_body else ""
            
            matched_keywords = [kw for kw in keywords_lower 
                              if kw in title.lower() 
                              or kw in full_text]
            
            if matched_keywords:
                result_entry = f"{date} – {title} – {link}"
                with open('habr_parser.log', 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] ✔ Найдена статья (Selenium). Ключевые слова: {matched_keywords}\n")
                    f.write(f"    {result_entry}\n")
                yield result_entry
            
            driver.back()
            time.sleep(DELAY)
        
        driver.quit()
        
    except Exception as e:
        print(f"Ошибка в Selenium: {e}")
        if 'driver' in locals():
            driver.quit()
        raise

# ===================== ФУНКЦИЯ СЕЛЕНИУМ (СТАРАЯ ВЕРСИЯ) =====================
@logger('habr_parser.log')
def get_habr_articles_selenium():
    """Совместимость со старой версией"""
    return list(get_habr_articles_selenium_generator())

# ===================== MAIN EXECUTION =====================
# ===================== MAIN EXECUTION =====================
if __name__ == "__main__":
    log_file = 'habr_parser.log'
    start_time = datetime.now()
    articles = []  # Инициализируем список статей
    
    try:
        # Открываем лог-файл для записи начала работы
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n=== Парсинг запущен {start_time} ===\n")
            f.write(f"Ключевые слова: {KEYWORDS}\n")
        
        # Создаем генератор
        article_generator = get_habr_articles_generator()
        
        # Обрабатываем результаты по мере их поступления
        while True:
            try:
                article = next(article_generator)
                articles.append(article)
                print(f"Найдена статья: {article}")
                
                # Записываем в лог немедленно
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] ✔ Статья добавлена в результаты: {article}\n")
            
            except StopIteration:
                # Генератор закончил работу
                break
            
            except KeyboardInterrupt:
                print("\nПарсинг прерван пользователем")
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write("\n!!! Парсинг прерван пользователем !!!\n")
                break
            
            except Exception as e:
                print(f"\nПроизошла ошибка: {e}")
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"!!! ОШИБКА: {str(e)}\n")
                break
    
    finally:
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Вывод итоговой информации
        print(f"\nИтоговая информация:")
        print(f"Найдено статей: {len(articles)}")
        print(f"Время выполнения: {duration.total_seconds():.2f} сек")
        print(f"Парсинг завершен: {end_time}")
        
        # Запись итогов в лог
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\nНайдено статей: {len(articles)}\n")
            f.write(f"Время выполнения: {duration.total_seconds():.2f} сек\n")
            f.write(f"=== Парсинг завершен {end_time} ===\n\n")
        
        # Вывод всех найденных статей
        if articles:
            print("\nСписок найденных статей:")
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article}")