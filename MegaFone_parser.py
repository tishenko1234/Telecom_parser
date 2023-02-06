from selenium.webdriver.common.by import By
from datetime import date
from selenium.webdriver.common.action_chains import ActionChains
from fuzzywuzzy import fuzz
from general_functions import *
from tqdm.auto import tqdm
import re


def MegaFon_get_one_card_information(card_text, today_date, region, company, link):
    """МегаФон мобильная связь: функция позволяет собрать всю информацию с одной карточки"""
    tariff_name = re.split(r'\n', card_text)[1]
    tariff_prices = int(re.findall(r'\d+ ₽+', card_text)[0].replace(' ₽', ''))
    internet_speed = 'no_inf'
    number_of_gb = int(re.findall(r'\n\d+ ГБ', card_text)[0].replace('\n', '').replace(' ГБ', ''))
    minutes_for_phone_calls = int(re.findall(r'\n\d+ минут', card_text)[0].replace('\n', '').replace(' минут', ''))
    city = 'no_inf'
    type_of_service = 'Мобильная связь'
    one_hundred_internet_speed = 'no_inf'
    cost_per_one_min = tariff_prices / minutes_for_phone_calls
    # Формирование дата фрейма
    df_one_card = pd.DataFrame(
        columns=['Дата', 'Регион', 'Город', 'Компания', 'Тип услуги', 'Название_тарифа', 'Цена_на_тариф',
                 'Скорость_интернета_Мбит/с', 'Стоимость за 1 Мбит/с', 'Количество_ГБ',
                 'Количество_минут', 'Стоимость за 1 мин', 'Ссылка'])
    df_one_card.loc[0] = [today_date, region, city, company, type_of_service, tariff_name, tariff_prices,
                          internet_speed, one_hundred_internet_speed, number_of_gb,
                          minutes_for_phone_calls, cost_per_one_min, link]
    return df_one_card


def MegaFon_get_one_region_information(driver, today_date, region, company, link):
    """МегаФон мобильная связь: функция позволяет собрать всю информацию об одном регионе"""
    all_cards = driver.find_elements(By.XPATH, "//div[@class='tariffs-card-v3 gtm-tariff-card-component']")
    all_cards = [a.text for a in all_cards if a.text != '']
    df_region = pd.DataFrame()
    for card in all_cards:
        try:
            df = MegaFon_get_one_card_information(card_text=card, today_date=today_date, region=region, company=company,
                                                  link=link)
            df_region = pd.concat([df_region, df])
        except:
            continue
    df_region.reset_index(drop=True, inplace=True)
    return df_region


def MegaFone(driver, update_links=False):
    """МегаФон мобильная связь: функция позволяет собрать всю информацию обо всех регионов"""
    if update_links:
        megaFon_get_regions_links(driver)
    # Получаем последний файл со всеми ссылками на страницы городов
    df_regions_links = get_last_file(path='''Result/MegaFon/Link_list''')

    # url = 'https://moscow.megafon.ru'
    # driver.get(url)
    today_date = date.today()
    company = 'MegaFon'
    # # Переходим на страницу с выбором регионов
    # driver.find_element(By.XPATH, "//div[@class='ch-region__trigger']").click()

    df_MegaFone = pd.DataFrame()
    for index, row in tqdm(df_regions_links.iterrows(), total=df_regions_links.shape[0], desc='MegaFone_parsing'):
        try:
            region_link = row['url']
            driver.get(region_link)
            length_value = random.choice([4, 5, 6, 7, 8, 9, 10])
            scrol(driver, n_down=length_value, n_up=length_value, always_up=True)
            ActionChains(driver).move_to_element(
                driver.find_element(By.XPATH, "//div[@class='tariffs-carousel-v3__slider']")).perform()
            region = row['region']
            df_region = MegaFon_get_one_region_information(driver, today_date, region, company, link=region_link)
            df_MegaFone = pd.concat([df_MegaFone, df_region])
        except:
            try:
                region_link = row['url']
                driver.get(region_link)
                length_value = random.choice([4, 5, 6, 7, 8, 9, 10])
                scrol(driver, n_down=length_value, n_up=length_value, always_up=True)
                region = row['region']
                df_region = MegaFon_get_one_region_information(driver, today_date, region, company, link=region_link)
                df_MegaFone = pd.concat([df_MegaFone, df_region])
            except:
                print(f"МегаФон Пропущен регион: {row['region']}")
                df_one_card = pd.DataFrame(
                    columns=['Дата', 'Регион', 'Город', 'Компания', 'Тип услуги', 'Название_тарифа', 'Цена_на_тариф',
                             'Скорость_интернета_Мбит/с', 'Стоимость за 1 Мбит/с', 'Количество_ГБ',
                             'Количество_минут', 'Стоимость за 1 мин', 'Ссылка'])
                city = None
                type_of_service = "Мобильная связь"
                tariff_name = None
                tariff_prices = None
                internet_speed = None
                one_hundred_internet_speed = None
                number_of_gb = None
                minutes_for_phone_calls = None
                cost_per_one_min = None
                df_one_card.loc[0] = [today_date, row['region'], city, company, type_of_service, tariff_name,
                                      tariff_prices,
                                      internet_speed, one_hundred_internet_speed, number_of_gb,
                                      minutes_for_phone_calls, cost_per_one_min, row['url']]
                df_MegaFone = pd.concat([df_MegaFone, df_one_card])
                continue
    df_MegaFone.reset_index(drop=True, inplace=True)
    df_MegaFone.to_excel(f'Result/MegaFon/MegaFone_{today_date}.xlsx')
    return df_MegaFone


