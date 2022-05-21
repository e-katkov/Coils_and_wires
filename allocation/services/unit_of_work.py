from typing import Protocol

from allocation.adapters import repository

from django.db import transaction


class AbstractCoilUnitOfWork(Protocol):
    coil_repo: repository.AbstractCoilRepository

    def __enter__(self) -> 'AbstractCoilUnitOfWork': ...

    def __exit__(self, *args): ...

    def commit(self): ...

    def rollback(self): ...


class AbstractOrderLineUnitOfWork(Protocol):
    line_repo: repository.AbstractOrderLineRepository

    def __enter__(self) -> 'AbstractOrderLineUnitOfWork': ...

    def __exit__(self, *args): ...

    def commit(self): ...

    def rollback(self): ...


class DjangoCoilUnitOfWork:
    def __enter__(self) -> 'DjangoCoilUnitOfWork':
        self.coil_repo = repository.DjangoCoilRepository()
        transaction.set_autocommit(False)
        return self

    def __exit__(self, *args):
        self.rollback()
        transaction.set_autocommit(True)

    def commit(self):
        transaction.commit()

    def rollback(self):
        transaction.rollback()


class DjangoOrderLineUnitOfWork:
    def __enter__(self) -> 'DjangoOrderLineUnitOfWork':
        self.line_repo = repository.DjangoOrderLineRepository()
        transaction.set_autocommit(False)
        return self

    def __exit__(self, *args):
        self.rollback()
        transaction.set_autocommit(True)

    def commit(self):
        transaction.commit()

    def rollback(self):
        transaction.rollback()
