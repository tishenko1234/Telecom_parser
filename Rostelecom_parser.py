from selenium.webdriver.common.by import By
from tqdm.auto import tqdm
from datetime import date
from fuzzywuzzy import fuzz
from general_functions import *
import re


def Rostelecom_int_get_one_card_information(text, today_date, region, company, city, link):
    """Ростелеком домашний интернет: Получает всю необходимую информацию о тарифах с одной карточки"""
    if len(re.findall(r'дней в подарок', text)) == 0:
        gift = 0
    else:
        gift = 1
    # Название тарифа
    if text.split('\n')[0] == '':
        tariff_name = text.split('\n')[1]
    else:
        tariff_name = text.split('\n')[0]
    # Цены на тарифы
    if gift == 0:
        tariff_prices = re.findall(r'\n[0-9 ]+\nруб', text)
        tariff_prices = int(tariff_prices[0].replace('\nруб', '').replace('\n', '').replace(' ', ''))
        if len(re.findall(r'\d', str(tariff_prices))) > 3:
            if re.findall(r'\d', str(tariff_prices))[2] == 0:
                tariff_prices = int(''.join(re.findall(r'\d', str(tariff_prices))[-3:]))
            else:
                tariff_prices = int(''.join(re.findall(r'\d', str(tariff_prices))[-4:]))
        else:
            tariff_prices = tariff_prices
    else:
        tariff_prices = "АКЦИЯ"
    # Скорость интернета
    internet_speed = re.findall(r'[0-9]+ Мбит/с', text)
    internet_speed = int(internet_speed[0].replace(' Мбит/с', ''))
    # Количество гигабайт
    number_of_gb = 'no_inf'
    # Минуты для телефонных разговоров
    minutes_for_phone_calls = 'no_inf'
    type_of_service = 'Домашний интернет'
    one_hundred_internet_speed = tariff_prices / internet_speed
    cost_per_one_min = 'no_inf'
    # Формироваие дата фрейма
    df_one_card = pd.DataFrame(
        columns=['Дата', 'Регион', 'Город', 'Компания', 'Тип услуги', 'Название_тарифа', 'Цена_на_тариф',
                 'Скорость_интернета_Мбит/с', 'Стоимость за 1 Мбит/с', 'Количество_ГБ',
                 'Количество_минут', 'Стоимость за 1 мин', 'Ссылка'])
    df_one_card.loc[0] = [today_date, region, city, company, type_of_service, tariff_name, tariff_prices,
                          internet_speed, one_hundred_internet_speed, number_of_gb,
                          minutes_for_phone_calls, cost_per_one_min, link]
    return df_one_card


def Rostelecom_int_get_one_region_information(driver, today_date, region, company, city, link):
    """Ростелеком домашний интернет: позволяет собрать информацию
     о тарифах для домашнего интернета для одного региона"""
    # Получение совокупного текста карточек
    full_text = driver.find_element(By.XPATH, "//div[@class='rt-container td-sp-h-none relative']").text
    cards_text = re.split(r'Настроить тариф|Подробнее о тарифе', full_text)
    # Оставляем только карточки в которых нет доп услуг (только подключение к домашнему интернету)
    good_cards_text = [a for a in cards_text if len(re.findall(r'Облачный|Игровой', a)) == 0 and len(a) > 0]
    df_region = pd.DataFrame()
    for text in good_cards_text:
        try:
            df = Rostelecom_int_get_one_card_information(text, today_date, region, company, city, link)
            df_region = pd.concat([df_region, df])
        except:
            continue
    df_region.reset_index(drop=True, inplace=True)
    return df_region


