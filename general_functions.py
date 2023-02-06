import time
import pandas as pd
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as ec
import random
import numpy as np
import os
from collections import Counter
from itertools import chain

def test_page(driver, delay, element):
    '''Функция проверки загрузки страницы
        delay - количество секунд ожидания
        element - что ищем пример (By.CLASS_NAME, 'popup-obj')
        driver - драйвер пример
        if __name__ == "__main__":
        driver = Chrome(executable_path="./chromedriver.exe")'''
    # проверка загрузилась ли стр
    try:
        myElem = WebDriverWait(driver, delay).until(
            ec.presence_of_element_located(
                element))
    except TimeoutException:
        print("Loading took too much time!")


def constrained_sum_sample_pos(n, total):
    """Генерация n случайных чисел, так
     чтобы сумма равнялась total"""
    dividers = sorted(random.sample(range(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


def scrol(driver, n_down=20, n_up=5, always_up=False):
    """Функция, которая позволяет скролить вниз с интервалами
    driver - браузер
    n_down - на сколько этапов поделится прокручивание вниз
    n_up - на сколько этапов пделитmся прокручивание вверх"""
    # Определяем величину страницы
    last_height = driver.execute_script("return document.body.scrollHeight")
    # Выбираем n_down случайных чисел так, чтобы сумма равнялась 5000
    scrol = constrained_sum_sample_pos(n=n_down, total=last_height)
    for s in scrol:
        # Прокрутить страницу вниз
        driver.execute_script(f"scrollBy(0,{s})")
        # Задержка для прогрузки страницы
        time.sleep(
            random.choice(np.arange(0.1, 0.2, 0.01)))
    # выберем случайное значение для имитации случайности
    rand = random.choice([0, 1])
    if (rand == 1) or (always_up):
        # Выбираем n_up случайных чисел так, чтобы сумма равнялась 5000
        scrol = constrained_sum_sample_pos(n=n_up, total=last_height)
        for s in scrol:
            # Прокрутить страницу вниз
            driver.execute_script(f"scrollBy(0,-{s})")
            # Задержка для прогрузки страницы
            time.sleep(
                random.choice(np.arange(0.1, 0.2, 0.01)))


def get_last_file(path):
    """Функция позволяет определить последний добавленный файл в папку и открыть его"""
    # получаем название всех файлов из папки
    files = os.listdir(path)
    # объединяем путь и название файла
    files = [os.path.join(path, file) for file in files]
    # Оставляем в списке только файлы
    files = [file for file in files if os.path.isfile(file)]
    # Определяем файл, у которого самое последнее время создания
    file_path = max(files, key=os.path.getctime)
    # Открываем файл со ссылками
    df_all_links = pd.read_excel(file_path)
    # Оставляем только уникальные ссылки
    df_all_links = df_all_links.drop_duplicates(subset=['url'])
    return df_all_links

def get_df_region_guide():
    """ Функция формирует из потока дата-фрейм с названиями регионов"""
    df_regions = pd.read_csv('dict_gar_fns_regions_hierarchy_level_locality_202301221100.csv')
    # Определим сама часто встречающиеся слова, чтобы удалить м.р-н,...
    phrases = [a.split() for a in df_regions['name_area']]
    words = list(chain.from_iterable(phrases))
    stop_words = [a[0] for a in Counter(words).most_common(7)]
    only_cities = [[c for c in b if c not in stop_words] for b in phrases]
    cities_new = (list(map(' '.join, only_cities)))
    df_regions.insert(3, "cities_name", cities_new)
    # Сформируем справочник регионов
    df_region_guide = df_regions[['region_code', 'region_name', 'cities_name']]
    df_region_guide = df_region_guide.drop_duplicates()
    df_region_guide.to_excel('region_guide.xlsx', index=False)
    return df_region_guide