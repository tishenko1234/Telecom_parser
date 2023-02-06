from selenium.webdriver.common.by import By
from tqdm.auto import tqdm
from datetime import date
from selenium.webdriver.common.action_chains import ActionChains
from fuzzywuzzy import fuzz
from general_functions import *
import re

def MTS_get_one_card_information(card_text, today_date, region, city, company, link):
    """МТС мобильная связь: функция позволяет собрать всю информацию с одной карточки"""
    type_of_service = 'Мобильная связь'
    tariff_name = re.split(r'\n', card_text)[0]
    if len(re.findall(r'КЕШБЭК', tariff_name)) != 0:
        tariff_name = re.split(r'\n', card_text)[1]
    tariff_prices = int(re.findall(r'\d+ руб.', card_text)[0].replace(' руб.', ''))
    internet_speed = 'no_inf'
    one_hundred_internet_speed = 'no_inf'
    number_of_gb = int(re.findall(r'\d+ Гб|\d+ ГБ', card_text)[0].replace(' Гб', '').replace(' ГБ', ''))
    minutes_for_phone_calls = int(
        re.findall(r'[0-9]+', re.findall(r'\nМинуты\d+|\nМинуты и SMS\d+|\n\d+ мин', card_text)[0])[0])
    cost_per_one_min = tariff_prices / minutes_for_phone_calls
    # Формирование дата-фрейма
    df_one_card = pd.DataFrame(
        columns=['Дата', 'Регион', 'Город', 'Компания', 'Тип услуги', 'Название_тарифа', 'Цена_на_тариф',
                 'Скорость_интернета_Мбит/с', 'Стоимость за 1 Мбит/с', 'Количество_ГБ',
                 'Количество_минут', 'Стоимость за 1 мин', 'Ссылка'])
    df_one_card.loc[0] = [today_date, region, city, company, type_of_service, tariff_name, tariff_prices,
                          internet_speed, one_hundred_internet_speed, number_of_gb,
                          minutes_for_phone_calls, cost_per_one_min, link]
    return df_one_card


def MTS_get_one_region_information(driver, today_date, region, city, company, link):
    """МТС мобильная связь: функция позволяет собрать всю информацию об одном регионе"""
    all_cards = [a.text for a in driver.find_elements(By.XPATH, "//div[@class='tariff-list__item']") if
                 len(re.findall(r'ЭКСКЛЮЗИВ|руб. в день', a.text)) == 0 and len(
                     re.findall(r'\nМинуты\d+|\nМинуты и SMS\d+|\n\d+ мин|руб./мес.', a.text)) != 0]
    df_region = pd.DataFrame()
    for card in all_cards:
        try:
            df = MTS_get_one_card_information(card_text=card, today_date=today_date, region=region, city=city,
                                              company=company, link=link)
            df_region = pd.concat([df_region, df])
        except IndexError:
            continue
    df_region.reset_index(drop=True, inplace=True)
    return df_region


def MTS(driver, update_links=False):
    """МТС мобильная связь: функция позволяет собрать всю информацию обо всех регионах.
    Также можно обновить список ссылок на случай добавления новых регионов на сайте.
    Длится 47 мин (обновление ссылок) и 14 мин (парсинг)"""
    today_date = date.today()
    if update_links:
        mts_get_all_links(driver)
    # Получаем последний файл со всеми ссылками на страницы городов
    df_regions_links = get_last_file(path='Result/MTS/Link_list')
    df_MTS = pd.DataFrame()
    for index, row in tqdm(df_regions_links.iterrows(), total=df_regions_links.shape[0], desc='MTS_parsing'):
        region = row['region']
        city = row['city']
        company = 'MTS'
        link = row['url']
        driver.get(link)
        try:
            # Обнуляем все скролллеры для того, чтобы выбрать наиболее дешевый тариф
            all_scrollers = driver.find_elements(By.XPATH, "//div[@class='range-slider']")
            for scroller in all_scrollers:
                # Прокручиваем страницу до нужного нам элемента
                ActionChains(driver).move_to_element(scroller).perform()
                # Ставим тариф на минимально возможный уровень
                ActionChains(driver).click_and_hold(scroller).move_by_offset(-200, 0).perform()
                ActionChains(driver).reset_actions()
        except:
            continue
        df_region = MTS_get_one_region_information(driver, today_date=today_date, region=region, city=city,
                                                   company=company,
                                                   link=link)
        df_MTS = pd.concat([df_MTS, df_region])
    df_MTS.reset_index(drop=True, inplace=True)
    df_MTS.to_excel(f'Result/MTS/MTS_{today_date}.xlsx', index=False)
    return df_MTS


