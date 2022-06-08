from allocation.exceptions.exceptions import OutOfStock


class OrderLine:
    def __init__(self, order_id: str, line_item: str, product_id: str, quantity: int):
        self.order_id = order_id
        self.line_item = line_item
        self.product_id = product_id
        self.quantity = quantity

    def __eq__(self, other) -> bool:
        if not isinstance(other, OrderLine):
            return False
        return self.order_id == other.order_id and self.line_item == other.line_item

    def __hash__(self):
        return hash(self.order_id + self.line_item)


class Coil:
    def __init__(self, reference: str, product_id: str, quantity: int,
                 recommended_balance: int, acceptable_loss: int):
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
        result = (self.product_id == line.product_id) and (
                ((self.available_quantity - line.quantity) >= self.recommended_balance) or
                (self.acceptable_loss >= (self.available_quantity - line.quantity) >= 0)
        )
        return result

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


def allocate_to_list_of_coils(line: OrderLine, coils: list[Coil]) -> Coil:
    try:
        coil = next(c for c in sorted(coils) if c.can_allocate(line))
        coil.allocate(line)
        return coil
    except StopIteration:
        raise OutOfStock(f'Недостаточное количество материала с product_id={line.product_id}')
