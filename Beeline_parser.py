from selenium.webdriver.common.by import By
from tqdm.auto import tqdm
from datetime import date
from fuzzywuzzy import fuzz
from general_functions import *
import re

def Beeline_get_one_card_information(card_text, today_date, region, company,link):
    """Билайн мобильная связь: функция позволяет собрать всю информацию с одной карточки"""
    if re.split(r'\n', card_text)[0] == '':
        tariff_name = re.split(r'\n', card_text)[1]
    else:
        tariff_name = re.split(r'\n', card_text)[0]
    tariff_prices = int(re.findall(r'\n\d+\n₽', card_text)[0].replace('\n₽', '').replace('\n', ''))
    internet_speed = 'no_inf'
    number_of_gb = int(re.findall(r'\n\d+\nГБ', card_text)[0].replace('\nГБ', '').replace('\n', ''))
    minutes_for_phone_calls = int(re.findall(r'\n\d+\nмин', card_text)[0].replace('\n', '').replace('мин', ''))
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


def Beeline_get_one_region_information(driver, today_date, region, company,link):
    """Билайн мобильная связь: функция позволяет собрать всю информацию об одном регионе"""
    full_text = driver.find_element(By.XPATH, "//div[@class='pAbvw9']").text
    all_cards = [a for a in re.split(r'\nНастроить', full_text) if len(a) > 0]
    df_region = pd.DataFrame()
    for card in all_cards:
        df = Beeline_get_one_card_information(card_text=card, today_date=today_date, region=region, company=company,
                                              link=link)
        df_region = pd.concat([df_region, df])
    df_region.reset_index(drop=True, inplace=True)
    return df_region


def Beeline(driver, update_links=False):
    """Билайн мобильная связь: функция позволяет собрать всю информацию обо всех регионов"""
    if update_links:
        beeline_get_regions_links(driver)
    # Получаем последний файл со всеми ссылками на страницы городов
    df_regions_links = get_last_file(path='Result/Beeline/Link_list')

    url = 'https://nizhegorodskaya-obl.beeline.ru/customers/products/mobile/tariffs/'
    driver.get(url)
    today_date = date.today()
    company = 'Beeline'
    df_Beeline = pd.DataFrame()
    for index, row in tqdm(df_regions_links.iterrows(), total=df_regions_links.shape[0], desc='Beeline_parsing'):
        try:
            driver.get(row['url'])
            length_value = random.choice([7, 8, 9, 10])
            scrol(driver, n_down=length_value, n_up=length_value, always_up=True)
            region = row['region']
            time.sleep(0.5)
            df_region = Beeline_get_one_region_information(driver, today_date, region, company,link= row['url'])
            df_Beeline = pd.concat([df_Beeline, df_region])
        except:
            try:
                driver.get(row['url'])
                length_value = random.choice([4, 5, 6, 7, 8, 9, 10])
                scrol(driver, n_down=length_value, n_up=length_value, always_up=True)
                region = row['region']
                df_region = Beeline_get_one_region_information(driver, today_date, region, company,link= row['url'])
                df_Beeline = pd.concat([df_Beeline, df_region])
            except:
                print(f"Билайн Пропущен регион: {row['region']}")
                continue
    df_Beeline.reset_index(drop=True,inplace=True)
    df_Beeline.to_excel(f'Result/Beeline/Beeline_{today_date}.xlsx')
    return df_Beeline

def Beeline_final(df_Beeline):
    """Билайн мобильная связь: функция позволяет усреднить показатели по регионам"""
    good_index = []
    for region in df_Beeline['Регион'].unique():
        df = df_Beeline[df_Beeline['Регион'] == region].copy()
        df['index'] = df['Цена_на_тариф']*df['Количество_ГБ']
        good_index.append(df.sort_values(by = 'index').index[0])
    df_Beeline = df_Beeline.loc[good_index]
    df_Beeline.reset_index(drop=True,inplace=True)
    df_Beeline_final = df_Beeline[['Дата', 'Регион', 'Компания', 'Тип услуги',
                                    'Цена_на_тариф', 'Скорость_интернета_Мбит/с', 'Стоимость за 1 Мбит/с',
                                    'Количество_ГБ', 'Количество_минут', 'Стоимость за 1 мин']]
    return df_Beeline_final
#########################################################################################################################
#########################################################################################################################

def beeline_get_right_region_names(df_links):
    """Функция позволяет преобразовать названия регионов нужный формат"""
    df_region_guide = pd.read_excel('region_guide.xlsx')
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

    region_list = []
    for region in tqdm(df_links['region']):
        rotation = [a for a in df_region_guide['region_name'].unique() if fuzz.ratio(
            ' '.join([c for c in region.split() if c not in ['край', 'Край', 'Республика', 'республика']]),
            ' '.join([c for c in a.split() if c not in ['край', 'Край', 'Республика', 'республика']])) > 95]
        if len(rotation) == 1:
            region_list.append(rotation[0])
        elif region == 'Республика Северная Осетия':
            region_list.append('Республика Северная Осетия – Алания')
        elif region == 'Ханты-Мансийский автономный округ':
            region_list.append('Ханты-Мансийский АО')
        elif region == 'Ямало-Ненецкий автономный округ':
            region_list.append('Ямало-Ненецкий АО')
        else:
            region_list.append(np.nan)
    df_Beeline = df_links.copy()
    df_Beeline.insert(0, "Регионы_новые", region_list)
    df_links = df_Beeline[df_Beeline['Регионы_новые'].isna() == False].copy()
    df_links.reset_index(drop=True, inplace=True)
    df_links.drop(columns=["region"], inplace=True)
    df_links.rename(columns = {'Регионы_новые':"region"},inplace=True)

    return df_links


def beeline_get_regions_links(driver):
    """Билайн мобильная связь: позволяет получить ссылки на все регионы """
    url = 'https://nizhegorodskaya-obl.beeline.ru/customers/products/mobile/tariffs/'
    driver.get(url)
    today_date = date.today()
    company = 'Beeline'
    city = 'no_inf'
    # Прокручиваем страницу вверх
    driver.execute_script(f"scrollBy(0,-1000)")
    # переходим на страницу с выбором регионов
    driver.find_element(By.XPATH, "//button[@id='toggleButton-regions-desktop']").click()
    # Получаем ссылки на все имеющиеся регионы
    test_page(driver, delay=3, element=(By.XPATH, "//a[@class='N_vrqM']"))
    all_inf = driver.find_elements(By.XPATH, "//a[@class='N_vrqM']")
    all_links = [a.get_attribute('href') for a in all_inf]
    all_links = [a + 'customers/products/mobile/tariffs/' for a in all_links]
    # Получаем названия всех имеющихся регионов
    all_regions = [a.text for a in all_inf]
    # Формируем общий дата фрейм
    df = pd.DataFrame({'region': all_regions,
                       'url': all_links})
    df.insert(1, 'city', city)
    df['date'] = today_date
    df['company'] = company
    df1 = beeline_get_right_region_names(df_links=df)
    df1.to_excel(f'Result/Beeline/Link_list/Beeline_links_{today_date}.xlsx', index=False)
    return df1
