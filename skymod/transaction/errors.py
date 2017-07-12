# Copyright 2017 Jesper Jensen (delusionallogic)
#
# This file is part of skymod.
#
# skymod is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# skymod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with skymod.  If not, see <http://www.gnu.org/licenses/>.
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

