from selenium.webdriver.common.by import By
from tqdm.auto import tqdm
from datetime import date
from fuzzywuzzy import fuzz
from general_functions import *
import re


def Tele2_get_one_card_information(text, today_date, region, company, link):
    """Tele2 Мобильная связь: Получает всю необходимую информацию о тарифах с одной карточки"""
    # Название тарифа
    tariff_name = text.split('\n')[0]
    # Цены на тарифы
    tariff_prices = re.findall(r'[0-9]+₽', text)
    tariff_prices = int(tariff_prices[0].replace('₽', ''))
    # Скорость интернета
    internet_speed = 'no_inf'
    # Количество гигабайт
    number_of_gb = re.findall(r'([0-9]+\n\+[0-9]+\nГБ)|([0-9]+\nГБ)', text)
    number_of_gb = [a[0] if a[0] != '' else a[1] for a in number_of_gb]
    number_of_gb = [sum([int(b) for b in (re.findall(r'([0-9]+)', a))]) if len(re.findall(r'([0-9]+)', a)) == 2 else
                    [int(b) for b in re.findall(r'([0-9]+)', a)][0] for a in number_of_gb][0]
    # Минуты для телефонных разговоров
    minutes_for_phone_calls = re.findall(r'([0-9]+\nминут на остальные номера России)|([0-9]+\nминут на [А-Яа-я ]+)',
                                         text)
    minutes_for_phone_calls = [int(re.findall(r'[0-9]+', b)[0]) for b in
                               [a[0] if a[0] != '' else a[1] for a in minutes_for_phone_calls]][0]
    city = 'no_inf'
    type_of_service = 'Мобильная связь'
    one_hundred_internet_speed = 'no_inf'
    cost_per_one_min = tariff_prices / minutes_for_phone_calls
    # Формироваие дата фрейма
    df_one_card = pd.DataFrame(
        columns=['Дата', 'Регион', 'Город', 'Компания', 'Тип услуги', 'Название_тарифа', 'Цена_на_тариф',
                 'Скорость_интернета_Мбит/с', 'Стоимость за 1 Мбит/с', 'Количество_ГБ',
                 'Количество_минут', 'Стоимость за 1 мин', 'Ссылка'])
    df_one_card.loc[0] = [today_date, region, city, company, type_of_service, tariff_name, tariff_prices,
                          internet_speed, one_hundred_internet_speed, number_of_gb,
                          minutes_for_phone_calls, cost_per_one_min, link]
    return df_one_card


def Tele2_get_one_region_information(driver, today_date, region, company, link):
    """Tele2 Мобильная связь: собирает всю информацию, со всех карточек,
    о тарифах про каждый из вариантов"""
    cards_premium = driver.find_elements(By.XPATH, "//div[@class='tariff-card tariff-card_inline tariff-card_premium']")
    cards = driver.find_elements(By.XPATH, "//div[@class='tariff-card tariff-card_inline']")
    df_region = pd.DataFrame()
    for card in cards + cards_premium:
        try:
            text = card.text
            df = Tele2_get_one_card_information(text, today_date, region, company, link=link)
            df_region = pd.concat([df_region, df])
        except IndexError:
            continue
    df_region.reset_index(drop=True, inplace=True)
    return df_region


def Tele2(driver, update_links=False):
    """ Tele2 Мобильная связь: позволяет собрать данные о тарифных планах для всех доступных регионов """
    today_date = date.today()
    if update_links:
        tele2_get_regions_links(driver)
    # Получаем последний файл со всеми ссылками на страницы городов
    df_regions_links = get_last_file(path='Result/Tele2/Link_list')
    # Компания
    company = 'Tele2'
    # Переходим на сайт
    url = 'https://msk.tele2.ru/tariffs'
    driver.get(url)
    df_Tele2 = pd.DataFrame()
    for index, row in tqdm(df_regions_links.iterrows(), total=df_regions_links.shape[0], desc='Tele2_parsing'):
        try:
            driver.get(row['url'])
            length_value = random.choice([7, 8, 9, 10])
            scrol(driver, n_down=length_value, n_up=length_value, always_up=True)
            region = row['region']
            time.sleep(0.5)
            df_region = Tele2_get_one_region_information(driver, today_date, region, company, link=row['url'])
            df_Tele2 = pd.concat([df_Tele2, df_region])
        except:
            try:
                driver.get(row['url'])
                length_value = random.choice([4, 5, 6, 7, 8, 9, 10])
                scrol(driver, n_down=length_value, n_up=length_value, always_up=True)
                region = row['region']
                df_region = Tele2_get_one_region_information(driver, today_date, region, company, link=row['url'])
                df_Tele2 = pd.concat([df_Tele2, df_region])
            except:
                print(f"Теле2 Пропущен регион: {row['region']}")
                continue
    df_Tele2.reset_index(drop=True, inplace=True)
    df_Tele2.to_excel(f'Result/Tele2/Tele2_{today_date}.xlsx')
    return df_Tele2


def Tele2_final(df_Tele2):
    """Теле2 мобильная связь: функция позволяет усреднить показатели по регионам"""
    good_index = []
    for region in df_Tele2['Регион'].unique():
        df = df_Tele2[df_Tele2['Регион'] == region].copy()
        df['index'] = df['Цена_на_тариф'] * df['Количество_ГБ']
        good_index.append(df.sort_values(by='index').index[0])
    df_Tele2 = df_Tele2.loc[good_index]
    df_Tele2.reset_index(drop=True, inplace=True)
    df_Tele2_final = df_Tele2[['Дата', 'Регион', 'Компания', 'Тип услуги',
                                    'Цена_на_тариф', 'Скорость_интернета_Мбит/с', 'Стоимость за 1 Мбит/с',
                                    'Количество_ГБ', 'Количество_минут', 'Стоимость за 1 мин']]
    return df_Tele2_final


