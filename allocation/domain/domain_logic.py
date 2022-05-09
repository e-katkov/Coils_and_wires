from dataclasses import dataclass


@dataclass(frozen=True)
class OrderLine:
    order_id: str
    product_id: str
    quantity: int


class Coil:
    def __init__(self, reference: str, product_id: str,
                 quantity: int, recommended_balance: int, acceptable_loss: int):
        self.reference = reference
        self.product_id = product_id
        self._initial_quantity = quantity
        self.recommended_balance = recommended_balance
        self.acceptable_loss = acceptable_loss
        self._allocations: set[OrderLine] = set()

    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._initial_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return (self.product_id == line.product_id) and (
            self.available_quantity >= line.quantity)

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Coil):
            return False
        return self.reference == other.reference

    def __lt__(self, other) -> bool:
        if not isinstance(other, Coil):
            return False
        return self.available_quantity < other.available_quantity

    def __hash__(self):
        return hash(self.reference)


def allocate_to_list_of_coils(line: OrderLine, coils: list[Coil]) -> str:
    coil = next(c for c in sorted(coils) if (
        c.can_allocate(line) and
        ((c.available_quantity - line.quantity) >= c.recommended_balance or
         (c.available_quantity - line.quantity) <= c.acceptable_loss)
    ))
    coil.allocate(line)
    return coil.reference
