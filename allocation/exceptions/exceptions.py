class OutOfStock(Exception):
    pass

class DBCoilRecordDoesNotExist(Exception):
    pass


class DBOrderLineRecordDoesNotExist(Exception):
    pass


class DBCoilRecordAlreadyExist(Exception):
    pass


class DBOrderLineRecordAlreadyExist(Exception):
    pass
