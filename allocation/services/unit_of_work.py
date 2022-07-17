from typing import Any, Protocol
from django.db import transaction

from allocation.adapters import repository


class AbstractUnitOfWork(Protocol):
    coil_repo: repository.AbstractCoilRepository
    line_repo: repository.AbstractOrderLineRepository

    def __enter__(self) -> 'AbstractUnitOfWork': ...

    def __exit__(self, *args: tuple[Any]) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class DjangoUnitOfWork(AbstractUnitOfWork):
    """
    Поддерживает протокол менеджера контекста в целях реализации паттерна «Unit of Work».
    При использовании экземпляра класса с инструкцией with создаются экземпляры
    классов-репозиториев, которые будут работать с одним контекстом данных.
    """
    def __enter__(self) -> 'DjangoUnitOfWork':
        """
        Выполняется до входа в блок with.
        Создает экземпляры классов-репозиториев и отключает автокоммит транзакций с базой данных.
        Возвращает экземпляр класса DjangoUnitOfWork.
        """
        self.coil_repo = repository.DjangoCoilRepository()
        self.line_repo = repository.DjangoOrderLineRepository()
        transaction.set_autocommit(False)
        return self

    def __exit__(self, *args: tuple[Any]) -> None:
        """
        Выполняется после выхода из блока with.
        Запускает метод rollback(), который сработает, если в блоке with не был запущен метод commit().
        Включает автокоммит транзакций с базой данных.
        """
        self.rollback()
        transaction.set_autocommit(True)

    def commit(self) -> None:
        """
        Обеспечивает фиксацию изменений, выполненных в базе данных,
        при выполнении операций в блоке with.
        """
        transaction.commit()

    def rollback(self) -> None:
        """
        Обеспечивает отмену изменений, выполненных в базе данных,
        при выполнении операций в блоке with.
        """
        transaction.rollback()
