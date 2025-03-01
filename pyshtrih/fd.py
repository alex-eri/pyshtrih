# -*- coding: utf-8 -*-


from . import misc, excepts
from .compat import unicode, bool_compat


@bool_compat
class FD(object):
    TAGS = {
        # тэг: (тип значения, признак обязательности соблюдения длины, максимальная длина)
        # перечень тегов https://www.garant.ru/products/ipo/prime/doc/71540610/
        # телефон или электронный адрес покупателя
        1008: (unicode, False, 64),
        # имя кассира для передачи в офд и печати на чеке
        1021: (unicode, False, 64),
        1212: (int, False, 1)
    }

    CAST = {
        unicode: lambda x: x.encode('cp866'),
        int: lambda x: x.to_bytes(1,'big')
    }
    LEN = {
        bytes: (len, lambda value, len_: value.ljust(len_))
    }

    def __init__(self, tags=None):
        """
        Структура для работы с фискальными данными.

        :type tags: dict
        :param tags: словарь {тэг: значение}
        """

        self.data = {}
        self.b_data = bytearray()

        tags = tags or {}
        for item in tags.items():
            self.set_value(*item)

    def set_value(self, tag, value):
        """
        Установить значение для тэга.

        :type tag: int
        :param tag: тэг
        :param value: значение тэга
        """

        try:
            type_, len_req, len_max = self.TAGS.get(tag)
        except TypeError:
            raise excepts.FDError(u'Тэг {} не поддерживается'.format(tag))

        value_type = type(value)
        if value_type != type_:
            raise excepts.FDError(
                u'Значение для тэга {} должно быть {}, получено {}'.format(tag, type_, value_type)
            )

        cast_call = self.CAST.get(value_type)
        if cast_call:
            value = cast_call(value)
            value_type = type(value)

        len_call, fill_call = self.LEN[value_type]
        if len_call(value) > len_max:
            raise excepts.FDError(u'Тэг {} имеет ограничение длины - {} байта'.format(tag, len_max))
        if len_req:
            value = fill_call(value, len_max)

        value_len = len_call(value)
        if not value_len:
            return

        self.data[tag] = value
        self.b_data.extend(
            misc.bytearray_concat(
                misc.CAST_SIZE['2'](tag),
                misc.CAST_SIZE['2'](len_call(value)),
                value
            )
        )

    def dump(self):
        """
        Получить TLV структуру, готовую для передачи в команду send_tlv_struct.

        :rtype: bytes
        :return: tlv строка
        """

        return bytes(self.b_data)

    def __bool__(self):
        return bool(self.data)
