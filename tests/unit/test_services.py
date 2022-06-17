from allocation.domain import domain_logic
from allocation.services import services


class FakeCoilRepository:
    def __init__(self):
        self.coils: set[domain_logic.Coil] = set()

    def get(self, reference: str) -> domain_logic.Coil:
        return next(c for c in self.coils if c.reference == reference)

    def add(self, coil: domain_logic.Coil) -> None:
        self.coils.add(coil)

    def update(self, coil: domain_logic.Coil) -> None:
        discard_coil = next(c for c in self.coils if c.reference == coil.reference)
        self.coils.discard(discard_coil)
        self.coils.add(coil)

    def delete(self, reference: str) -> set[domain_logic.OrderLine]:
        discarded_coil = next(c for c in self.coils if c.reference == reference)
        deallocated_lines = discarded_coil.allocations
        self.coils.discard(discarded_coil)
        return deallocated_lines

    def list(self) -> list[domain_logic.Coil]:
        return list(self.coils)


class FakeCoilUnitOfWork:
    def __init__(self):
        self.coil_repo = FakeCoilRepository()
        self.committed = False

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeOrderLineRepository:
    def __init__(self):
        self.lines: set[domain_logic.OrderLine] = set()

    def get(self, order_id: str, line_item: str) -> domain_logic.OrderLine:
        return next(line for line in self.lines if line.order_id == order_id and line.line_item == line_item)

    def add(self, line: domain_logic.OrderLine) -> None:
        self.lines.add(line)


class FakeOrderLineUnitOfWork:
    def __init__(self):
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


def test_get_a_coil():
    uow = FakeCoilUnitOfWork()
    services.add_a_coil('Бухта-015', 'АВВГ_3х1,5', 70, 10, 2, uow)
    services.add_a_coil('Бухта-016', 'АВВГ_2х2,5', 200, 15, 3, uow)

    coil = services.get_a_coil('Бухта-016', uow)

    assert coil.product_id == 'АВВГ_2х2,5'
    assert coil.recommended_balance == 15


def test_add_a_coil():
    uow = FakeCoilUnitOfWork()

    services.add_a_coil('Бухта-040', 'АВВГ_2х2,5', 200, 15, 3, uow)

    assert uow.coil_repo.get('Бухта-040') is not None
    assert uow.committed


def test_update_a_coil():
    uow_coil = FakeCoilUnitOfWork()
    uow_line = FakeOrderLineUnitOfWork()
    services.add_a_coil('Бухта-051', 'АВВГ_2х2,5', 100, 20, 3, uow_coil)
    services.add_a_line('Заказ-052', 'Позиция-002', 'АВВГ_2х2,5', 40, uow_line)
    services.add_a_line('Заказ-053', 'Позиция-001', 'АВВГ_2х2,5', 35, uow_line)
    services.allocate('Заказ-052', 'Позиция-002', uow_line, uow_coil)
    services.allocate('Заказ-053', 'Позиция-001', uow_line, uow_coil)

    deallocated_lines = services.update_a_coil('Бухта-051', 'АВВГ_2х2,5', 80, 20, 3, uow_coil)

    assert uow_coil.coil_repo.get('Бухта-051').allocated_quantity == 35
    assert {(line.order_id, line.line_item) for line in deallocated_lines} == {('Заказ-052', 'Позиция-002')}
    assert uow_coil.committed


def test_delete_a_coil():
    # Создание "поддельных" классов UnitOfWork
    uow_coil = FakeCoilUnitOfWork()
    uow_line = FakeOrderLineUnitOfWork()
    # Создание coil
    services.add_a_coil('Бухта-052', 'АВВГ_2х6', 150, 20, 5, uow_coil)
    # Создание и размещение orderline
    services.add_a_line('Заказ-054', 'Позиция-002', 'АВВГ_2х6', 50, uow_line)
    services.allocate('Заказ-054', 'Позиция-002', uow_line, uow_coil)

    deallocated_lines = services.delete_a_coil('Бухта-052', uow_coil)

    assert {(line.order_id, line.line_item) for line in deallocated_lines} == {('Заказ-054', 'Позиция-002')}
    assert uow_coil.committed


def test_get_a_line():
    uow = FakeOrderLineUnitOfWork()
    services.add_a_line('Заказ-061', 'Позиция-001', 'АВВГ_2х6', 20, uow)
    services.add_a_line('Заказ-061', 'Позиция-002', 'АВВГ_2х2,5', 25, uow)

    line = services.get_a_line('Заказ-061', 'Позиция-002', uow)

    assert line.line_item == 'Позиция-002'
    assert line.product_id == 'АВВГ_2х2,5'


def test_add_a_line():
    uow = FakeOrderLineUnitOfWork()

    services.add_a_line('Заказ-050', 'Позиция-001', 'АВВГ_2х6', 16, uow)

    assert uow.line_repo.get('Заказ-050', 'Позиция-001') is not None
    assert uow.committed


def test_allocate_returns_allocation():
    uow_coil = FakeCoilUnitOfWork()
    uow_line = FakeOrderLineUnitOfWork()
    services.add_a_coil('Бухта-041', 'АВВГ_2х6', 70, 15, 3, uow_coil)
    services.add_a_coil('Бухта-042', 'АВВГ_2х6', 50, 15, 3, uow_coil)
    services.add_a_line('Заказ-051', 'Позиция-001', 'АВВГ_2х6', 16, uow_line)
    services.add_a_line('Заказ-051', 'Позиция-002', 'АВВГ_2х6', 10, uow_line)

    services.allocate('Заказ-051', 'Позиция-001', uow_line, uow_coil)
    result_coil = services.allocate('Заказ-051', 'Позиция-002', uow_line, uow_coil)

    assert result_coil.reference == 'Бухта-042'
    assert result_coil.available_quantity == 24
