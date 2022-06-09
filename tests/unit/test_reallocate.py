from allocation.domain.domain_logic import Coil


def test_can_reallocate_enough_orderlines(dict_of_orderlines):
    coil = Coil('Бухта-001', 'АВВГ_3х1,5', 60, 15, 3)
    coil._allocations = dict_of_orderlines['set_0'] | dict_of_orderlines['set_1'] | dict_of_orderlines['set_2']
    # Увеличено значение _initial_quantity=80,
    # ввиду чего будут размещены все OrderLines
    new_coil = Coil('Бухта-001', 'АВВГ_3х1,5', 80, 15, 3)

    deallocated_lines = coil.reallocate(new_coil)

    assert deallocated_lines == set()


def test_cannot_reallocate_one_orderline(dict_of_orderlines):
    coil = Coil('Бухта-001', 'АВВГ_3х1,5', 60, 15, 3)
    coil._allocations = dict_of_orderlines['set_0'] | dict_of_orderlines['set_1'] | dict_of_orderlines['set_2']
    # Уменьшено значение acceptable_loss=2,
    # ввиду чего не смогут быть размещены OrderLines из dict_of_orderlines['set_2']
    new_coil = Coil('Бухта-001', 'АВВГ_3х1,5', 60, 15, 2)

    deallocated_lines = coil.reallocate(new_coil)
    deallocated_lines_quantity_set = {line.quantity for line in deallocated_lines}

    assert deallocated_lines_quantity_set == {line.quantity for line in dict_of_orderlines['set_2']}


def test_cannot_reallocate_two_orderlines(dict_of_orderlines):
    coil = Coil('Бухта-001', 'АВВГ_3х1,5', 60, 15, 3)
    coil._allocations = dict_of_orderlines['set_0'] | dict_of_orderlines['set_1'] | dict_of_orderlines['set_2']
    # Уменьшено значение acceptable_loss=2 и увеличено значение recommended_balance=17
    # ввиду чего не смогут быть размещены OrderLines из dict_of_orderlines['set_1'] и dict_of_orderlines['set_2']
    new_coil = Coil('Бухта-001', 'АВВГ_3х1,5', 60, 17, 2)

    deallocated_lines = coil.reallocate(new_coil)
    deallocated_lines_quantity_set = {line.quantity for line in deallocated_lines}

    assert deallocated_lines_quantity_set == {line.quantity for line in
                                              (dict_of_orderlines['set_1'] | dict_of_orderlines['set_2'])}