def MTS_final(df_MTS):
    """МТС мобильная связь: функция позволяет усреднить показатели по регионам"""
    good_index = []
    for region in df_MTS['Регион'].unique():
        df = df_MTS[df_MTS['Регион'] == region].copy()
        df['index'] = df['Цена_на_тариф'] * df['Количество_ГБ']
        good_index.append(df.sort_values(by='index').index[0])

    df_MTS = df_MTS.loc[good_index]
    # Усредняем по региону
    df_only_regions = pd.DataFrame()
    for region in df_MTS['Регион'].unique():
        df = df_MTS[df_MTS['Регион'] == region].copy()
        if df.shape[0] == 1:
            df.drop(columns='Город', inplace=True)
            df_one_region = df
            df_only_regions = pd.concat([df_only_regions, df_one_region])
        else:
            df_one_region = pd.DataFrame(df.iloc[0]).transpose()
            df_one_region['Цена_на_тариф'] = np.mean(df['Цена_на_тариф'])
            df_one_region['Количество_минут'] = np.mean(df['Количество_минут'])
            df_one_region.drop(columns='Город', inplace=True)
            df_only_regions = pd.concat([df_only_regions, df_one_region])

    df_MTS_final = df_only_regions[['Дата', 'Регион', 'Компания', 'Тип услуги',
                                    'Цена_на_тариф', 'Скорость_интернета_Мбит/с', 'Стоимость за 1 Мбит/с',
                                    'Количество_ГБ', 'Количество_минут', 'Стоимость за 1 мин']]
    return df_MTS_final


#########################################################################################################################
#########################################################################################################################

def mts_get_one_reg_links(driver, scrol=False, scrol_length=100, cities_name_get=['Пусто']):
    """МТС мобильная связь: функция позволяет собрать ссылки на страницы каждого города.
    И позволяет скролить вниз и выбирать только те города, которые ранее не были добавлены (cities_name_get)"""
    need_scrol = scrol
    if need_scrol:
        # прокручиваем
        source_element = driver.find_elements(By.XPATH, "//div[@class='jspDrag']")[1]  # сам скролер
        time.sleep(2)
        ActionChains(driver).click_and_hold(source_element).move_by_offset(0, scrol_length).perform()
        ActionChains(driver).reset_actions()
        time.sleep(1)
    time.sleep(1)
    # Получаем все объекты selenium про города
    cities_obj = driver.find_elements(By.XPATH, "//a[@class='mts16-popup-regions__link']")
    # Оставляем только нужные нам города
    our_cities_obj_part = [a for a in cities_obj if
                           a.text not in ['Россия', 'Армения', 'Беларусь', 'Другие города', '']]
    if need_scrol:
        # прокручиваем
        source_element = driver.find_elements(By.XPATH, "//div[@class='jspDrag']")[1]  # сам скролер
        time.sleep(2)
        ActionChains(driver).click_and_hold(source_element).move_by_offset(0, -scrol_length).perform()
        ActionChains(driver).reset_actions()
    cities_url = []
    cities_name = []
    city_missed = "Пусто"
    for w in range(len(our_cities_obj_part)):
        try:
            if need_scrol:
                # прокручиваем
                source_element = driver.find_elements(By.XPATH, "//div[@class='jspDrag']")[1]  # сам скролер
                time.sleep(2)
                ActionChains(driver).click_and_hold(source_element).move_by_offset(0, scrol_length).perform()
                ActionChains(driver).reset_actions()
                time.sleep(1)
            cities_obj = driver.find_elements(By.XPATH, "//a[@class='mts16-popup-regions__link']")
            # Оставляем только нужные нам города
            our_cities_obj_part = [a for a in cities_obj if
                                   a.text not in ['Россия', 'Армения', 'Беларусь', 'Другие города', '']]
            # Сохраняем их названия
            city_name = our_cities_obj_part[w].text

            if city_name in cities_name_get:
                need_scrol = False
                continue
            else:
                need_scrol = scrol
                cities_name.append(city_name)
                time.sleep(1)
                city_missed = our_cities_obj_part[w].text
                our_cities_obj_part[w].click()
                city_url = driver.current_url
                cities_url.append(city_url)
                # Перейдем в поле для выбора регионов
                driver.find_element(By.XPATH, "//div[@class='header__top-text js-user-region-title']").click()
                time.sleep(1)
        except:
            print(
                f"""МТС - город - {city_missed} был пропущен""")
            continue
    return cities_name, cities_url


