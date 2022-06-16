import pytest

from allocation.adapters import repository
from allocation.domain.domain_logic import Coil, OrderLine


@pytest.mark.django_db
def test_repository_saves_a_coil():
    coil = Coil('Бухта-020', 'АВВГ_3х1,5', 120, 5, 1)
    repo = repository.DjangoCoilRepository()

    repo.add(coil)
    saved_coil = repo.get(reference='Бухта-020')

    assert saved_coil.reference == coil.reference
    assert saved_coil.product_id == coil.product_id
    assert saved_coil.initial_quantity == coil.initial_quantity
    assert saved_coil.recommended_balance == coil.recommended_balance
    assert saved_coil.acceptable_loss == coil.acceptable_loss


@pytest.mark.django_db
def test_repository_updates_a_coil():
    coil = Coil('Бухта-021', 'АВВГ_2х6', 120, 10, 1)
    line_1 = OrderLine('Заказ-031', 'Позиция-001', 'АВВГ_2х6', 30)
    line_2 = OrderLine('Заказ-032', 'Позиция-001', 'АВВГ_2х6', 35)
    line_3 = OrderLine('Заказ-033', 'Позиция-001', 'АВВГ_2х6', 40)
    # создание экземпляров репозиториев
    repo_coil = repository.DjangoCoilRepository()
    repo_line = repository.DjangoOrderLineRepository()
    # добавление записей моделей Coil и OrderLine в базу данных
    repo_coil.add(coil)
    repo_line.add(line_1)
    repo_line.add(line_2)
    repo_line.add(line_3)
    # размещение OrderLines
    coil.allocate(line_1)
    coil.allocate(line_2)
    coil.allocate(line_3)

    repo_coil.update(coil)

    assert {line.quantity for line in coil.allocations} == {line_1.quantity, line_2.quantity, line_3.quantity}


@pytest.mark.django_db
def test_repository_gets_a_list_of_coils():
    coil_1 = Coil('Бухта-025', 'АВВГ_4х16', 120, 20, 5)
    coil_2 = Coil('Бухта-026', 'АВВГ_2х6', 70, 6, 2)
    repo_coil = repository.DjangoCoilRepository()
    repo_coil.add(coil_1)
    repo_coil.add(coil_2)

    list_of_coils = repo_coil.list()

    assert list_of_coils == [coil_1, coil_2]


@pytest.mark.django_db
def test_repository_updates_a_line():
    # создание экземпляра репозитория
    repo = repository.DjangoOrderLineRepository()
    # добавление coil в базу данных
    old_line = OrderLine('Заказ-033', 'Позиция-003', 'АВВГ_2х2,5', 25)
    repo.add(old_line)
    # создание экземпляра orderline доменной модели
    new_line = OrderLine('Заказ-033', 'Позиция-003', 'АВВГ_2х6', 20)

    repo.update(new_line)
    update_line = repo.get(order_id=old_line.order_id, line_item=old_line.line_item)

    assert update_line.product_id == new_line.product_id
    assert update_line.quantity == new_line.quantity


@pytest.mark.django_db
def test_repository_gets_a_real_allocation_coil():
    # создание экземпляров репозиториев
    repo_line = repository.DjangoOrderLineRepository()
    repo_coil = repository.DjangoCoilRepository()
    # добавление coil и orderline в базу данных
    line = OrderLine('Заказ-034', 'Позиция-002', 'АВВГ_4х16', 35)
    repo_line.add(line)
    coil = Coil('Бухта-024', 'АВВГ_4х16', 150, 25, 5)
    repo_coil.add(coil)
    # размещение orderLine
    coil.allocate(line)
    repo_coil.update(coil)

    output_coil = repo_line.get_an_allocation_coil(line)

    assert output_coil.reference == coil.reference
    assert output_coil.available_quantity == coil.initial_quantity - line.quantity


@pytest.mark.django_db
def test_repository_gets_a_fake_allocation_coil():
    # создание экземпляров репозиториев
    repo_line = repository.DjangoOrderLineRepository()
    repo_coil = repository.DjangoCoilRepository()
    # добавление coil и orderline в базу данных
    line = OrderLine('Заказ-034', 'Позиция-002', 'АВВГ_4х16', 35)
    repo_line.add(line)
    coil = Coil('Бухта-024', 'АВВГ_4х16', 150, 25, 5)
    repo_coil.add(coil)

    output_coil = repo_line.get_an_allocation_coil(line)

    assert output_coil.reference == 'fake'
    assert output_coil.product_id == 'fake'
