from enum import Enum

class TransactionState(Enum):
    INIT = 1
    EXPANDED = 2
    PREPARED = 3
    COMMITTED = 4

