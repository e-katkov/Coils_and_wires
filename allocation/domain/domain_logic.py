from copy import deepcopy
from typing import Any

from allocation.exceptions import exceptions


class OrderLine:
    """Абстракция товарной позиции - элемента заказа материалов (проводов, кабелей)."""
    def __init__(self, order_id: str, line_item: str, product_id: str, quantity: int):
        # Идентификатор заказа материалов
        self.order_id = order_id
        # Номер товарной позиции в заказе
        self.line_item = line_item
        # Идентификатор материала
        self.product_id = product_id
        # Количество материала
        self.quantity = quantity

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, OrderLine):
            return False
        return self.order_id == other.order_id and self.line_item == other.line_item

    def __hash__(self) -> int:
        return hash(self.order_id + self.line_item)


class Coil:
    """
    Абстракция бухты - кольцеобразного мотка провода/кабеля
    или барабана, на который намотан данный материал.
    """
    def __init__(self, reference: str, product_id: str, quantity: int,
                 recommended_balance: int, acceptable_loss: int):
        # Идентификатор бухты с материалом
        self.reference = reference
        # Идентификатор материала
        self.product_id = product_id
        # Изначальное количество материала
        self.initial_quantity = quantity
        # Рекомендуемый остаток материала - количество материала, оставшееся после размещения
        # товарной позиции, которое наиболее вероятно позволит выполнить следующее размещение
        self.recommended_balance = recommended_balance
        # Приемлемые потери материала - количество материала, которое маловероятно
        # сможет быть реализовано при следующем размещении
        self.acceptable_loss = acceptable_loss
        # Множество экземпляров размещенных товарных позиций
        self.allocations: set[OrderLine] = set()

    @property
    def allocated_quantity(self) -> int:
        """Суммарное количество материала для выполненных размещений товарных позиций."""
        return sum(line.quantity for line in self.allocations)

    @property
    def available_quantity(self) -> int:
        """Доступное количество материала после выполненных размещений товарных позиций."""
        return self.initial_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        """Принимает экземпляр товарной позиции, определяет возможность ее размещения в бухте."""
        result = (self.product_id == line.product_id) and \
                 (((self.available_quantity - line.quantity) >= self.recommended_balance)
                  or (self.acceptable_loss >= (self.available_quantity - line.quantity) >= 0))
        return result

    def allocate(self, line: OrderLine) -> None:
        """Принимает экземпляр товарной позиции, размещает ее в бухте."""
        if self.can_allocate(line):
            self.allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        """Принимает экземпляр товарной позиции, отменяет ее размещение в бухте."""
        if line in self.allocations:
            self.allocations.discard(line)

    def reallocate(self, coil: 'Coil') -> set[OrderLine]:
        """
        Принимает экземпляр бухты. Среди товарных позиций, размещенных в бухте (self),
        для которой вызван метод, определяет те, которые могут быть размещены
        в бухте (coil) - аргументе метода.
        """
        new_coil = deepcopy(coil)
        sorted_line_list = sorted(self.allocations, key=lambda x: x.quantity)
        for line in sorted_line_list:
            new_coil.allocate(line)
        return new_coil.allocations

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Coil):
            return False
        return self.reference == other.reference

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Coil):
            return False
        return self.available_quantity < other.available_quantity

    def __hash__(self) -> int:
        return hash(self.reference)


def allocate_to_list_of_coils(line: OrderLine, coils: list[Coil]) -> Coil:
    """
    Принимает экземпляр товарной позиции и список экземпляров бухт, возвращает бухту,
    в которую было выполнено размещение.

    В случае, если товарная позиции уже была размещена в одной из бухт списка, возвращает эту бухту.
    Генерирует исключение, возникающее при невозможности разместить товарную позицию
    в какой-либо бухте списка.
    """
    for coil in coils:
        for orderline in coil.allocations:
            if orderline.order_id == line.order_id and orderline.line_item == line.line_item:
                return coil
    try:
        result_coil = next(coil for coil in sorted(coils) if coil.can_allocate(line))
        result_coil.allocate(line)
        return result_coil
    except StopIteration:
        raise exceptions.OutOfStock(line.product_id)
