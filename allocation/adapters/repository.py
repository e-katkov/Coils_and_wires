from typing import Protocol

from allocation.domain import domain_logic
from allocation import models as django_models


class AbstractCoilRepository(Protocol):
    @staticmethod
    def get(reference: str) -> domain_logic.Coil: ...

    @staticmethod
    def add(coil: domain_logic.Coil) -> None: ...

    @staticmethod
    def update(coil: domain_logic.Coil) -> None: ...

    @staticmethod
    def list() -> list[domain_logic.Coil]: ...


class AbstractOrderLineRepository(Protocol):
    @staticmethod
    def get(order_id: str, line_item: str) -> domain_logic.OrderLine: ...

    @staticmethod
    def add(line: domain_logic.OrderLine) -> None: ...


class DjangoCoilRepository:
    @staticmethod
    def get(reference: str) -> domain_logic.Coil:
        return django_models.Coil.get(reference=reference).to_domain()

    @staticmethod
    def add(coil: domain_logic.Coil) -> None:
        django_models.Coil.create_from_domain(coil)

    @staticmethod
    def update(coil: domain_logic.Coil) -> None:
        django_models.Coil.update_from_domain(coil)

    @staticmethod
    def list() -> list[domain_logic.Coil]:
        return [coil.to_domain() for coil in django_models.Coil.objects.all()]


class DjangoOrderLineRepository:
    @staticmethod
    def get(order_id: str, line_item: str) -> domain_logic.OrderLine:
        return django_models.OrderLine.objects.get(order_id=order_id, line_item=line_item).to_domain()

    @staticmethod
    def add(line: domain_logic.OrderLine) -> None:
        django_models.OrderLine.create_from_domain(line)

    @staticmethod
    def list() -> list[domain_logic.OrderLine]:
        return [line.to_domain() for line in django_models.OrderLine.objects.all()]
