from typing import Protocol
from django.db import transaction

from allocation.adapters import repository


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
    """
    Поддерживает протокол менеджера контекста в целях реализации паттерна «Unit of Work».
    При использовании экземпляра класса с инструкцией with создается экземпляр
    класса-репозитория, который будет работать с одним контекстом данных.
    """
    def __enter__(self) -> 'DjangoCoilUnitOfWork':
        """
        Выполняется до входа в блок with.
        Создает экземпляр класса-репозитория и отключает автокоммит транзакций с базой данных.
        Возвращает экземпляр класса DjangoCoilUnitOfWork.
        """
        self.coil_repo = repository.DjangoCoilRepository()
        transaction.set_autocommit(False)
        return self

    def __exit__(self, *args):
        """
        Выполняется после выхода из блока with.
        Запускает метод rollback(), который сработает, если в блоке with не был запущен метод commit().
        Включает автокоммит транзакций с базой данных.
        """
        self.rollback()
        transaction.set_autocommit(True)

    def commit(self):
        """
        Обеспечивает фиксацию изменений, выполненных в базе данных,
        при выполнении операций в блоке with.
        """
        transaction.commit()

    def rollback(self):
        """
        Обеспечивает отмену изменений, выполненных в базе данных,
        при выполнении операций в блоке with.
        """
        transaction.rollback()


class DjangoOrderLineUnitOfWork:
    """
    Поддерживает протокол менеджера контекста в целях реализации паттерна «Unit of Work».
    При использовании экземпляра класса с инструкцией with создается экземпляр
    класса-репозитория, который будет работать с одним контекстом данных.
    """
    def __enter__(self) -> 'DjangoOrderLineUnitOfWork':
        """
        Выполняется до входа в блок with.
        Создает экземпляр класса-репозитория и отключает автокоммит транзакций с базой данных.
        Возвращает экземпляр класса DjangoOrderLineUnitOfWork.
        """
        self.line_repo = repository.DjangoOrderLineRepository()
        transaction.set_autocommit(False)
        return self

    def __exit__(self, *args):
        """
        Выполняется после выхода из блока with.
        Запускает метод rollback(), который сработает, если в блоке with не был запущен метод commit().
        Включает автокоммит транзакций с базой данных.
        """
        self.rollback()
        transaction.set_autocommit(True)

    def commit(self):
        """
        Обеспечивает фиксацию изменений, выполненных в базе данных,
        при выполнении операций в блоке with.
        """
        transaction.commit()

    def rollback(self):
        """
        Обеспечивает отмену изменений, выполненных в базе данных,
        при выполнении операций в блоке with.
        """
        transaction.rollback()
