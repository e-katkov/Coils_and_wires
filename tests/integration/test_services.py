from allocation.domain import domain_logic
from allocation.services import services


class FakeCoilRepository:
    """
    "Поддельная" версия репозитория для бухт,
    которая позволяет не обращаться к базе данных при тестировании.
    """
    def __init__(self):
        # Множество экземпляров бухт, используемое при тестировании в качестве хранилища
        self.coils: set[domain_logic.Coil] = set()

    def get(self, reference: str) -> domain_logic.Coil:
        result_coil = next(coil for coil in self.coils if coil.reference == reference)
        return result_coil

    def add(self, coil: domain_logic.Coil) -> None:
        self.coils.add(coil)

    def update(self, coil: domain_logic.Coil) -> None:
        discarded_coil = next(c for c in self.coils if c.reference == coil.reference)
        self.coils.discard(discarded_coil)
        self.coils.add(coil)

    def delete(self, reference: str) -> set[domain_logic.OrderLine]:
        discarded_coil = next(coil for coil in self.coils if coil.reference == reference)
        deallocated_lines = discarded_coil.allocations
        self.coils.discard(discarded_coil)
        return deallocated_lines

    def coils_list(self) -> list[domain_logic.Coil]:
        return list(self.coils)


class FakeOrderLineRepository:
    """
    "Поддельная" версия репозитория для товарных позиций,
    которая позволяет не обращаться к базе данных при тестировании.
    """
    def __init__(self):
        # Множество экземпляров товарных позиций, используемое при тестировании в качестве хранилища
        self.lines: set[domain_logic.OrderLine] = set()

    def get(self, order_id: str, line_item: str) -> domain_logic.OrderLine:
        result_line = next(line for line in self.lines
                           if line.order_id == order_id and line.line_item == line_item)
        return result_line

    def add(self, line: domain_logic.OrderLine) -> None:
        self.lines.add(line)

    def update(self, line: domain_logic.OrderLine) -> None:
        discarded_line = next(o_line for o_line in self.lines if o_line.order_id == line.order_id
                              and o_line.line_item == line.line_item)
        self.lines.discard(discarded_line)
        self.lines.add(line)

    def delete(self, order_id: str, line_item: str) -> None:
        discarded_line = next(o_line for o_line in self.lines if o_line.order_id == order_id
                              and o_line.line_item == line_item)
        self.lines.discard(discarded_line)

    def order_lines_list(self) -> list[domain_logic.OrderLine]:
        return list(self.lines)


class FakeUnitOfWork:
    """
    "Поддельная" версия класса, реализующего паттерн "Unit of Work",
    которая создает "поддельные" версии репозиториев для бухт и товарных позиций при тестировании.
    """
    def __init__(self):
        self.coil_repo = FakeCoilRepository()
        self.line_repo = FakeOrderLineRepository()
        self.committed = False

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_service_get_a_coil():
    uow = FakeUnitOfWork()
    # Добавление бухты в хранилище
    services.add_a_coil('Бухта-015', 'АВВГ_3х1,5', 70, 10, 2, uow)
    services.add_a_coil('Бухта-016', 'АВВГ_2х2,5', 200, 15, 3, uow)

    # Получение бухты из хранилища
    coil = services.get_a_coil('Бухта-016', uow)

    assert coil.product_id == 'АВВГ_2х2,5'
    assert coil.recommended_balance == 15


def test_service_add_a_coil():
    uow = FakeUnitOfWork()

    # Добавление бухты в хранилище
    services.add_a_coil('Бухта-040', 'АВВГ_2х2,5', 200, 15, 3, uow)
    # Получение бухты из хранилища
    saved_coil = services.get_a_coil('Бухта-040', uow)

    assert saved_coil.product_id == 'АВВГ_2х2,5'
    assert uow.committed


def test_service_update_a_coil():
    """
    Уменьшение изначального количества материала в бухте при ее обновлении
    изменит состав размещенных товарных позиций.
    """
    uow = FakeUnitOfWork()
    # Добавление бухты в хранилище
    services.add_a_coil('Бухта-051', 'АВВГ_2х2,5', 100, 20, 3, uow)
    # Добавление товарных позиций в хранилище и их размещение в бухте
    services.add_a_line('Заказ-052', 'Позиция-002', 'АВВГ_2х2,5', 40, uow)
    services.add_a_line('Заказ-053', 'Позиция-001', 'АВВГ_2х2,5', 35, uow)
    services.allocate('Заказ-052', 'Позиция-002', uow)
    services.allocate('Заказ-053', 'Позиция-001', uow)

    # Обновление бухты возвращает множество товарных позиций,
    # которые перестанут быть размещенными после обновления
    deallocated_lines = services.update_a_coil('Бухта-051', 'АВВГ_2х2,5', 80, 20, 3, uow)
    deallocated_lines_ids_and_line_items = {(line.order_id, line.line_item) for line in deallocated_lines}

    # Обновление бухты приведет к тому, что товарная позиция ('Заказ-052', 'Позиция-002')
    # перестанет быть размещенной
    assert services.get_a_coil('Бухта-051', uow).available_quantity == 45
    assert deallocated_lines_ids_and_line_items == {('Заказ-052', 'Позиция-002')}
    assert uow.committed


