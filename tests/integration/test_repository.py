import pytest

from allocation.adapters import repository
from allocation.domain.domain_logic import Coil, OrderLine


@pytest.mark.django_db
def test_repository_get_a_coil():
    repo = repository.DjangoCoilRepository()
    # Добавление бухты в базу данных
    coil = Coil('Бухта-020', 'АВВГ_3х1,5', 150, 3, 1)
    repo.add(coil)

    # Получение бухты из базы данных
    saved_coil = repo.get(reference='Бухта-020')

    assert saved_coil.reference == coil.reference
    assert saved_coil.product_id == coil.product_id


@pytest.mark.django_db
def test_repository_save_a_coil():
    repo = repository.DjangoCoilRepository()
    # Создание бухты
    coil = Coil('Бухта-020', 'АВВГ_3х1,5', 120, 5, 1)

    # Добавление бухты в базу данных
    repo.add(coil)
    # Получение бухты из базы данных
    saved_coil = repo.get(reference='Бухта-020')

    assert saved_coil.reference == coil.reference
    assert saved_coil.product_id == coil.product_id


@pytest.mark.django_db
def test_repository_update_a_coil():
    repo_coil = repository.DjangoCoilRepository()
    repo_line = repository.DjangoOrderLineRepository()
    # Добавление бухты в базу данных
    coil = Coil('Бухта-021', 'АВВГ_2х6', 120, 10, 1)
    repo_coil.add(coil)
    # Добавление товарных позиций в базу данных и их размещение в бухтах
    line_1 = OrderLine('Заказ-031', 'Позиция-001', 'АВВГ_2х6', 30)
    line_2 = OrderLine('Заказ-032', 'Позиция-001', 'АВВГ_2х6', 35)
    repo_line.add(line_1)
    repo_line.add(line_2)
    coil.allocate(line_1)
    coil.allocate(line_2)

    # Обновление бухты в базе данных добавит две товарные позиции во множество allocations
    repo_coil.update(coil)
    update_coil = repo_coil.get(reference=coil.reference)

    assert update_coil.allocations == {line_1, line_2}
    assert update_coil.available_quantity == 55


@pytest.mark.django_db
def test_repository_delete_a_coil():
    repo = repository.DjangoCoilRepository()
    # Добавление бухты в базу данных
    coil = Coil('Бухта-021', 'АВВГ_2х2,5', 150, 5, 1)
    repo.add(coil)

    # Удаление бухты из базы данных
    repo.delete(reference=coil.reference)

    # Список сохраненных в базе данных бухт будет пустым
    assert repo.coils_list() == []


@pytest.mark.django_db
def test_repository_get_a_list_of_coils():
    repo = repository.DjangoCoilRepository()
    # Добавление бухт в базу данных
    coil_1 = Coil('Бухта-022', 'АВВГ_4х16', 120, 20, 5)
    coil_2 = Coil('Бухта-023', 'АВВГ_2х6', 70, 6, 2)
    repo.add(coil_1)
    repo.add(coil_2)

    # Получение списка имеющихся в базе данных бухт
    list_of_coils = repo.coils_list()

    assert list_of_coils == [coil_1, coil_2]


@pytest.mark.django_db
def test_repository_get_a_line():
    repo = repository.DjangoOrderLineRepository()
    # Добавление товарной позиции в базу данных
    line = OrderLine('Заказ-033', 'Позиция-004', 'АВВГ_2х2,5', 30)
    repo.add(line)

    # Получение товарной позиции из базы данных
    saved_line = repo.get(order_id='Заказ-033', line_item='Позиция-004')

    assert saved_line.product_id == line.product_id
    assert saved_line.quantity == line.quantity


@pytest.mark.django_db
def test_repository_save_a_line():
    repo = repository.DjangoOrderLineRepository()
    # Создание товарной позиции
    line = OrderLine('Заказ-034', 'Позиция-002', 'АВВГ_2х2,5', 42)

    # Добавление товарной позиции в базу данных
    repo.add(line)
    # Получение товарной позиции из базы данных
    saved_line = repo.get(order_id='Заказ-034', line_item='Позиция-002')

    assert saved_line.product_id == line.product_id
    assert saved_line.quantity == line.quantity


@pytest.mark.django_db
def test_repository_update_a_line():
    repo = repository.DjangoOrderLineRepository()
    # Добавление товарной позиции в базу данных
    old_line = OrderLine('Заказ-035', 'Позиция-003', 'АВВГ_2х2,5', 25)
    repo.add(old_line)
    # Создание товарной позиции
    new_line = OrderLine('Заказ-035', 'Позиция-003', 'АВВГ_2х6', 20)

    # Обновление товарной позиции
    repo.update(new_line)
    update_line = repo.get(order_id=old_line.order_id, line_item=old_line.line_item)

    assert update_line.product_id == new_line.product_id
    assert update_line.quantity == new_line.quantity


@pytest.mark.django_db
def test_repository_delete_a_line():
    repo = repository.DjangoOrderLineRepository()
    # Добавление товарной позиции в базу данных
    line = OrderLine('Заказ-036', 'Позиция-005', 'АВВГ_4х16', 25)
    repo.add(line)

    # Удаление товарной позиции из базы данных
    repo.delete(order_id=line.order_id, line_item=line.line_item)

    # Список сохраненных в базе данных товарных позиций будет пустым
    assert repo.order_lines_list() == []


@pytest.mark.django_db
def test_repository_get_a_list_of_lines():
    repo = repository.DjangoOrderLineRepository()
    # Добавление товарных позиций в базу данных
    line_1 = OrderLine('Заказ-037', 'Позиция-001', 'АВВГ_2х6', 37)
    line_2 = OrderLine('Заказ-038', 'Позиция-003', 'АВВГ_2х2,5', 15)
    repo.add(line_1)
    repo.add(line_2)

    # Получение списка имеющихся в базе данных товарных позиций
    list_of_lines = repo.order_lines_list()

    assert list_of_lines == [line_1, line_2]
