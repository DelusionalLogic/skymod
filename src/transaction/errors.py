class TransactionCycleError(Exception):
    def __init__(self, cycle):
        self.cycle = cycle
        super().__init__()

class MissingDependencyError(Exception):
    def __init__(self, dependencies):
        self.dependencies = dependencies
        super().__init__()

class DependencyBreakError(Exception):
    def __init__(self, dependencies):
        self.dependencies = dependencies
        super().__init__()

class ConflictError(Exception):
    def __init__(self, conflicts):
        self.conflicts = conflicts
        super().__init__()