def test_service_delete_a_coil():
    """Удаление бухты возвращает множество товарных позиций, которые перестанут быть размещенными"""
    uow = FakeUnitOfWork()
    # Добавление бухты в хранилище
    services.add_a_coil('Бухта-052', 'АВВГ_2х6', 150, 20, 5, uow)
    # Добавление товарных позиций в хранилище и их размещение в бухте
    services.add_a_line('Заказ-054', 'Позиция-002', 'АВВГ_2х6', 50, uow)
    services.add_a_line('Заказ-055', 'Позиция-003', 'АВВГ_2х6', 64, uow)
    services.allocate('Заказ-054', 'Позиция-002', uow)
    services.allocate('Заказ-055', 'Позиция-003', uow)

    # Удаление бухты возвращает множество товарных позиций,
    # которые перестанут быть размещенными
    deallocated_lines = services.delete_a_coil('Бухта-052', uow)
    deallocated_lines_ids_and_line_items = {(line.order_id, line.line_item) for line in deallocated_lines}

    # Удаление бухты приведет к тому, что обе товарных позиции
    # перестанут быть размещенными
    assert deallocated_lines_ids_and_line_items == {('Заказ-054', 'Позиция-002'),
                                                    ('Заказ-055', 'Позиция-003')}
    assert uow.committed


def test_service_get_a_line():
    uow = FakeUnitOfWork()
    # Добавление товарных позиций в хранилище
    services.add_a_line('Заказ-061', 'Позиция-001', 'АВВГ_2х6', 20, uow)
    services.add_a_line('Заказ-061', 'Позиция-002', 'АВВГ_2х2,5', 25, uow)

    # Получение товарной позиции из хранилища
    line = services.get_a_line('Заказ-061', 'Позиция-002', uow)

    assert line.product_id == 'АВВГ_2х2,5'
    assert line.quantity == 25


def test_service_add_a_line():
    uow = FakeUnitOfWork()

    # Добавление товарной позиции в хранилище
    services.add_a_line('Заказ-050', 'Позиция-001', 'АВВГ_2х6', 16, uow)
    # Получение товарной позиции из хранилища
    saved_line = services.get_a_line('Заказ-050', 'Позиция-001', uow)

    assert saved_line.product_id == 'АВВГ_2х6'
    assert uow.committed


def test_service_update_a_line():
    """
    Увеличение количества материала в товарной позиции при обновлении
    приведет к ее переразмещению.
    """
    uow = FakeUnitOfWork()
    # Добавление бухт в хранилище
    services.add_a_coil('Бухта-055', 'АВВГ_2х2,5', 80, 15, 2, uow)
    services.add_a_coil('Бухта-056', 'АВВГ_2х2,5', 120, 15, 2, uow)
    # Добавление товарной позиции в хранилище и ее размещение в бухте
    services.add_a_line('Заказ-008', 'Позиция-002', 'АВВГ_2х2,5', 24, uow)
    services.allocate('Заказ-008', 'Позиция-002', uow)
    # Получение бухты, в которой размещена товарная позиция
    allocation_coil_1 = services.get_an_allocation_coil('Заказ-008', 'Позиция-002', uow)

    # Обновление товарной позиции возвращает бухту, в которой она будет размещена
    allocation_coil_2 = services.update_a_line('Заказ-008', 'Позиция-002', 'АВВГ_2х2,5', 90, uow)

    # Обновление товарной позиции приведет к ее переразмещению
    assert allocation_coil_1.reference == 'Бухта-055'
    assert services.get_a_coil('Бухта-055', uow).available_quantity == 80
    assert allocation_coil_2.reference == 'Бухта-056'
    assert allocation_coil_2.available_quantity == 30
    assert uow.committed


