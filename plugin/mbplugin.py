# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import time, os, sys, logging, traceback
import xml.etree.ElementTree as etree
import dbengine, store, settings, httpserver_mobile

lang = 'p'  # Для плагинов на python преффикс lang всегда 'p'

def main():
    options = store.read_ini()['Options']
    logging.basicConfig(filename=options.get('loggingfilename', settings.loggingfilename),
                        level=options.get('logginglevel', settings.logginglevel),
                        format=options.get('loggingformat', settings.loggingformat))
    # В коммандной строке указан плагин ?
    if len(sys.argv) < 2:
        exception_text = f'При вызове mbplugin.bat не указан модуль'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        return -1
    # Это плагин от python ?
    if not sys.argv[1].startswith(f'{lang}_'):
        # Это плагин не от python, тихо выходим
        logging.info(f'Not python preffix')
        return -2
    plugin = sys.argv[1].split('_', 1)[1]  # plugin это все что после p_
    # Такой модуль есть ? Он грузится ?
    try:
        module = __import__(plugin, globals(), locals(), [], 0)
    except Exception:
        exception_text = f'Модуль {plugin} не грузится: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        return -1
    if len(sys.argv) == 4: # plugin login password
        login = sys.argv[2]
        password = sys.argv[3]
    else: # request указан в переменной RequestVariable ?        
        try:
            RequestVariable = os.environ['RequestVariable'].strip(' "')
            root = etree.fromstring(RequestVariable)
            login = root.find('Login').text
            password = root.find('Password').text
        except Exception:
            exception_text = f'Не смог взять RequestVariable: {"".join(traceback.format_exception(*sys.exc_info()))}'
            logging.error(exception_text)
            sys.stdout.write(exception_text)
            return -1
        logging.debug(f'request = {RequestVariable}')
    
    # Запуск плагина
    logging.info(f'Start {lang} {plugin} {login}')
    try:
        result = module.get_balance(login, password, f'{lang}_{plugin}_{login}')
    except Exception:
        exception_text = f'Ошибка при вызове модуля \n{plugin}: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        return -1
    # Готовим результат
    try:
        sys.stdout.write(store.result_to_xml(result))
    except Exception:
        exception_text = f'Ошибка при подготовке результата: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        return -1
    # пишем в базу
    dbengine.write_result_to_db(f'{lang}_{plugin}', login, result)
    # обновляем данные из mdb
    dbengine.update_sqlite_from_mdb()
    # генерируем balance_html
    httpserver_mobile.write_report()
    logging.debug(f'result = {result}')
    logging.info(f'Complete {lang} {plugin} {login}\n')
    return 0


if __name__ == '__main__':
    # todo mbplugin.py plugin  (RequestVariable=<Request>\n<ParentWindow>007F09DA</ParentWindow>\n<Login>p_test_1234567</Login>\n<Password>pass1234</Password>\n</Request>)
    # todo mbplugin.py plugin login password (нужен для отладки)
    main()
