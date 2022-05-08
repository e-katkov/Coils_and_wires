from dataclasses import dataclass


@dataclass(frozen=True)
class OrderLine:
    order_id: str
    product_id: str
    quantity: int


class Coil:
    def __init__(
            self,
            reference: str,
            product_id: str,
            quantity: int
    ):
        self.reference = reference
        self.product_id = product_id
        self.available_quantity = quantity

    def allocate(self, line: OrderLine):
        self.available_quantity -= line.quantity
