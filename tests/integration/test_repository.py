import pytest

from allocation.adapters import repository
from allocation.domain.domain_logic import Coil, OrderLine


@pytest.mark.django_db
def test_repository_saves_a_coil():
    # Создание экземпляра репозитория
    repo = repository.DjangoCoilRepository()
    # Создание экземпляра coil
    coil = Coil('Бухта-020', 'АВВГ_3х1,5', 120, 5, 1)

    # Добавление coil в базу данных
    repo.add(coil)
    # Получение из базы данных добавленного coil
    saved_coil = repo.get(reference='Бухта-020')

    assert saved_coil.reference == coil.reference
    assert saved_coil.product_id == coil.product_id
    assert saved_coil.initial_quantity == coil.initial_quantity
    assert saved_coil.recommended_balance == coil.recommended_balance
    assert saved_coil.acceptable_loss == coil.acceptable_loss


@pytest.mark.django_db
def test_repository_updates_a_coil():
    # Создание экземпляров репозиториев
    repo_coil = repository.DjangoCoilRepository()
    repo_line = repository.DjangoOrderLineRepository()
    # Создание coil, orderlines и добавление их в базу данных
    coil = Coil('Бухта-021', 'АВВГ_2х6', 120, 10, 1)
    repo_coil.add(coil)
    line_1 = OrderLine('Заказ-031', 'Позиция-001', 'АВВГ_2х6', 30)
    line_2 = OrderLine('Заказ-032', 'Позиция-001', 'АВВГ_2х6', 35)
    repo_line.add(line_1)
    repo_line.add(line_2)
    # Размещение orderlines
    coil.allocate(line_1)
    coil.allocate(line_2)

    # Обновление coil в базе данных
    repo_coil.update(coil)
    update_coil = repo_coil.get(reference=coil.reference)

    assert {line.quantity for line in update_coil.allocations} == {line_1.quantity, line_2.quantity}


@pytest.mark.django_db
def test_repository_delete_a_coil():
    # Создание экземпляра репозитория
    repo = repository.DjangoCoilRepository()
    # Создание coil и добавление его в базу данных
    coil = Coil('Бухта-021', 'АВВГ_2х2,5', 150, 5, 1)
    repo.add(coil)

    # Удаление coil
    repo.delete(reference=coil.reference)

    assert repo.list() == []


@pytest.mark.django_db
def test_repository_gets_a_list_of_coils():
    # Создание экземпляра репозиотрия
    repo = repository.DjangoCoilRepository()
    # Создание coils и добавление их в базу данных
    coil_1 = Coil('Бухта-022', 'АВВГ_4х16', 120, 20, 5)
    coil_2 = Coil('Бухта-023', 'АВВГ_2х6', 70, 6, 2)
    repo.add(coil_1)
    repo.add(coil_2)

    # Получение списка имеющихся в базе данных coils
    list_of_coils = repo.list()

    assert list_of_coils == [coil_1, coil_2]


@pytest.mark.django_db
def test_repository_updates_a_line():
    # Создание экземпляра репозитория
    repo = repository.DjangoOrderLineRepository()
    # Создание orderline и добавление ее в базу данных
    old_line = OrderLine('Заказ-033', 'Позиция-003', 'АВВГ_2х2,5', 25)
    repo.add(old_line)
    # Создание нового экземпляра orderline
    new_line = OrderLine('Заказ-033', 'Позиция-003', 'АВВГ_2х6', 20)

    # Обновление orderline
    repo.update(new_line)
    update_line = repo.get(order_id=old_line.order_id, line_item=old_line.line_item)

    assert update_line.product_id == new_line.product_id
    assert update_line.quantity == new_line.quantity


@pytest.mark.django_db
def test_repository_delete_a_line():
    # создание экземпляра репозитория
    repo = repository.DjangoOrderLineRepository()
    # Создание orderline и добавление ее в базу данных
    line = OrderLine('Заказ-036', 'Позиция-005', 'АВВГ_4х16', 25)
    repo.add(line)

    # Удаление orderline
    repo.delete(order_id=line.order_id, line_item=line.line_item)

    assert repo.list() == []
