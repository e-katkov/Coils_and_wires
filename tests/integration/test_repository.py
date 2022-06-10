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
    assert saved_coil._initial_quantity == coil._initial_quantity
    assert saved_coil.recommended_balance == coil.recommended_balance
    assert saved_coil.acceptable_loss == coil.acceptable_loss


@pytest.mark.django_db
def test_repository_updates_a_coil():
    old_coil = Coil('Бухта-021', 'АВВГ_2х6', 120, 10, 1)
    line_1 = OrderLine('Заказ-031', 'Позиция-001', 'АВВГ_2х6', 30)
    line_2 = OrderLine('Заказ-032', 'Позиция-001', 'АВВГ_2х6', 35)
    line_3 = OrderLine('Заказ-033', 'Позиция-001', 'АВВГ_2х6', 40)
    # создание экземпляров репозиториев
    repo_coil = repository.DjangoCoilRepository()
    repo_line = repository.DjangoOrderLineRepository()
    # добавление записей моделей Coil и OrderLine в базу данных
    repo_coil.add(old_coil)
    repo_line.add(line_1)
    repo_line.add(line_2)
    repo_line.add(line_3)
    # размещение OrderLines
    old_coil.allocate(line_1)
    old_coil.allocate(line_2)
    old_coil.allocate(line_3)
    repo_coil.update(old_coil)

    # обновление в базе данных записи модели Coil
    new_coil = Coil('Бухта-021', 'АВВГ_2х6', 80, 10, 1)
    repo_coil.update(new_coil)
    # полученная запись модели Coil
    saved_coil = repo_coil.get(reference='Бухта-021')

    assert {line.quantity for line in saved_coil._allocations} == {line_1.quantity, line_2.quantity}


@pytest.mark.django_db
def test_repository_gets_a_list_of_coils():
    coil_1 = Coil('Бухта-025', 'АВВГ_4х16', 120, 20, 5)
    coil_2 = Coil('Бухта-026', 'АВВГ_2х6', 70, 6, 2)
    repo_coil = repository.DjangoCoilRepository()
    repo_coil.add(coil_1)
    repo_coil.add(coil_2)

    list_of_coils = repo_coil.list()

    assert list_of_coils == [coil_1, coil_2]