def test_service_delete_a_line():
    """Удаление товарной позиции возвращает бухту, в которой она была размещена."""
    uow = FakeUnitOfWork()
    # Добавление бухты в хранилище
    services.add_a_coil('Бухта-056', 'АВВГ_2х2,5', 100, 15, 2, uow)
    # Добавление товарной позиции в хранилище и ее размещение в бухте
    services.add_a_line('Заказ-007', 'Позиция-004', 'АВВГ_2х2,5', 24, uow)
    services.allocate('Заказ-007', 'Позиция-004', uow)

    # Удаление товарной позиции возвращает бухту, в которой она была размещена
    allocation_coil = services.delete_a_line('Заказ-007', 'Позиция-004', uow)

    assert allocation_coil.reference == 'Бухта-056'
    assert services.get_a_coil('Бухта-056', uow).available_quantity == 100
    assert uow.committed


def test_service_get_a_real_allocation_coil():
    """Получение бухты, в которой размещена товарная позиция."""
    uow = FakeUnitOfWork()
    # Добавление бухты в хранилище
    services.add_a_coil('Бухта-058', 'АВВГ_2х6', 170, 20, 3, uow)
    # Добавление товарной позиции в хранилище и ее размещение в бухте
    services.add_a_line('Заказ-012', 'Позиция-002', 'АВВГ_2х6', 52, uow)
    services.allocate('Заказ-012', 'Позиция-002', uow)

    # Получение бухты, в которой размещена товарная позиция
    allocation_coil = services.get_an_allocation_coil('Заказ-012', 'Позиция-002', uow)

    assert allocation_coil.reference == 'Бухта-058'
    assert allocation_coil.available_quantity == 118


def test_service_get_a_fake_allocation_coil():
    """Получение "поддельной" бухты, в которой размещена неразмещенная товарная позиция."""
    uow = FakeUnitOfWork()
    # Добавление бухты в хранилище
    services.add_a_coil('Бухта-058', 'АВВГ_2х6', 170, 20, 3, uow)
    # Добавление товарной позиции в хранилище
    services.add_a_line('Заказ-012', 'Позиция-002', 'АВВГ_2х6', 52, uow)

    # Получение "поддельной" бухты, в которой размещена неразмещенная товарная позиция
    allocation_coil = services.get_an_allocation_coil('Заказ-012', 'Позиция-002', uow)

    assert allocation_coil.reference == 'fake'
    assert allocation_coil.available_quantity == 1


def test_service_allocate_a_line_and_return_allocation_coil():
    """Размещение товарной позиции возвращает бухту, в которой она размещена."""
    uow = FakeUnitOfWork()
    # Добавление бухт в хранилище
    services.add_a_coil('Бухта-041', 'АВВГ_2х6', 70, 15, 3, uow)
    services.add_a_coil('Бухта-042', 'АВВГ_2х6', 50, 15, 3, uow)
    # Добавление товарных позиции в хранилище
    services.add_a_line('Заказ-050', 'Позиция-002', 'АВВГ_2х6', 16, uow)
    services.add_a_line('Заказ-051', 'Позиция-005', 'АВВГ_2х6', 10, uow)

    # Размещение товарной позиции возвращает бухту, в которой она размещена
    result_coil_1 = services.allocate('Заказ-050', 'Позиция-002', uow)
    result_coil_2 = services.allocate('Заказ-051', 'Позиция-005', uow)

    assert result_coil_1.reference == 'Бухта-042'
    assert result_coil_2.reference == 'Бухта-042'
    assert services.get_a_coil('Бухта-042', uow).available_quantity == 24


def test_service_deallocate_a_line_and_return_allocation_coil():
    """Отмена размещения товарной позиции возвращает бухту, в которой она была размещена."""
    uow = FakeUnitOfWork()
    # Добавление бухт в хранилище
    services.add_a_coil('Бухта-041', 'АВВГ_2х6', 70, 15, 3, uow)
    services.add_a_coil('Бухта-042', 'АВВГ_2х6', 50, 15, 3, uow)
    # Добавление товарных позиций в хранилище и их размещение в бухтах
    services.add_a_line('Заказ-050', 'Позиция-002', 'АВВГ_2х6', 16, uow)
    services.add_a_line('Заказ-051', 'Позиция-005', 'АВВГ_2х6', 10, uow)
    services.allocate('Заказ-050', 'Позиция-002', uow)
    services.allocate('Заказ-051', 'Позиция-005', uow)

    # Отмена размещения товарной позиции возвращает бухту, в которой она была размещена
    result_coil_1 = services.deallocate('Заказ-050', 'Позиция-002', uow)
    result_coil_2 = services.deallocate('Заказ-051', 'Позиция-005', uow)

    assert result_coil_1.reference == 'Бухта-042'
    assert result_coil_2.reference == 'Бухта-042'
    assert services.get_a_coil('Бухта-042', uow).available_quantity == 50
