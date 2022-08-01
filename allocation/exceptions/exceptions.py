from dataclasses import dataclass, field


@dataclass
class OutOfStock(Exception):
    """
    Исключение возникает при размещении товарной позиции в одну из бухт списка,
    в случае, если выполнить такое размещение невозможно из-за недостаточного количества материала.
    """
    product_id: str
    message: str = field(init=False)

    def __post_init__(self) -> None:
        self.message = f'Недостаточное количество материала с product_id={self.product_id}'


@dataclass
class DBCoilRecordDoesNotExist(Exception):
    """
    Исключение возникает при обращении к записи с идентификатором reference таблицы Coil базы данных,
    в случае, если записи с таким идентификатором в таблице не существует.
    """
    reference: str
    message: str = field(init=False)

    def __post_init__(self) -> None:
        self.message = f'Запись с reference={self.reference} отсутствует в таблице CoilDB базы данных'


@dataclass
class DBOrderLineRecordDoesNotExist(Exception):
    """
    Исключение возникает при обращении к записи с идентификаторами order_id и line_item таблицы OrderLine базы данных,
    в случае, если записи с такими идентификаторами в таблице не существует.
    """
    order_id: str
    line_item: str
    message: str = field(init=False)

    def __post_init__(self) -> None:
        self.message = f'Запись с order_id={self.order_id} и line_item={self.line_item}' \
                       f' отсутствует в таблице OrderLineDB базы данных'


@dataclass
class DBCoilRecordAlreadyExist(Exception):
    """
    Исключение возникает при создании в таблице Coil базы данных записи с идентификатором reference,
    в случае, если запись с таким идентификатором уже существует в таблице.
    """
    reference: str
    message: str = field(init=False)

    def __post_init__(self) -> None:
        self.message = f'Запись с reference={self.reference} уже существует в таблице CoilDB базы данных'


@dataclass
class DBOrderLineRecordAlreadyExist(Exception):
    """
    Исключение возникает при создании в таблице OrderLine базы данных записи с идентификаторами
    order_id и line_item, в случае, если запись с такими идентификаторами уже существует в таблице.
    """
    order_id: str
    line_item: str
    message: str = field(init=False)

    def __post_init__(self) -> None:
        self.message = f'Запись с order_id={self.order_id} и line_item={self.line_item}' \
                       f' уже существует в таблице OrderLineDB базы данных'