def mts_get_right_region_names(df_links):
    """Функция позволяет преобразовать названия регионов нужный формат"""
    df_region_guide = pd.read_excel('region_guide.xlsx')
    # Разграничим Москву и Московскую область
    for index, row in df_links[df_links['region'] == 'Москва и Московская область'].iterrows():
        if row['city'] == 'Москва':
            df_links.loc[index, 'region'] = 'Москва'
        else:
            df_links.loc[index, 'region'] = 'Московская область'

    # Разграничим Санкт-Петербург и Ленинградская область
    for index, row in df_links[df_links['region'] == 'Санкт-Петербург и Ленинградская область'].iterrows():
        if row['city'] == 'Санкт-Петербург':
            df_links.loc[index, 'region'] = 'Санкт-Петербург'
        else:
            df_links.loc[index, 'region'] = 'Ленинградская область'

    # Сделаем словарь для респулики Адыгея с городами
    df_adigey_region = df_region_guide[df_region_guide['region_name'] == 'Республика Адыгея']
    df_krasnodarski_region = df_region_guide[df_region_guide['region_name'] == 'Краснодарский край']
    # Разграничим Краснодарский край и Республика Адыгея
    for index, row in df_links[df_links['region'] == 'Краснодарский край и Республика Адыгея'].iterrows():
        if row['city'] in list(df_adigey_region['cities_name']):
            df_links.loc[index, 'region'] = 'Республика Адыгея'
        elif row['city'] in list(df_krasnodarski_region['cities_name']) + ['Сочи', 'Анапа', 'Геленджик']:
            df_links.loc[index, 'region'] = 'Краснодарский край'

    # Заменим названия регионов на верные из справочника
    region_list = []
    for region in df_links['region']:
        rotation = [a for a in df_region_guide['region_name'].unique() if fuzz.ratio(
            ' '.join([c for c in region.split() if c not in ['край', 'Край', 'Республика', 'республика', 'Югра', '-']]),
            ' '.join(
                [c for c in a.split() if c not in ['край', 'Край', 'Республика', 'республика', 'Югра', '-']])) > 95]
        if len(rotation) == 1:
            region_list.append(rotation[0])
        else:
            print(region)
            region_list.append(np.nan)
    df_links['region'] = region_list
    return df_links


