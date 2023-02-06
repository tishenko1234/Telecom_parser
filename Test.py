import numpy as np

from Tele2_parser import *
from MegaFone_parser import *
from Rostelecom_parser import *
from MTS_parser import *
from Beeline_parser import *
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

df_MegaFone = pd.read_excel('Result/MegaFon/MegaFone_2023-01-26.xlsx')
df_Beeline = pd.read_excel('Result/Beeline/Beeline_2023-01-27.xlsx')
df_MTS = pd.read_excel('Result/MTS/MTS_2023-01-26.xlsx')
df_Tele2 = pd.read_excel('Result/Tele2/Tele2_2023-01-26.xlsx')
df_Rostelecom = pd.read_excel('Result/Rostelecom/Rostelecom_2023-01-26.xlsx')

MegaFone = MegaFone_final(df_MegaFone)
Beeline = Beeline_final(df_Beeline)
MTS = MTS_final(df_MTS)
Tele2 = Tele2_final(df_Tele2)
Rostelecom = Rostelecom_final(df_Rostelecom)

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
from sqlalchemy import create_engine

db_user = 'vyurchenko'
db_pass = 'aSkjaMXSUQzQIhKMvZOQ80aZaUJLgT'
db_ip = '10.101.16.21:5432'
engine = create_engine(f"postgresql://{db_user}:{db_pass}@{db_ip.split(':')[0]}:{db_ip.split(':')[1]}/khd_kc")
df_final.to_sql(con=engine, schema='dal_data', name='iskc_cnp_004_a_monitoring_prices_telecom', if_exists='append',
                index=False)