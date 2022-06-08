import pytest

from allocation.adapters import repository
from allocation.domain import domain_logic


@pytest.mark.django_db
def test_repository_saves_a_coil():
    coil = domain_logic.Coil('Бухта-020', 'АВВГ_3х1,5', 120, 5, 1)

    repo: repository.AbstractCoilRepository = repository.DjangoCoilRepository()
    repo.add(coil)
    saved_coil = repo.get(reference='Бухта-020')

    assert saved_coil.reference == coil.reference
    assert saved_coil.product_id == coil.product_id
    assert saved_coil._initial_quantity == coil._initial_quantity
    assert saved_coil.recommended_balance == coil.recommended_balance
    assert saved_coil.acceptable_loss == coil.acceptable_loss


@pytest.mark.django_db
def test_repository_updates_a_coil():
    line_1 = domain_logic.OrderLine('Заказ-030', 'Позиция-001', 'АВВГ_2х6', 12)
    line_2 = domain_logic.OrderLine('Заказ-031', 'Позиция-001', 'АВВГ_2х6', 25)
    coil_a = domain_logic.Coil('Бухта-021', 'АВВГ_2х6', 120, 5, 1)
    coil_b = domain_logic.Coil('Бухта-021', 'АВВГ_2х6', 70, 6, 2)

    # создание экземпляров репозиториев
    repo_coil = repository.DjangoCoilRepository()
    repo_line = repository.DjangoOrderLineRepository()
    # добавление записей моделей Coil и OrderLine
    repo_coil.add(coil_a)
    repo_line.add(line_1)
    repo_line.add(line_2)

    # обновление записи модели Coil путем размещения товарной позиции line_1
    coil_a.allocate(line_1)
    repo_coil.update(coil_a)
    # обновление записи модели Coil путем изменения значений полей
    repo_coil.update(coil_b)
    # обновление записи модели Coil путем размещения дополнительной товарной позиции line_2
    coil_c = repo_coil.get(reference='Бухта-021')
    coil_c.allocate(line_2)
    repo_coil.update(coil_c)

    # полученная запись модели Coil
    saved_coil = repo_coil.get(reference='Бухта-021')

    assert saved_coil.reference == coil_b.reference
    assert saved_coil.product_id == coil_b.product_id
    assert saved_coil._initial_quantity == coil_b._initial_quantity
    assert saved_coil.recommended_balance == coil_b.recommended_balance
    assert saved_coil.acceptable_loss == coil_b.acceptable_loss
    assert saved_coil._allocations == {line_1, line_2}


@pytest.mark.django_db
def test_repository_gets_a_list_of_coils():
    coil_1 = domain_logic.Coil('Бухта-025', 'АВВГ_4х16', 120, 20, 5)
    coil_2 = domain_logic.Coil('Бухта-026', 'АВВГ_2х6', 70, 6, 2)

    repo_coil: repository.AbstractCoilRepository = repository.DjangoCoilRepository()
    repo_coil.add(coil_1)
    repo_coil.add(coil_2)

    list_of_coils = repo_coil.list()

    assert list_of_coils == [coil_1, coil_2]