def Rostelecom(driver, update_links=False):
    """Ростелеком домашний интернет: Позволяет собрать данные со всего сайта."""
    if update_links:
        rostelecom_get_regions_links(driver)
    # Получаем последний файл со всеми ссылками на страницы городов
    df_regions_links = get_last_file(path='Result/Rostelecom/Link_list')
    company = 'Rostelecom'
    today_date = date.today()
    url = 'https://msk.rt.ru/homeinternet'
    driver.get(url)
    # Собираем данные
    df_Rostelecom = pd.DataFrame()
    for index, row in tqdm(df_regions_links.iterrows(), total=df_regions_links.shape[0], desc='Rostelecom_parsing'):
        try:
            link = row['url']
            region = row['region']
            city = row['city']
            driver.get(link)
            # Прокручиваем страницу
            length_value = random.choice([4, 5, 6, 7, 8, 9, 10])
            scrol(driver, n_down=length_value, n_up=length_value, always_up=True)
            df_region = Rostelecom_int_get_one_region_information(driver, today_date, region, company, city, link)
            df_Rostelecom = pd.concat([df_Rostelecom, df_region])
            df_Rostelecom.reset_index(drop=True, inplace=True)
        except:
            try:
                link = row['url']
                region = row['region']
                city = row['city']
                driver.get(link)
                # Прокручиваем страницу
                length_value = random.choice([4, 5, 6, 7, 8, 9, 10])
                scrol(driver, n_down=length_value, n_up=length_value, always_up=True)
                df_region = Rostelecom_int_get_one_region_information(driver, today_date, region, company, city, link)
                df_Rostelecom = pd.concat([df_Rostelecom, df_region])
                df_Rostelecom.reset_index(drop=True, inplace=True)
            except:
                print(f"Ростелеком Пропущен регион: {row['region']}")
                continue
    df_Rostelecom.to_excel(f'Result/Rostelecom/Rostelecom_{today_date}.xlsx')
    return df_Rostelecom


def Rostelecom_final(df_Rostelecom):
    """Ростелеком домашний интернет: функция позволяет усреднить показатели по регионам"""
    good_index = []
    for region in df_Rostelecom['Регион'].unique():
        df = df_Rostelecom[df_Rostelecom['Регион'] == region].copy()
        good_index.append(df.sort_values(by='Цена_на_тариф').index[0])
    df_Rostelecom = df_Rostelecom.loc[good_index]
    df_Rostelecom.reset_index(drop=True, inplace=True)
    df_Rostelecom_final = df_Rostelecom[['Дата', 'Регион', 'Компания', 'Тип услуги',
                                    'Цена_на_тариф', 'Скорость_интернета_Мбит/с', 'Стоимость за 1 Мбит/с',
                                    'Количество_ГБ', 'Количество_минут', 'Стоимость за 1 мин']]
    return df_Rostelecom_final


#########################################################################################################################
#########################################################################################################################
def rostelecom_get_right_region_names(df_links):
    """Функция позволяет преобразовать названия регионов нужный формат"""
    df_region_guide = pd.read_excel('region_guide.xlsx')

    # Заменим названия регионов на верные из справочника
    region_list = []
    for region in df_links['region']:
        rotation = [a for a in df_region_guide['region_name'].unique() if fuzz.ratio(
            ' '.join([c for c in region.split() if
                      c not in ['край', 'Край', 'Республика', 'республика', 'Югра', '-', 'город']]),
            ' '.join(
                [c for c in a.split() if
                 c not in ['край', 'Край', 'Республика', 'республика', 'Югра', '-', 'город']])) > 95]
        if len(rotation) == 1:
            region_list.append(rotation[0])
        elif region == 'Еврейская автономная область':
            region_list.append('Еврейская АО')
        elif region == 'Ханты-Мансийский Автономный округ - Югра автономный округ':
            region_list.append('Ханты-Мансийский АО')
        elif region == 'Ненецкий автономный округ':
            region_list.append('Ненецкий АО')
        elif region == 'Ненецкий автономный округ':
            region_list.append('Ненецкий АО')
        elif region == 'Саха /Якутия/ Республика':
            region_list.append('Республика Саха (Якутия)')
        elif region == 'Чукотский автономный округ':
            region_list.append('Чукотский АО')
        elif region == 'Кемеровская область-Кузбасс область':
            region_list.append('Кемеровская область')
        elif region == 'Ямало-Ненецкий автономный округ':
            region_list.append('Ямало-Ненецкий АО')
        else:
            print(region)
    df_links['region'] = region_list
    return df_links


