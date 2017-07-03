import networkx as nx
from networkx.algorithms.traversal.depth_first_search import dfs_tree
from networkx.algorithms.approximation.connectivity import local_node_connectivity

import query as Q

#@ENHANCE: Right now the strategy is baked into the solver. Maybe pull that out
class DependencySolver(object):
    def __init__(self, repo, local_repo):
        self.repo = repo
        self.local_repo = local_repo
        pass

    def _find_satisfier_in_targets(self, targets, query):
        for t in targets:
            if query.matches(t):
                return t
        return None

    def _find_satisfier(self, targets, q):
        dep_package = self._find_satisfier_in_targets(targets, q)
        if dep_package is not None:
            return dep_package
        dep_package = self.local_repo.find_package(q)
        if dep_package is not None:
            return dep_package
        candidates = self.repo.find_packages(q)
        if len(candidates) == 1:
            return candidates.pop()
        return Q.option("Possible candidates for {}".format(q), candidates)

    def _expand_dependencies_to_graph(self, targets):
        G = nx.DiGraph()
        targets_copy = list(targets)
        queue = list(targets)
        seen = set(targets)
        while queue:
            package = queue.pop()
            G.add_node(package)
            for dep_name in package.dependecies:
                q = Query(dep_name)
                dep_package = self._find_satisfier(targets_copy, q)
                if dep_package is None:
                    self.unresolved.append(q)
                    continue

                G.add_edge(package, dep_package)
                if not dep_package in seen:
                    targets_copy.append(dep_package)
                    seen.add(dep_package)
                    queue.append(dep_package)
        return G

    def expand_packages(self, packages):
        G = self._expand_dependencies_to_graph(packages)
        return DependencyGraph(G)

# DependencyGraph shows the dependencies of a single package it can only have
# one root, specified at instantiation time
class DependencyGraph(object):
    def __init__(self, G, root):
        self.G = G
        self.root = root

    def present(self):
        from asciinet import graph_to_ascii
        print(graph_to_ascii(self.G))

    def subtree_from(self, package):
        return DependencyGraph(dfs_tree(self.G, package))

    def exclude_subtree_from(self, package):
        sub = dfs_tree(self.G, package)
        seen = {package}
        for n in sub.nodes():
            if n in seen:
                continue
            seen.add(n)
            if local_node_connectivity(self.G, self.root, n) > 1:
                sub.remove_nodes_from(DependencyGraph(sub).exclude_subtree_from(n))
        return DependencyGraph(sub)

    def __iter__(self):
        return self.G.__iter__()

