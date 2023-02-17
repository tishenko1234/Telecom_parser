from Tele2_parser import *
from MegaFone_parser import *
from Rostelecom_parser import *
from MTS_parser import *
from Beeline_parser import *
from selenium.webdriver.chrome.options import Options
from selenium import webdriver


# Запускаем браузер
options = Options()
options.headless = True
options.add_argument('--start-maximized')
options.page_load_strategy = 'normal'
try:
    driver = webdriver.Chrome(executable_path="./chromedriver_windows.exe", options=options)
except:
    driver = webdriver.Chrome(executable_path="./chromedriver_mac_os.exe", options=options)

df_MegaFone = MegaFone(driver, update_links=False)
MegaFone = MegaFone_final(df_MegaFone)

df_Beeline = Beeline(driver, update_links=False)
Beeline = Beeline_final(df_Beeline)

df_MTS = MTS(driver, update_links=False)
MTS = MTS_final(df_MTS)


df_Tele2 = Tele2(driver, update_links=False)
Tele2 = Tele2_final(df_Tele2)


df_Rostelecom = Rostelecom(driver, update_links=False)
Rostelecom = Rostelecom_final(df_Rostelecom)
driver.quit()

df_final = pd.concat([Beeline, MegaFone, MTS, Tele2, Rostelecom])

# Добавляем код региона
df_region = pd.read_excel('region_guide.xlsx')
df_region = df_region.drop_duplicates()
reg = [a for a in df_region['region_name']]
cod = [a for a in df_region['region_code']]
reg_cod_voc = dict(zip(reg, cod))
df_final.insert(2, 'Код региона', [reg_cod_voc[a] for a in df_final['Регион']])
today_date = date.today()
df_final.replace('no_inf', 0, inplace=True)
df_final.astype({'Дата': np.datetime64,
                 'Регион': str,
                 'Компания': str,
                 'Тип услуги': str,
                 'Цена_на_тариф': float,
                 'Скорость_интернета_Мбит/с': float,
                 'Стоимость за 1 Мбит/с': float,
                 'Количество_ГБ': float,
                 'Количество_минут': float,
                 'Стоимость за 1 мин': float
                 })
df_final.columns = ['date',
                    'region_name',
                    'region_code',
                    'company',
                    'type_service',
                    'tarif_price',
                    'internet_speed',
                    'price_for_1mb',
                    'amount_gb',
                    'amount_minute',
                    'price_for_1minute']

df_final.to_excel(f'Result/Final/Final_{today_date}.xlsx', index=False)


