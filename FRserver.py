#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from __future__ import print_function #compatible print function for Python 2 and 3
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import pyshtrih

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0
finally:
  C = ConfigParser()
  C.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'FRserver.config'))
  debug = C.getboolean('CONFIG', 'debug', fallback=True)
  ServerInterface = C.get('CONFIG', 'ServerInterface', fallback='127.0.0.1')
  ServerPort = C.getint('CONFIG', 'ServerPort', fallback=8888)
  FRport = C.get('CONFIG', 'FRport', fallback='AUTO')
  FRspeed = C.getint('CONFIG', 'FRspeed', fallback=115200)

def discovery_callback(port, baudrate):
  if debug:
    print(port, baudrate)

class GP(BaseHTTPRequestHandler):
  def do_HEAD(self):
    self.send_response(404)
    self.end_headers()
  def do_GET(self):
    self.send_response(404)
    self.end_headers()

  def do_POST(self):
    length = int(self.headers['content-length'])
    data = self.rfile.read(length) #it is bytes
    data = data.decode("utf-8")

    if self.path == '/req' and data[:5] == 'data=':
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.send_header('Access-Control-Allow-Origin', '*')
      self.end_headers()

      data = data[5:] #strip data=
      data = data.split('&') #remove not used parameters
      data = data[0] #take data parameter only

      if debug:
        print(data)

      resp = self.doPRINT(data) #magic

      self.wfile.write(resp.encode("utf-8")) #bytes(string, "utf-8") or string.encode("utf-8")
    else:
      self.send_response(404)
      self.end_headers()

  def doPRINT(self, data):
    result = '' #Наименование_команды;код_ответа;текст_ответа;ответ_ядра XML BASE64URL;
    connected = True

    try:
      if FRport == 'AUTO':
        devices = pyshtrih.discovery(discovery_callback)
      else:
        devices = pyshtrih.discovery(discovery_callback, FRport, FRspeed)

      if not devices:
          raise Exception(u'Устройства не найдены')

      # предположим, что подключена только одна ККМ
      device = devices[0]
      device.connect()
    except Exception as e:
      print(e)
      connected = False

    try:
      for l in data.strip().splitlines():
        d = l.strip().split(';')

        #reset print settings to default
        if connected:
          pass

        #пропускаем пустую строку
        if not d:
          result += "\n"

        elif not connected:
          result += d[0]+";255;Нет связи c ФР;;\n"

        elif d[0]=='feed': #feed;КОЛВО_СТРОК; протяжка ленты
          try:
            device.feed(int(d[1]), control_tape=True, cash_tape=True, skid_document=False)
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";1;"+format(e)+";;\n"

        elif d[0]=='continue_print': #continue_print; Продолжить печать после ошибки
          try:
            device.continue_print()
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";9;"+format(e)+";;\n"

        elif d[0]=='cut_check': #cut_check; отрезчик
          try:
            device.cut()
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";10;"+format(e)+";;\n"

        elif d[0]=='open_cash_box': #open_cash_box;НОМЕР_ЯЩИКА;
          try:
            device.open_drawer(int(d[1])) #device.open_drawer(box=0)
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";11;"+format(e)+";;\n"

        elif d[0]=='p': #p;ТЕКСТ; выводит текст
          try:
            device.print_string(d[1])
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";2;"+format(e)+";;\n"

        elif d[0]=='pm': #pm;ТЕКСТ; выводит текст c новыми линиями
          try:
            for line in d[1].split("#kkm_br#"):
              device.print_string(line)
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";3;"+format(e)+";;\n"

        elif d[0]=='print_font': #print_font;НОМЕР_ШРИФТА;ТЕКСТ; выводит текст заданым шрифтом
          try:
            device.print_font(d[2], int(d[1]))
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";4;"+format(e)+";;\n"

        elif d[0]=='print_bold': #print_bold;ТЕКСТ; выводит текст жирным
          try:
            device.print_font(d[1], 2)
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";5;"+format(e)+";;\n"

        elif d[0]=='b': #b;ТИП_ЧЕКА;КАССИР;ПЕЧАТЬ; #открытие чека
          try:
            check_type = int(d[1])

            # TODO d[3] сделать передачу печатать/не печатать документ

            #QKKM     #0 продажа, 1 возврат продажи, 2 покупка,           3 возврат покупки
            #Strih-M  #0 продажа, 1 покупка,         2 - возврат продажи, 3 - возврат покупки
            #делаем совместимость с Qkkm
            if check_type == 0:
              check_type = 0
            elif check_type == 1:
              check_type = 2
            elif check_type == 2:
              check_type = 1
            elif check_type == 3:
              check_type = 3
            else: #поставим по-умолчанию продажу
              check_type = 0

            #открываем документ
            device.open_check(check_type)

            #указываем кассира если есть
            if d[2]:
              cashier = pyshtrih.FD({1021: d[2]})
              device.send_tlv_struct(cashier.dump())


            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";6;"+format(e)+";;\n"

        elif d[0]=='set_tlv': #set_tlv;ТЭГ;ТИП;ДАННЫЕ #Передать TLV-реквизит в ККМ
          try:
            tlv = pyshtrih.FD({int(d[1]): d[3]})
            device.send_tlv_struct(tlv.dump())

            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";12;"+format(e)+";;\n"

        elif d[0]=='smde': #smde;НАЗВАНИЕ_ТОВАРА;ЦЕНА;КОЛВО;НАЛОГ;СЕКЦИЯ;ПСР;ППР #Добавить товар в чек
          try:
            text = d[1]
            price = int(d[2])
            quantity = int(d[3])
            nalog = int(d[4])
            department = int(d[5])
            #psr = int(d[6])
            #ppr = int(d[7])

            # TODO сделать поддержку ФФД 1.1 согласно протоколу Qkkm

            #device.sale(item, department_num=0, tax1=0, tax2=0, tax3=0, tax4=0)
            #text, quantity, price = item
            if check_type == 0:
              device.sale( (text, quantity, price), department_num=department, tax1=nalog )
            elif check_type == 2:
              device.return_sale( (text, quantity, price), department_num=department, tax1=nalog )
            else:
              raise Exception(u'Операция не поддерживается')

            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";7;"+format(e)+";;\n"

        elif d[0]=='tmde':
          try:
            #device.close_check(cash=0, payment_type2=0, payment_type3=0, payment_type4=0, discount_allowance=0, tax1=0, tax2=0, tax3=0, tax4=0, text=None)

            if len(d) >= 9: #Оплатить чек (длинная форма) Не соответствует ФФД 1.1
              #смешанная оплата, должны быть заполнены все поля
              #tmde;СУММА1;СУММА2;СУММА3;СУММА4;НОМЕР_НАЛОГА_1;НОМЕР_НАЛОГА_2;НОМЕР_НАЛОГА_3;НОМЕР_НАЛОГА_4

              device.close_check(
                cash=int(d[1]),
                payment_type2=int(d[2]),
                payment_type3=int(d[3]),
                payment_type4=int(d[4]),
                discount_allowance=0,
                tax1=int(d[5]),
                tax2=int(d[6]),
                tax3=int(d[7]),
                tax4=int(d[8]),
                text=None
              )

            elif len(d) >= 7: #Оплатить чек Соответствует ФФД 1.1
              # TODO сделать поддержку ФФД 1.1 согласно протоколу Qkkm
              #tmde;СУММА1;СУММА2;СУММА3;СУММА4;СУММА5;СНО
              device.close_check(
                cash=int(d[1]),
                payment_type2=int(d[2]),
                payment_type3=int(d[3]),
                payment_type4=int(d[4])
              )

            else:
              #Оплатить чек (короткая форма) Не соответствует ФФД 1.1
              #tmde;СУММА;НОМЕР_ОПЛАТЫ;
              payment_type = int(d[2])
              summa = int(d[1])

              if payment_type == 0:
                device.close_check(cash=summa)
              elif payment_type == 1:
                device.close_check(payment_type2=summa)
              elif payment_type == 2:
                device.close_check(payment_type3=summa)
              elif payment_type == 3:
                device.close_check(payment_type4=summa)

            result += d[0]+";0;Успешно;;\n"

          except Exception as e:
            result += d[0]+";8;"+format(e)+";;\n"

        elif d[0]=='g': #g; Аннулировать чек
          try:
            device.cancel_check()
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";14;"+format(e)+";;\n"

        elif d[0]=='open_session': #open_session; Открыть смену
          try:
            device.open_shift()
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";15;"+format(e)+";;\n"

        elif d[0]=='x': #x; Печатает промежуточный отчет без гашения. Смена не закрывается.
          try:
            device.x_report()
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";16;"+format(e)+";;\n"

        elif d[0]=='z': #z; Печатает отчет c гашением. Смена закрывается.
          try:
            device.z_report()
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";17;"+format(e)+";;\n"

        elif d[0]=='c': #c; Выводит на чековую ленту дубликат последнего распечатанного чека.
          try:
            device.repeat()
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";18;"+format(e)+";;\n"

        elif d[0]=='imde': #imde;СУММА Внесение/выемка денег в кассу
          try:
            summa = int(d[1]);

            if summa > 0:
              device.income(summa)
            elif summa < 0:
              device.outcome(summa)

            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";19;"+format(e)+";;\n"

        elif d[0]=='d': #d; Запрос полного статуса ККМ
          try:
            state = ''
            state += format(device.full_state())+" "
            state += format(device.fs_state())+" "
            state += format(device.fs_info_exchange())
            result += d[0]+";0;"+state+";;\n"
          except Exception as e:
            result += d[0]+";20;"+format(e)+";;\n"

        elif d[0]=='rep_sections': #rep_sections; Отчет по секциям
          try:
            device.sections_report()
            result += d[0]+";0;Успешно;;\n"
          except Exception as e:
            result += d[0]+";21;"+format(e)+";;\n"

        elif d[0]=='m': #m;РЕГИСТР
          try:
            result += d[0]+";0;"+format(device.request_monetary_register(int(d[1])))+";;\n"
          except Exception as e:
            result += d[0]+";22;"+format(e)+";;\n"

        elif d[0]=='get_fiscal_mark': #get_fiscal_mark;ФНДок
          try:
            result += d[0]+";0;"+format(device.fs_find_document_by_num(int(d[1])))+";;\n"
          except Exception as e:
            result += d[0]+";23;"+format(e)+";;\n"

        else:
          result += d[0]+";0;Команда не поддерживается;;\n"

    except Exception as e:
      if debug:
        state_ = device.state()
        mode = state_[u'Режим ФР']
        print(format(e), "\nРежим ФР", mode)
      return None

    finally:
      if debug:
        print(result)

      if connected:
        device.disconnect()

      return result

def run(server_class=HTTPServer, handler_class=GP):
  try:
    server_address = (ServerInterface, ServerPort)
    httpd = server_class(server_address, handler_class)
    print('Server running at '+ServerInterface+':'+str(ServerPort)+'...', "\nPress Ctrl+C to shut down")
    httpd.serve_forever()
  except KeyboardInterrupt:
    print(' KeyboardInterrupt received, shutting down server')
    httpd.socket.close()

run()