def mts_get_all_links(driver):
    """МТС мобильная связь: функция позволяет собрать список всех ссылок на страницы городов
    для каждого региона. Возможны пропуски некоторых регионов.
    Занимает примерно 40 мин"""
    company = 'MTS'
    today_date = date.today()
    url = 'https://volgograd.mts.ru/personal/mobilnaya-svyaz/tarifi/vse-tarifi/dla-smartfona'
    driver.get(url)
    # Перейдем в поле для выбора регионов
    driver.find_element(By.XPATH, "//div[@class='header__top-text js-user-region-title']").click()
    # Передвинем внутренний scroler повыше, чтобы был виден первый регион
    time.sleep(1)
    source_element = driver.find_element(By.XPATH, "//div[@class='jspDrag']")  # сам скролер
    # прокручиваем
    time.sleep(2)
    ActionChains(driver).click_and_hold(source_element).move_by_offset(0, -100).perform()
    ActionChains(driver).reset_actions()
    time.sleep(2)
    # Получаем названия всех регионов
    all_regions = driver.find_elements(By.XPATH,
                                       "//a[@class='mts16-popup-regions__link mts16-popup-regions__subregions-opener']")
    df_regions_cities = pd.DataFrame()
    region_missed = "Пусто"
    for j in range(len(all_regions) + 1):
        try:
            time.sleep(1)
            # Получаем названия всех регионов
            all_regions = driver.find_elements(By.XPATH,
                                               "//a[@class='mts16-popup-regions__link mts16-popup-regions__subregions-opener']")
            if j == 0:
                region = all_regions[j]
            elif j == 79:
                region = all_regions[-1]
            else:
                region = all_regions[j - 1]
            # Получаем название региона
            region_name = region.text
            region_missed = region_name
            # Нажимаем на название региона
            region.click()
            time.sleep(1)

            if len(driver.find_elements(By.XPATH, "//div[@class='jspDrag']")) > 1:
                # Получаем названия городов и ссылки на их страницы
                cities_name, cities_url = mts_get_one_reg_links(driver)
                for i in [100, 200, 300]:
                    try:
                        # Получаем названия городов и ссылки на их страницы
                        cities_name_part, cities_url_part = mts_get_one_reg_links(driver, scrol=True, scrol_length=i,
                                                                                  cities_name_get=cities_name)
                        cities_name = cities_name + cities_name_part
                        cities_url = cities_url + cities_url_part
                    except:
                        continue
                # Запоминаем значения
                cities_name = cities_name
                cities_url = cities_url

            else:
                # Получаем названия городов и ссылки на их страницы
                cities_name, cities_url = mts_get_one_reg_links(driver)

            # Добавляем все в дата-фрейм
            df = pd.DataFrame({'region': region_name,
                               'city': cities_name,
                               'url': cities_url})
            df['date'] = today_date
            df['company'] = company
            df_regions_cities = pd.concat([df_regions_cities, df])

            if j < 74:
                # Передвинем внутренний scroler повыше, чтобы был виден первый регион
                time.sleep(1)
                source_element = driver.find_element(By.XPATH, "//div[@class='jspDrag']")  # сам скролер
                # прокручиваем
                time.sleep(2)
                ActionChains(driver).click_and_hold(source_element).move_by_offset(0, -30).perform()
                ActionChains(driver).reset_actions()
        except:
            try:
                driver.get(list(df_regions_cities['url'])[-1])
                # Перейдем в поле для выбора регионов
                driver.find_element(By.XPATH, "//div[@class='header__top-text js-user-region-title']").click()
                # Передвинем внутренний scroler повыше, чтобы был виден первый регион
                time.sleep(1)
                source_element = driver.find_element(By.XPATH, "//div[@class='jspDrag']")  # сам скролер
                # прокручиваем
                time.sleep(2)
                ActionChains(driver).click_and_hold(source_element).move_by_offset(0, -30).perform()
                ActionChains(driver).reset_actions()
                # Получаем названия всех регионов
                all_regions = driver.find_elements(By.XPATH,
                                                   "//a[@class='mts16-popup-regions__link mts16-popup-regions__subregions-opener']")
                if j == 0:
                    region = all_regions[j]
                elif j == 79:
                    region = all_regions[-1]
                else:
                    region = all_regions[j - 1]
                # Получаем название региона
                region_name = region.text
                region_missed = region_name
                # Нажимаем на название региона
                region.click()
                time.sleep(1)

                if len(driver.find_elements(By.XPATH, "//div[@class='jspDrag']")) > 1:
                    # Получаем названия городов и ссылки на их страницы
                    cities_name, cities_url = mts_get_one_reg_links(driver)
                    for i in [100, 200, 300]:
                        # Получаем названия городов и ссылки на их страницы
                        cities_name_part, cities_url_part = mts_get_one_reg_links(driver, scrol=True, scrol_length=i,
                                                                                  cities_name_get=cities_name)
                        cities_name = cities_name + cities_name_part
                        cities_url = cities_url + cities_url_part
                    # Запоминаем значения
                    cities_name = cities_name
                    cities_url = cities_url

                else:
                    # Получаем названия городов и ссылки на их страницы
                    cities_name, cities_url = mts_get_one_reg_links(driver)

                # Добавляем все в дата-фрейм
                df = pd.DataFrame({'region': region_name,
                                   'city': cities_name,
                                   'url': cities_url})
                df['date'] = today_date
                df['company'] = company
                df_regions_cities = pd.concat([df_regions_cities, df])

                if j < 74:
                    # Передвинем внутренний scroler повыше, чтобы был виден первый регион
                    time.sleep(1)
                    source_element = driver.find_element(By.XPATH, "//div[@class='jspDrag']")  # сам скролер
                    # прокручиваем
                    time.sleep(2)
                    ActionChains(driver).click_and_hold(source_element).move_by_offset(0, -30).perform()
                    ActionChains(driver).reset_actions()
            except:
                print(f"""МТС-Пропущен регион - {region_missed}""")
                continue
    # Уберем лишние элементы из ссылок
    df_regions_cities['url'] = [
        link.replace(re.findall(r'\?.+', link)[0], "") if len(re.findall(r'\?.+', link)) != 0 else link
        for link in
        df_regions_cities['url']]
    df_regions_cities.reset_index(drop=True, inplace=True)
    df_regions_cities = mts_get_right_region_names(df_links=df_regions_cities)
    df_regions_cities.to_excel(f'Result/MTS/Link_list/MTS_links_{today_date}.xlsx', index=False)
    return df_regions_cities
