from sqlalchemy import create_engine
from general_functions import *
from password import *

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
    return df_all_links

# Получаем последний созданный файл
df_final = get_last_file('Result\Final')
# Получаем пароли
db_user,db_pass,db_ip = password()
# Загружаем талицу в БД
engine = create_engine(f"postgresql://{db_user}:{db_pass}@{db_ip.split(':')[0]}:{db_ip.split(':')[1]}/khd_kc")
df_final.to_sql(con=engine, schema='dal_data', name='iskc_cnp_004_a_monitoring_prices_telecom', if_exists='append',
                index=False)