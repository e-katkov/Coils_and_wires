from dataclasses import dataclass


@dataclass(frozen=True)
class OrderLine:
    order_id: str
    product_id: str
    quantity: int


class Coil:
    def __init__(self, reference: str, product_id: str, quantity: int):
        self.reference = reference
        self.product_id = product_id
        self._initial_quantity = quantity
        self._allocations: set[OrderLine] = set()

    @property
    def allocated_quantity(self):
        return sum(line.quantity for line in self._allocations)

    @property
    def available_quantity(self):
        return self._initial_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return (self.product_id == line.product_id) and (
            self.available_quantity >= line.quantity)

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