def MegaFone_final(df_MegaFone):
    """МегаФон мобильная связь: функция позволяет усреднить показатели по регионам"""
    good_index = []
    for region in df_MegaFone['Регион'].unique():
        df = df_MegaFone[df_MegaFone['Регион'] == region].copy()
        df['index'] = df['Цена_на_тариф'] * df['Количество_ГБ']
        good_index.append(df.sort_values(by='index').index[0])
    df_MegaFone = df_MegaFone.loc[good_index]
    df_MegaFone.reset_index(drop=True, inplace=True)
    df_MegaFone_final = df_MegaFone[['Дата', 'Регион', 'Компания', 'Тип услуги',
                                     'Цена_на_тариф', 'Скорость_интернета_Мбит/с', 'Стоимость за 1 Мбит/с',
                                     'Количество_ГБ', 'Количество_минут', 'Стоимость за 1 мин']]
    return df_MegaFone_final


#########################################################################################################################
#########################################################################################################################

def megafone_get_right_region_names(df_links):
    """Функция позволяет преобразовать названия регионов нужный формат"""
    df_region_guide = pd.read_excel('region_guide.xlsx')
    # Разграничим Москву и Московскую область.
    # Определяем нужную нам строку и сохраняем ее
    line = list(df_links[df_links['region'] == 'Москва и область'].iloc[0])[1:]
    # Добавляем две новые строки в конец с разбитыми названиями
    df_links.loc[df_links.shape[0]] = ['Москва'] + line
    df_links.loc[df_links.shape[0]] = ['Московская область'] + line
    # Удаляем старую строку
    df_links.drop(index=int(df_links[df_links['region'] == 'Москва и область'].index.values), inplace=True)
    df_links.reset_index(drop=True, inplace=True)
    # Разграничим Санкт-Петербург и Ленинградская область.
    # Определяем нужную нам строку и сохраняем ее
    line = list(df_links[df_links['region'] == 'Санкт-Петербург и область'].iloc[0])[1:]
    # Добавляем две новые строки в конец с разбитыми названиями
    df_links.loc[df_links.shape[0]] = ['Санкт-Петербург'] + line
    df_links.loc[df_links.shape[0]] = ['Ленинградская область'] + line
    # Удаляем старую строку
    df_links.drop(index=int(df_links[df_links['region'] == 'Санкт-Петербург и область'].index.values), inplace=True)
    df_links.reset_index(drop=True, inplace=True)

    # Заменим названия регионов на верные из справочника
    region_list = []
    for region in df_links['region']:
        rotation = [a for a in df_region_guide['region_name'].unique() if fuzz.ratio(
            ' '.join([c for c in region.split() if c not in ['край', 'Край', 'Республика', 'республика', 'Югра', '-']]),
            ' '.join(
                [c for c in a.split() if c not in ['край', 'Край', 'Республика', 'республика', 'Югра', '-']])) > 95]
        if len(rotation) == 1:
            region_list.append(rotation[0])
        elif region == 'Н.Новгород и область':
            region_list.append('Нижегородская область')
        elif region == 'Норильск и Таймырский МР':
            region_list.append('Красноярский край')
        elif region == 'Еврейская автономная область':
            region_list.append('Еврейская АО')
        elif region == 'Республика Кабардино-Балкария':
            region_list.append('Кабардино-Балкарская республика')
        elif region == 'Республика Карачаево-Черкесия':
            region_list.append('Карачаево-Черкесская республика')
        elif region == 'Республика Северная Осетия':
            region_list.append('Республика Северная Осетия – Алания')
        else:
            print(region)
            region_list.append(np.nan)
    df_links['region'] = region_list
    return df_links


def megaFon_get_regions_links(driver):
    """МегаФон мобильная связь: позволяет получить ссылки на все регионы """
    company = 'MegaFon'
    city = 'no_inf'
    url = 'https://moscow.megafon.ru'
    today_date = date.today()
    driver.get(url)
    driver.refresh()
    # Переходим на страницу с выбором регионов
    driver.find_element(By.XPATH, "//div[@class='ch-region__trigger']").click()
    # Собираем названия доступных регионов
    source_element = driver.find_element(By.XPATH, "//div[@class='scrollbar']")  # сам скролер
    all_region_names = pd.DataFrame()
    for i in [0, 100, 100, 100, 100]:
        # прокручиваем
        ActionChains(driver).click_and_hold(source_element).move_by_offset(0, i).perform()
        time.sleep(2)
        links = driver.find_elements(By.XPATH, "//a[@class='ch-region-popup__link']")
        good_links = [a for a in links if a.text != ""]
        region_names_part = [a.text for a in good_links]
        region_links_part = [a.get_attribute('href') for a in good_links]
        df = pd.DataFrame({'region': region_names_part,
                           'url': region_links_part})
        df.insert(1, 'city', city)
        df['date'] = today_date
        df['company'] = company
        all_region_names = pd.concat([all_region_names, df])
    ActionChains(driver).reset_actions()
    all_region_names.drop_duplicates(subset='url', inplace=True)
    all_region_names.reset_index(drop=True, inplace=True)
    all_region_names = megafone_get_right_region_names(all_region_names)
    all_region_names.to_excel(f'Result/MegaFon/Link_list/MegaFone_links_{today_date}.xlsx', index=False)
    return all_region_names
