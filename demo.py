#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function #compatible print function for Python 2 and 3
import pyshtrih


def discovery_callback(port, baudrate):
    print(port, baudrate)


if __name__ == '__main__':
    devices = pyshtrih.discovery(discovery_callback)
    #devices = pyshtrih.discovery(discovery_callback, "/dev/ttyUSB0", 115200)
    #devices = pyshtrih.discovery(discovery_callback, "socket://192.168.137.111:7778", 115200)

    if not devices:
        raise Exception(u'Устройства не найдены')

    # для простоты примера, предположим, что подключена только одна ККМ
    device = devices[0]
    device.connect()

    try:
        #device.cancel_check()
        #device.open_shift()
        #device.open_check(0) #0 - продажа, 1 - покупка, 2 - возврат продажи, 3 - возврат покупки
        #print(device.model())
        #print(device.state())
        #print(device.full_state())
        #print(device.fs_state())
        #print(device.fs_info_exchange())
        device.beep()
        '''
        device.print_string("Пример печати нефискальной строки текста")
        device.print_line() #Печать строки разделителя
        device.feed(3, control_tape=False, cash_tape=True, skid_document=False) #Протяжка чековой ленты на заданное количество строк
        device.cut() #Обрезка чека
        '''
        #device.open_drawer() #Открыть денежный ящик
        #device.open_shift() #Открыть смену
        #device.x_report()
        #device.z_report()
        #device.income(50000) #Внесение
        #device.outcome(50000) #Выплата
        #device.return_sale() #Возврат продажи
        #device.print_barcode() #Печать штрих-кода
        #device.continue_print() #Продолжение печати
        #device.cancel_check() #Отменить чек
        #device.send_tlv_struct() #Передать произвольную TLV структуру

        #Тест установки TLV
        """
        #device.cancel_check()
        phone = pyshtrih.FD({1008: u'+79313587439'})
        email = pyshtrih.FD({1008: u'm0x3@mail.ru'})
        cashier = pyshtrih.FD({1021: u'Кассир: Пупкин В.И.'})
        #tlv.set_value(1008, u'+79313587439')
        #tlv.set_value(1021, u'Кассир: Пупкин В.И.')
        device.open_check(0)
        device.send_tlv_struct(cashier.dump())
        device.send_tlv_struct(phone.dump())
        #device.send_tlv_struct(email.dump())
        device.sale(
            (u'За рубль', 1000, 100), tax1=1
        )
        device.close_check(100)
        device.feed(3, control_tape=True, cash_tape=True)
        """

        """
        device.open_check(0)

        #device.sale(item, department_num=0, tax1=0, tax2=0, tax3=0, tax4=0)
        #text, quantity, price = item

        device.sale(
            (u'Позиция 1', 4000, 1000), tax1=1
        )
        device.sale(
            (u'Позиция 2', 3000, 2000), tax1=2
        )
        device.sale(
            (u'Позиция 3', 2000, 3000), tax1=3
        )
        device.sale(
            (u'Позиция 4', 1000, 4000), tax1=4
        )
        device.close_check(20000)
        device.cut(True)
        """

    except Exception as e:
        state_ = device.state()
        mode = state_[u'Режим ФР']
        print(e, "\nРежим ФР", mode)
    finally:
        device.disconnect()
