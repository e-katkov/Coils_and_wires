from typing import Protocol

from allocation.domain import domain_logic
from allocation import models as django_models


class AbstractCoilRepository(Protocol):
    @staticmethod
    def get(reference: str) -> domain_logic.Coil:
        raise NotImplementedError

    @staticmethod
    def add(coil: domain_logic.Coil) -> None:
        raise NotImplementedError

    @staticmethod
    def update(coil: domain_logic.Coil) -> None:
        raise NotImplementedError

    @staticmethod
    def list() -> list[domain_logic.Coil]:
        raise NotImplementedError


class AbstractOrderLineRepository(Protocol):
    @staticmethod
    def add(line: domain_logic.OrderLine) -> None:
        raise NotImplementedError


class DjangoCoilRepository:
    @staticmethod
    def get(reference: str) -> domain_logic.Coil:
        return django_models.Coil.objects.get(reference=reference).to_domain()

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
    def add(line: domain_logic.OrderLine) -> None:
        django_models.OrderLine.create_from_domain(line)
