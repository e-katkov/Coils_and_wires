from typing import Protocol

from allocation.domain import domain_logic
from allocation import models as django_models


class AbstractCoilRepository(Protocol):
    def get(self, reference: str) -> domain_logic.Coil: ...

    def add(self, coil: domain_logic.Coil) -> None: ...

    def update(self, coil: domain_logic.Coil) -> None: ...

    def delete(self, reference: str) -> None: ...

    def list(self) -> list[domain_logic.Coil]: ...


class AbstractOrderLineRepository(Protocol):
    def get(self, order_id: str, line_item: str) -> domain_logic.OrderLine: ...

    def add(self, line: domain_logic.OrderLine) -> None: ...

    def update(self, line: domain_logic.OrderLine) -> None: ...

    def get_an_allocation_coil(self, line: domain_logic.OrderLine) -> domain_logic.Coil: ...

    def delete(self, order_id: str, line_item: str) -> None: ...

    def list(self) -> list[domain_logic.OrderLine]: ...


class DjangoCoilRepository:
    def get(self, reference: str) -> domain_logic.Coil:
        return django_models.Coil.get(reference=reference).to_domain()

    def add(self, coil: domain_logic.Coil) -> None:
        django_models.Coil.create_from_domain(coil)

    def update(self, coil: domain_logic.Coil) -> None:
        django_models.Coil.update_from_domain(coil)

    def delete(self, reference: str) -> None:
        django_models.Coil.delete(reference)

    def list(self) -> list[domain_logic.Coil]:
        return [coil.to_domain() for coil in django_models.Coil.objects.all()]


class DjangoOrderLineRepository:
    def get(self, order_id: str, line_item: str) -> domain_logic.OrderLine:
        return django_models.OrderLine.get(order_id=order_id, line_item=line_item).to_domain()

    def add(self, line: domain_logic.OrderLine) -> None:
        django_models.OrderLine.create_from_domain(line)

    def update(self, line: domain_logic.OrderLine) -> None:
        django_models.OrderLine.update_from_domain(line)

    def get_an_allocation_coil(self, line: domain_logic.OrderLine) -> domain_logic.Coil:
        return django_models.OrderLine.get_an_allocation_coil(line)

    def delete(self, order_id: str, line_item: str) -> None:
        django_models.OrderLine.delete(order_id=order_id, line_item=line_item)

    def list(self) -> list[domain_logic.OrderLine]:
        return [line.to_domain() for line in django_models.OrderLine.objects.all()]
