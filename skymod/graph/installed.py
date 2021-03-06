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
import networkx as nx
from networkx.algorithms.approximation.connectivity import (
    local_node_connectivity
)
from networkx.algorithms.traversal.depth_first_search import dfs_tree


class RootNode(object):
    def __init__(self):
        self.name = None

    def __str__(self):
        return "Installed"

# An installed graph is supposed to represent all the packages currently
# installed
# An InstalledGraph has multiple package "roots" augmented with a fake super
# root pointing at everything explicitly installed
class InstalledGraph(object):
    def __init__(self, G):
        self.G = G

    def from_depends(subtrees):
        G = nx.DiGraph()
        root = RootNode()
        for subG in subtrees:
            self.G = nx.compose(G, subG.G)
            self.G.add_edge(root, subG.root)
        return InstalledGraph(G, root)

    def exclude_subtree_from(self, package):
        sub = dfs_tree(self.G, package)
        root = nx.topological_sort(self.G)[0]
        seen = {package}
        for n in sub.nodes():
            if n in seen:
                continue
            seen.add(n)
            if local_node_connectivity(self.G, root, n) > 1:
                sub.remove_nodes_from(InstalledGraph(sub).exclude_subtree_from(n))
        return InstalledGraph(sub)

    def present(self):
        print(graph_to_ascii(self.G))

    def __iter__(self):
        return self.G.__iter__()
