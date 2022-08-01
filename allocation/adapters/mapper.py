from allocation import models as django_models
from allocation.domain import domain_logic


def coil_record_to_domain(coil_record: django_models.CoilDB) -> domain_logic.Coil:
    """Создает экземпляр класса Coil доменной модели в соответствии с полученной записью таблицы CoilDB."""
    coil_domain = domain_logic.Coil(reference=coil_record.reference,
                                    product_id=coil_record.product_id,
                                    quantity=coil_record.quantity,
                                    recommended_balance=coil_record.recommended_balance,
                                    acceptable_loss=coil_record.acceptable_loss)
    coil_domain.allocations = set(orderline_record_to_domain(a.orderline_record) for a in
                                  coil_record.allocationdb_set.all())
    return coil_domain


def orderline_record_to_domain(orderline_record: django_models.OrderLineDB) -> domain_logic.OrderLine:
    """Создает экземпляр класса OrderLine доменной модели в соответствии с полученной записью таблицы OrderLineDB."""
    orderline_domain = domain_logic.OrderLine(order_id=orderline_record.order_id,
                                              line_item=orderline_record.line_item,
                                              product_id=orderline_record.product_id,
                                              quantity=orderline_record.quantity)
    return orderline_domain