#########################################################################################################################
#########################################################################################################################


def tele2_get_right_region_names(df_links):
    """Функция позволяет преобразовать названия регионов нужный формат"""
    df_region_guide = pd.read_excel('region_guide.xlsx')
    # Разграничим Санкт-Петербург и Ленинградская область.
    # Определяем нужную нам строку и сохраняем ее
    line = list(df_links[df_links['region'] == 'Санкт-Петербург и Ленинградская область'].iloc[0])[1:]
    # Добавляем две новые строки в конец с разбитыми названиями
    df_links.loc[df_links.shape[0]] = ['Санкт-Петербург'] + line
    df_links.loc[df_links.shape[0]] = ['Ленинградская область'] + line
    # Удаляем старую строку
    df_links.drop(index=int(df_links[df_links['region'] == 'Санкт-Петербург и Ленинградская область'].index.values),
                  inplace=True)
    df_links.reset_index(drop=True, inplace=True)

    # Разграничим Москву и Московскую область.
    # Определяем нужную нам строку и сохраняем ее
    line = list(df_links[df_links['region'] == 'Москва и область'].iloc[0])[1:]
    # Добавляем две новые строки в конец с разбитыми названиями
    df_links.loc[df_links.shape[0]] = ['Москва'] + line
    df_links.loc[df_links.shape[0]] = ['Московская область'] + line
    # Удаляем старую строку
    df_links.drop(index=int(df_links[df_links['region'] == 'Москва и область'].index.values), inplace=True)
    df_links.reset_index(drop=True, inplace=True)

    # Разграничим Краснодарский край и Республика Адыгея.
    # Определяем нужную нам строку и сохраняем ее
    line = list(df_links[df_links['region'] == 'Краснодарский край и Республика Адыгея'].iloc[0])[1:]
    # Добавляем две новые строки в конец с разбитыми названиями
    df_links.loc[df_links.shape[0]] = ['Краснодарский край'] + line
    df_links.loc[df_links.shape[0]] = ['Республика Адыгея'] + line
    # Удаляем старую строку
    df_links.drop(index=int(df_links[df_links['region'] == 'Краснодарский край и Республика Адыгея'].index.values),
                  inplace=True)
    df_links.reset_index(drop=True, inplace=True)

    # Разграничим Республика Хакасия и Республика Тыва.
    # Определяем нужную нам строку и сохраняем ее
    line = list(df_links[df_links['region'] == 'Республика Хакасия и Республика Тыва'].iloc[0])[1:]
    # Добавляем две новые строки в конец с разбитыми названиями
    df_links.loc[df_links.shape[0]] = ['Республика Хакасия'] + line
    df_links.loc[df_links.shape[0]] = ['Республика Тыва'] + line
    # Удаляем старую строку
    df_links.drop(index=int(df_links[df_links['region'] == 'Республика Хакасия и Республика Тыва'].index.values),
                  inplace=True)
    df_links.reset_index(drop=True, inplace=True)

    region_list = []
    for region in df_links['region']:
        rotation = [a for a in df_region_guide['region_name'].unique() if fuzz.ratio(
            ' '.join([c for c in region.split() if c not in ['край', 'Край', 'Республика', 'республика']]),
            ' '.join([c for c in a.split() if c not in ['край', 'Край', 'Республика', 'республика']])) > 95]
        if len(rotation) == 1:
            region_list.append(rotation[0])
        elif region == 'Красноярский край (кроме Норильска)':
            region_list.append('Красноярский край')
        elif region == 'Красноярский край (Норильск)':
            region_list.append('Красноярский край')
        elif region == 'Ханты-Мансийский АО—Югра':
            region_list.append('Ханты-Мансийский АО')
        else:
            print(region)
            region_list.append(np.nan)
    df_links['region'] = region_list
    return df_links


def tele2_get_regions_links(driver):
    """Теле2 мобильная связь: позволяет получить ссылки на все регионы """
    # Компания
    company = 'Tele2'
    city = 'no_inf'
    today_date = date.today()
    # Переходим на сайт
    url = 'https://msk.tele2.ru/tariffs'
    driver.get(url)
    test_page(driver, delay=5,
              element=(By.XPATH, "//button[@class='unstyled-button header-navbar-choose-region-button']"))
    # Открываем панель выбора региона
    driver.find_element(By.XPATH, "//button[@class='unstyled-button header-navbar-choose-region-button']").click()

    # Получаем HTML страницы
    test_page(driver, delay=3, element=(By.ID, 'regionSearch'))
    link_text = driver.find_element(By.ID, 'regionSearch').get_attribute('innerHTML')
    links_text = re.findall(r'<li>(.*?)/li>+', link_text)
    # Составляем словарь из ссылок и названий регионов
    links_voc = dict(
        zip([re.findall(r'>(.*?)</a>+', a)[0] for a in links_text],
            [re.findall(r'"(.*?)"+', a)[0] for a in links_text]))
    # Формируем общий дата фрейм
    df = pd.DataFrame(list(links_voc.items()), columns=['region', 'url'])
    df.insert(1, 'city', city)
    df['date'] = today_date
    df['company'] = company
    df.reset_index(drop=True, inplace=True)
    df_Tele2 = tele2_get_right_region_names(df_links=df)
    df_Tele2.to_excel(f'Result/Tele2/Link_list/Tele2_links_{today_date}.xlsx', index=False)
    return df_Tele2
