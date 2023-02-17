<h1 align="center">Приветствуем вас
<img src="https://github.com/blackcater/blackcater/raw/main/images/Hi.gif" height="32"/></h1>
<h1 align="center"><a href="https://github.com/AlchiProMent/GrForecast.git" target="_blank">"Парсер сайтов телекоммуникационных услуг"</a></h1>

<h4 align="center">февраль,2023 г.</h4>


## Введение
Проект создан для автоматизированного сбора информации о ценах не телекоммуникационные услуги в разрезе по регионам со следующих сайтов:
* <a href="https://volgograd.mts.ru/personal/mobilnaya-svyaz/tarifi/vse-tarifi/dla-smartfona" target="_blank">МТС - мобильная связь</a>
* <a href="https://moscow.megafon.ru" target="_blank">Мегафон - мобильная связь </a>
* <a href="https://nizhegorodskaya-obl.beeline.ru/customers/products/mobile/tariffs/" target="_blank">Билайн - мобильная связь</a>
* <a href="https://msk.rt.ru/homeinternet" target="_blank">Ростелеком - домашний интернет</a>
* <a href="https://msk.tele2.ru/tariffs" target="_blank">Теле2 - мобильная связь</a>

## Инструкция по установке
#### Для запуска кода необходимо установить Python 3.10 и выполнить следующие команды:
1. git clone http://... 
2. Создать виртуальное окружение командой 
* > py -m venv env для windows 
* > python -m venv venv для MacOs 
3. Активировать виртуальное окружение командой: 
* > venv\bin\Activate.ps1 для Windows 
* > venv\Scripts\activate для MacOs
4. Установить все необходимые библиотеки командой: 
* > py -m pip install -r requirements.txt
* > python3 -m pip3 install -r requirements.txt
5. Создать файл password.py, в котором будут указана необходимая информация для подключения к базе, так как код после сбора информации кладет ее в базу формата PostgreSQL
* > def password():
    db_user = ''
    db_pass = ''
    db_ip = ''
    return db_user,db_pass,db_ip
6. Запустить программу командой: 
* > streamlit run [main.py](main.py)

## Структура репозитория 

1. Наборы функций для сбора информации с сайтов:
   * [MTS_parser.py](MTS_parser.py)
   * [MegaFone_parser.py](MegaFone_parser.py)
   * [Beeline_parser.py](Beeline_parser.py)
   * [Rostelecom_parser.py](Rostelecom_parser.py)
   * [Tele2_parser.py](Tele2_parser.py)
2. [Postgre_base.py](Postgre_base.py) - Код, который вытаскивает последний файл из папки [Final](Result/Final) и грузит его в БД формата PostgreSQL
3. [chromedriver_windows.exe](chromedriver_windows.exe) | [chromedriver_mac_os.exe](chromedriver_mac_os.exe) - Chrome драйвера для windows и mac os соответственно. ВНИМАНИЕ драйвера иногда приходится обновлять в зависимости от версии вашего браузера Chrome. Скачать их можно на [сайте](https://chromedriver.chromium.org/downloads)
4. [general_functions.py](general_functions.py) - Тут содержится набор общих функций, которые используются в функциях из пункта 1
5. [main.py](main.py) - Код, который:
   * запускает драйвер [Chrome](chromedriver_mac_os.exe)
   * запускает по очереди функции из пункта 1
   * собирает необходимую информацию с сайтов pandas.DataFrame
   * определяет формат каждой колонки
   * сохраняет полученный результат в excel файл в папке [Final](Result/Final)
6. [Pac.bat](Pac.bat) - файл, который позволяет запустить [main.py](main.py) простым двойным кликом.
   * Для работы необходимо прописать полный путь к интерпретатору и в кавычках прописать полный путь к исполняемому файлу, в конце поставив pause, для завершения кода
   * Используется для автоматического запуска на Task Scheduler (ps если в коде есть локальные ссылки внутри папке в Scheduler необходимо указать путь к проекту в поле "Start in")
7. [region_guide.xlsx](region_guide.xlsx) - файл с единым словарем с названиями всех регионов и их кодом. Используется для стандартизации названий регионов