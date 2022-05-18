from typing import Protocol

from allocation.adapters import repository

from django.db import transaction


class AbstractCoilUnitOfWork(Protocol):
    coil_repo: repository.AbstractCoilRepository

    def __enter__(self) -> 'AbstractCoilUnitOfWork':
        raise NotImplementedError

    def __exit__(self, *args):
        self.rollback()

    @staticmethod
    def commit():
        raise NotImplementedError

    @staticmethod
    def rollback():
        raise NotImplementedError


class AbstractOrderLineUnitOfWork(Protocol):
    line_repo: repository.AbstractOrderLineRepository

    def __enter__(self) -> 'AbstractOrderLineUnitOfWork':
        raise NotImplementedError

    def __exit__(self, *args):
        self.rollback()

    @staticmethod
    def commit():
        raise NotImplementedError

    @staticmethod
    def rollback():
        raise NotImplementedError


class DjangoCoilUnitOfWork:
    def __enter__(self) -> 'DjangoCoilUnitOfWork':
        self.coil_repo = repository.DjangoCoilRepository()
        transaction.set_autocommit(False)
        return self

    def __exit__(self, *args):
        self.rollback()
        transaction.set_autocommit(True)

    @staticmethod
    def commit():
        transaction.commit()

    @staticmethod
    def rollback():
        transaction.rollback()


class DjangoOrderLineUnitOfWork:
    def __enter__(self) -> 'DjangoOrderLineUnitOfWork':
        self.line_repo = repository.DjangoOrderLineRepository()
        transaction.set_autocommit(False)
        return self

    def __exit__(self):
        self.rollback()
        transaction.set_autocommit(True)

    @staticmethod
    def commit():
        transaction.commit()

    @staticmethod
    def rollback():
        transaction.rollback()
