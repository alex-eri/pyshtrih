# -*- coding: utf-8 -*-

from __future__ import print_function #compatible print function for Python 2 and 3
import pyshtrih


def discovery_callback(port, baudrate):
    print(port, baudrate)


if __name__ == '__main__':
    #devices = pyshtrih.discovery(discovery_callback)
    #devices = pyshtrih.discovery(discovery_callback, "/dev/ttyUSB0", 115200)
    devices = pyshtrih.discovery(discovery_callback, "socket://192.168.137.111:7778", 115200)

    if not devices:
        raise Exception(u'Устройства не найдены')

    # для простоты примера, предположим, что подключена только одна ККМ
    device = devices[0]
    device.connect()

    print(device.model())
    print(device.full_state())

    device.beep()
    """
    device.open_check(0)
    device.sale(
        (u'Позиция 1', 1000, 1000), tax1=1
    )
    device.sale(
        (u'Позиция 2', 1000, 2000), tax1=2
    )
    device.sale(
        (u'Позиция 3', 1000, 3000), tax1=3
    )
    device.sale(
        (u'Позиция 4', 1000, 4000), tax1=4
    )
    device.close_check(10000)
    device.cut(True)
    """

    device.disconnect()
