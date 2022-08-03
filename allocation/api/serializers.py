from pydantic import BaseModel, Field

from allocation.domain.domain_logic import Coil, OrderLine, coil_validation_patterns, orderline_validation_patterns


class CoilBaseModel(BaseModel):
    """
    Принимает данные для инициализации экземпляра класса, выполняет их синтаксический анализ и проверку.
    Возвращает экземпляр класса, поля которого соответствуют типам полей, определенных в классе.
    Генерирует ошибку ValidationError, возникающую в случае указанного несоответствия.
    """
    reference: str = Field(regex=coil_validation_patterns['reference'])
    product_id: str
    quantity: int = Field(gt=0)
    recommended_balance: int = Field(gt=0)
    acceptable_loss: int = Field(gt=0)
    allocations: list = []


class OrderLineBaseModel(BaseModel):
    """
    Принимает данные для инициализации экземпляра класса, выполняет их синтаксический анализ и проверку.
    Возвращает экземпляр класса, поля которого соответствуют типам полей, определенных в классе.
    Генерирует ошибку ValidationError, возникающую в случае указанного несоответствия.
    """
    order_id: str = Field(regex=orderline_validation_patterns['order_id'])
    line_item: str = Field(regex=orderline_validation_patterns['line_item'])
    product_id: str
    quantity: int = Field(gt=0)


def serialize_coil_domain_instance_to_json(domain_instance: Coil) -> str:
    """
    Принимает бухту - экземпляр класса Coil доменной модели, создает соответствующий ей
    экземпляр класса CoilBaseModel, выполняя тем самым синтаксический анализ и проверку.
    Сериализует экземпляр класса в объект JSON и возвращает его.
    Экземпляры класса OrderLine доменной модели, находящиеся в allocations, также
    проверяются и сериализуются в объекты JSON.
    """
    model_instance = CoilBaseModel(
        reference=domain_instance.reference,
        product_id=domain_instance.product_id,
        quantity=domain_instance.initial_quantity,
        recommended_balance=domain_instance.recommended_balance,
        acceptable_loss=domain_instance.acceptable_loss,
        allocations=[serialize_order_line_domain_instance_to_json(line)
                     for line in domain_instance.allocations],
    )
    return model_instance.json(ensure_ascii=False)


def serialize_order_line_domain_instance_to_json(domain_instance: OrderLine) -> str:
    """
    Принимает товарную позицию - экземпляр класса OrderLine доменной модели,
    создает соответствующий ей экземпляр класса OrderLineBaseModel,
    выполняя тем самым синтаксический анализ и проверку.
    Сериализует экземпляр класса в объект JSON и возвращает его.
    """
    model_instance = OrderLineBaseModel(
        order_id=domain_instance.order_id,
        line_item=domain_instance.line_item,
        product_id=domain_instance.product_id,
        quantity=domain_instance.quantity,
    )
    return model_instance.json(ensure_ascii=False)