def rostelecom_get_regions_links(driver):
    """Ростелеком Интернет: позволяет получить ссылки на все регионы"""
    today_date = date.today()
    company = 'Rostelecom'
    url = 'https://msk.rt.ru/homeinternet'
    driver.get(url)
    # Открываем страницу для выбора региона
    driver.find_element(By.XPATH, "//a[@class='nav__change-region change-region']").click()
    time.sleep(2)
    # Получаем список всех регионов
    all_region_obj = driver.find_elements(By.XPATH, "//span[@class='b-regions__group-expand']")
    # Закрываем вкладку
    driver.find_element(By.XPATH, "//a[@class='header__section-close']").click()
    time.sleep(1)
    all_region_names = pd.DataFrame()
    region_mistake = 'Пусто'
    for i in range(len(all_region_obj)):
        try:
            # Открываем страницу для выбора региона
            time.sleep(2)
            try:
                driver.find_element(By.XPATH, "//a[@class='nav__change-region change-region']").text
            except:
                scrol(driver, n_down=5, n_up=5, always_up=True)
                time.sleep(1)
            driver.find_element(By.XPATH, "//a[@class='nav__change-region change-region']").click()
            time.sleep(2)
            # Получаем список всех регионов
            all_region_obj = driver.find_elements(By.XPATH, "//span[@class='b-regions__group-expand']")
            region = all_region_obj[i].text
            try:
                region_mistake = all_region_obj[i + 1].text
            except:
                region_mistake = all_region_obj[i].text
                # Нажимаем на регион
            all_region_obj[i].click()
            time.sleep(2)
            # Определяем объект отвечающий за название города
            if len(driver.find_elements(By.XPATH, "//span[@class='b-regions__change-region']")) == 1:
                city_obj = driver.find_element(By.XPATH, "//span[@class='b-regions__change-region']")
            else:
                city_obj = driver.find_element(By.XPATH, "//span[@class='b-regions__change-region is-capital']")
            city = city_obj.text
            city_obj.click()
            url = driver.current_url
            df = pd.DataFrame({'region': [region],
                               'city': [city],
                               'url': [url],
                               'date': [today_date],
                               'company': [company]})
            all_region_names = pd.concat([all_region_names, df])
        except:
            try:
                driver.get(list(all_region_names['url'])[-1])
                # Открываем страницу для выбора региона
                time.sleep(2)
                try:
                    driver.find_element(By.XPATH, "//a[@class='nav__change-region change-region']").text
                except:
                    scrol(driver, n_down=5, n_up=5, always_up=True)
                    time.sleep(1)
                driver.find_element(By.XPATH, "//a[@class='nav__change-region change-region']").click()
                time.sleep(2)
                # Получаем список всех регионов
                all_region_obj = driver.find_elements(By.XPATH, "//span[@class='b-regions__group-expand']")
                region = all_region_obj[i].text
                # Нажимаем на регион
                all_region_obj[i].click()
                time.sleep(2)
                # Определяем объект отвечающий за название города
                if len(driver.find_elements(By.XPATH, "//span[@class='b-regions__change-region']")) == 1:
                    city_obj = driver.find_element(By.XPATH, "//span[@class='b-regions__change-region']")
                else:
                    city_obj = driver.find_element(By.XPATH, "//span[@class='b-regions__change-region is-capital']")
                city = city_obj.text
                city_obj.click()
                url = driver.current_url
                df = pd.DataFrame({'region': [region],
                                   'city': [city],
                                   'url': [url],
                                   'date': [today_date],
                                   'company': [company]})
                all_region_names = pd.concat([all_region_names, df])
            except:
                try:
                    driver.find_element(By.XPATH, "//a[@class='header__section-close']").click()
                    print(f"""Ростелеком - регион - {region_mistake} был пропущен""")
                except:
                    print(f"""Ростелеком - регион - {region_mistake} был пропущен""")
    all_region_names.reset_index(drop=True, inplace=True)
    all_region_names = rostelecom_get_right_region_names(df_links=all_region_names)
    all_region_names.to_excel(f'Result/Rostelecom/Link_list/Rostelecom_links_{today_date}.xlsx')
    return all_region_names
