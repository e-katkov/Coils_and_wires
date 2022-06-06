from allocation.domain import domain_logic
from allocation.services import services


class FakeCoilRepository:
    coils: set[domain_logic.Coil] = set()

    @staticmethod
    def get(reference: str) -> domain_logic.Coil:
        return next(c for c in FakeCoilRepository.coils if c.reference == reference)

    @staticmethod
    def add(coil: domain_logic.Coil) -> None:
        FakeCoilRepository.coils.add(coil)

    @staticmethod
    def update(coil: domain_logic.Coil) -> None:
        discard_coil = next(c for c in FakeCoilRepository.coils if c.reference == coil.reference)
        FakeCoilRepository.coils.discard(discard_coil)
        FakeCoilRepository.coils.add(coil)

    @staticmethod
    def list() -> list[domain_logic.Coil]:
        return list(FakeCoilRepository.coils)


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
    lines: set[domain_logic.OrderLine] = set()

    @staticmethod
    def get(order_id: str, line_item: str) -> domain_logic.OrderLine:
        return next(l for l in FakeOrderLineRepository.lines if l.order_id == order_id and l.line_item == line_item)

    @staticmethod
    def add(line: domain_logic.OrderLine) -> None:
        FakeOrderLineRepository.lines.add(line)


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

    result_coil = services.allocate('Заказ-051', 'Позиция-001', uow_line, uow_coil)

    assert result_coil.reference == 'Бухта-042'
    assert result_coil.available_quantity == 34
    #во множестве coils находится coil со значением reference='Бухта-041',
    # у которого не произошло уменьшение available_quantity после размещения/аллокации
    assert next(c for c in uow_coil.coil_repo.coils if c.reference == 'Бухта-041').available_quantity == 70
