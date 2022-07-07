from allocation.domain.domain_logic import Coil


def test_can_reallocate_enough_orderlines(dict_of_orderlines):
    """
    Увеличение изначального количества материала в бухте не изменит состав
    размещенных товарных позиций после их переразмещения.
    """
    coil = Coil('Бухта-001', 'АВВГ_3х1,5', 60, 15, 3)
    coil.allocations = dict_of_orderlines['set_0'] | dict_of_orderlines['set_1'] | dict_of_orderlines['set_2']
    coil_allocations_quantities = {line.quantity for line in coil.allocations}

    new_coil = Coil('Бухта-001', 'АВВГ_3х1,5', 80, 15, 3)
    reallocated_lines = coil.reallocate(new_coil)
    reallocated_lines_quantities = {line.quantity for line in reallocated_lines}

    assert reallocated_lines_quantities == coil_allocations_quantities


def test_cannot_reallocate_one_orderline(dict_of_orderlines):
    """
    Уменьшение изначальных приемлемых потерь материала в бухте изменит состав
    размещенных товарных позиций после их переразмещения.
    """
    coil = Coil('Бухта-001', 'АВВГ_3х1,5', 60, 15, 3)
    coil.allocations = dict_of_orderlines['set_0'] | dict_of_orderlines['set_1'] | dict_of_orderlines['set_2']
    quantities_of_set_0_set_1 = {line.quantity for line in (dict_of_orderlines['set_0'] |
                                                            dict_of_orderlines['set_1'])}

    new_coil = Coil('Бухта-001', 'АВВГ_3х1,5', 60, 15, 2)
    reallocated_lines = coil.reallocate(new_coil)
    reallocated_lines_quantities = {line.quantity for line in reallocated_lines}

    assert reallocated_lines_quantities == quantities_of_set_0_set_1


def test_cannot_reallocate_two_orderlines(dict_of_orderlines):
    """
    Уменьшение изначальных приемлемых потерь материала и увеличение рекомендуемого остатка материала
    в бухте изменит состав размещенных товарных позиций после их переразмещения.
    """
    coil = Coil('Бухта-001', 'АВВГ_3х1,5', 60, 15, 3)
    coil.allocations = dict_of_orderlines['set_0'] | dict_of_orderlines['set_1'] | dict_of_orderlines['set_2']
    quantities_of_set_0 = {line.quantity for line in dict_of_orderlines['set_0']}

    new_coil = Coil('Бухта-001', 'АВВГ_3х1,5', 60, 17, 2)
    reallocated_lines = coil.reallocate(new_coil)
    reallocated_lines_quantities = {line.quantity for line in reallocated_lines}

    assert reallocated_lines_quantities == quantities_of_set_0
