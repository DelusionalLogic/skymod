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
from path import Path
from lupa import LuaRuntime
from distutils.dir_util import copy_tree

lua = LuaRuntime()

def is_subdir(sub, root):
    sub = sub.realpath() / ""
    root = root.realpath() / ""

    return sub.startswith(root)

_functions = []
def lua_function(function):
    _functions.append(function)

@lua_function
def install(context, from_str, to_str=""):
    to = Path(to_str)
    if not is_subdir(context.pkgins / to, context.pkgins):
        raise Exception("Package tried to copy to directory outside its own")

    from_ = Path(from_str).normpath()
    if from_.isabs():
        raise Exception("From glob is not allowed to be absolute")

    from_ = context.source_lookup.translate(from_)

    for d in from_.glob(""):
        from_ = d
        if not is_subdir(from_, context.pkgsrc):
            raise Exception("Package tried to copy from directory outside its own")

        name = from_.name

        if from_.isdir():
            rel_from = from_.relpath(context.pkgsrc)
            context.add_package_file( (rel_from, to / name) )
            for e in from_.walk():
                rel_to = e.relpath(from_)
                rel_from = e.relpath(context.pkgsrc)
                context.add_package_file( (rel_from, to / name / rel_to) )
        else:
            rel_from = from_.relpath(context.pkgsrc)
            context.add_package_file( (rel_from, to / name) )

class RuntimeContext(object):
    def __init__(self, env):
        self.env = env
        self.package_files = []

    def add_package_file(self, entry):
        self.package_files.append(entry)

class RuntimeSandbox(object):
    def __init__(self):
        self.safe_env = lua.eval("{}")
        self.safe_env.print = lua.globals().print
        self.safe_env.type = lua.globals().type
        self.safe_env.fail = lua.globals().error

        self.sandbox_meta = lua.eval("{}")
        self.sandbox_meta["__index"] = self.safe_env
        self.setmeta = lua.eval("setmetatable")

        self.sandboxFile = lua.eval("""
        function(path, env)
            local f = io.open(path, "rb")
            if f == nil then
                print("failed opening file: ", path)
                f:close()
                error()
            end
            if f:read(1) == 27 then return nil, "binary bytecode prohibited" end
            f:close()

            local untrusted_function, message = loadfile(path)
            if not untrusted_function then return nil, message end

            setfenv(untrusted_function, env)
            return untrusted_function()
        end
        """)

    def load_file(self, path):
        sandbox = lua.eval("{}")
        self.setmeta(sandbox, self.sandbox_meta)

        context = RuntimeContext(sandbox)
        for v in _functions:
            sandbox[v.__name__] = lambda *x, v=v: v(context, *x)

        self.sandboxFile(path, sandbox)
        return context
