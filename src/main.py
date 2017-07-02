import click
import os
from config.runtimesandbox import RuntimeSandbox
from urllib.parse import urlparse
from path import Path
import patoolib
from lupa import LuaError
import query as Q
import humanize

from cfg import config as cfg

from package import LuaPackageConfigProxy
from package import load_config
from package import Version, InstallReason

from repository import GitRemotePackageRepo
from repository import LocalPackageRepo
from repository import Query

from transaction import AddTransaction, RemoveTransaction
from transaction import TransactionCycleError, DependencyBreakError, ConflictError, MissingDependencyError

from downloader import Downloader, NexusHandler, LoversLabHandler, StubHandler

from graph.dependency import DependencySolver

from colorama import Fore, Style
import colorama

colorama.init()

@click.group()
def cli():
    pass

@cli.group()
def cache():
    pass

@cache.command()
def clear():
    cache_dir = cfg.cache.dir
    source_dir = cfg.source.dir
    if not Q.yes_no("Are you sure? This will remove cache and source dir", default="no"):
        return

    for d in cache_dir.dirs():
        d.rmtree()

    for d in source_dir.dirs():
        d.rmtree()

@cache.command()
def size():
    cache_dir = cfg.cache.dir
    source_dir = cfg.source.dir

    cache_size = 0
    for f in cache_dir.walkfiles():
        cache_size += f.size

    source_size = 0
    for f in source_dir.walkfiles():
        source_size += f.size

    print("{Style.BRIGHT}Cache: {Style.RESET_ALL} {}".format(humanize.naturalsize(cache_size, binary=True), Style=Style))
    print("{Style.BRIGHT}Source:{Style.RESET_ALL} {}".format(humanize.naturalsize(source_size, binary=True), Style=Style))

@cli.group()
def config():
    pass

@config.command("set")
@click.argument("name", nargs=1)
@click.argument("value", nargs=1)
def set_(name, value):
    section, name = name.split(".")
    cfg[section][name] = value

@config.command()
@click.argument("name", nargs=1)
def get(name):
    section, name = name.split(".")
    print(cfg[section][name])

@cli.group()
def package():
    global repo, local_repo, downloader, qs

    downloader = Downloader()

    handler = NexusHandler()
    downloader.add_handler(handler)

    handler = LoversLabHandler()
    downloader.add_handler(handler)

    repo_dir = cfg.repo.dir
    if not repo_dir.exists():
        repo_dir.makedirs()
    repo = GitRemotePackageRepo(repo_dir, "https://github.com/DelusionalLogic/modbuild-repo.git")

    local_dir = cfg.local.dir
    if not local_dir.exists():
        local_dir.makedirs()
    local_repo = LocalPackageRepo(local_dir)

# @HACK This is super hacky! we should have some template or something
def make_full_graph():
    import networkx as nx
    with open("profile/modlist.txt", "w") as f:
        G = nx.DiGraph()
        for package in local_repo.get_all_packages():
            G.add_node(package)
            for dep_name in package.dependecies:
                q = Query(dep_name)
                dep = local_repo.find_package(q)
                G.add_edge(package, dep)
        for package in nx.topological_sort(G):
            print("+" + package.name, file=f)
        print("*Unmanaged: Dawnguard", file=f)
        print("*Unmanaged: Dragonborn", file=f)
        print("*Unmanaged: HearthFires", file=f)
        print("*Unmanaged: HighResTexturePack01", file=f)
        print("*Unmanaged: HighResTexturePack02", file=f)
        print("*Unmanaged: HighResTexturePack03", file=f)
        print("*Unmanaged: Unofficial Dawnguard Patch", file=f)
        print("*Unmanaged: Unofficial Dragonborn Patch", file=f)
        print("*Unmanaged: Unofficial Hearthfire Patch", file=f)
        print("*Unmanaged: Unofficial High Resolution Patch", file=f)
        print("*Unmanaged: Unofficial Skyrim Patch", file=f)

@package.command()
def sync():
    print("Syncing remote repo")
    repo.update()

@package.command()
@click.argument("packages", nargs=-1)
@click.option("--explicit", "-e", multiple=True, help="Explicit package descriptor files to include")
def install(packages, explicit):
    # Create the queries from the strings
    qs = [Query(p) for p in packages]
    t = AddTransaction(local_repo, repo, downloader)

    # Support for loading out of tree package specifications
    for e_path in explicit:
        # @HACK this should be a config option and also maybe not specified
        # here?
        pkgins = Path("dist")
        pkgsrc = cfg.source.dir
        e = Path(e_path)
        if not e.exists():
            print("Explicit package at {Style.BRIGHT}{}{Style.RESET_ALL} not found".format(e, Style=Style, Fore=Fore))
            exit(1)
        package = load_config(e, pkgsrc, pkgins)
        t.add(package)

    for q in qs:
        package = repo.find_package(q)
        if package is None:
            print("No package named {Style.BRIGHT}{}{Style.RESET_ALL}".format(q, Style=Style))
            return
        t.add(package)

    try:
        t.expand()
    except TransactionCycleError as e:
        # Some form of dependency cycle
        # @ENHANCEMENT We should really run visualize on the graph that failed.
        # That would be way more helpful
        print("ERROR Cycle detected: ")
        print("\tCycle consists of: {}".format(", ".join( (p.name for p in e.cycle) )))
        exit(1)
    except ConflictError as e:
        # We found some conflicts which means we need to look for some package
        # to bridge them that aren't part of the transaction
        print("{Fore.RED}Conflicting packages{Fore.RESET}".format(Fore=Fore))
        for conflict in e.conflicts:
            print("{Style.BRIGHT}{}{Style.RESET_ALL} conflicts with {Style.BRIGHT}{}{Style.RESET_ALL}".format(*conflict, Style=Style))
            bridges = repo.find_bridges(*conflict)
            for bridge in bridges:
                print("\t{Style.BRIGHT}{}{Style.RESET_ALL} could bridge that conflict".format(bridge, Style=Style))
        exit(1)
    except MissingDependencyError as e:
        print("{Fore.RED}Unresolved dependencies{Fore.RESET}".format(Fore=Fore))
        for missing in e.dependencies:
            print("{Style.BRIGHT}{}{Style.RESET_ALL} requires {Style.BRIGHT}{}{Style.RESET_ALL} which wasn't found".format(*missing, Style=Style))
        exit(1)

    print("")
    print("This will install the following packages: ")
    print("-> " + Style.BRIGHT + ", ".join(map(str, t.installs)))
    print("")
    Q.yes_no("Are you sure?")

    t.prepare()
    t.commit()
    make_full_graph()

@package.command()
@click.argument("packages", nargs=-1)
def remove(packages):
    qs = [Query(p) for p in packages]
    t = RemoveTransaction(local_repo, repo, downloader)
    for q in qs:
        package = local_repo.find_package(q)
        if package is None:
            print("No installed package named {Style.BRIGHT}{}{Style.RESET_ALL}".format(q, Style=Style))
            return
        t.add(package)

    try:
        t.expand()
    except ConflictError as e:
        # Removing these packages would mean creating these new conflicts
        # This is possible because we have bridges
        print("{Fore.RED}Conflicting packages{Fore.RESET}".format(Fore=Fore))
        for (bridge, conflict) in e.conflicts:
            print("Removing {Style.BRIGHT}{}{Style.RESET_ALL} would break bridge of {Style.BRIGHT}{}{Style.RESET_ALL} and {Style.BRIGHT}{}{Style.RESET_ALL}".format(bridge, *conflict, Style=Style))
            bridges = repo.find_bridges(*conflict, exclude=t.targets)
            for bridge in bridges:
                print("\t {Style.BRIGHT}{}{Style.RESET_ALL} is an alternative bridge".format(bridge, Style=Style))
            if not bridges:
                print("\t {Fore.RED}Unfortunately{Fore.RESET} I don't know of any alternative".format(Fore=Fore))
        exit(1)
    except DependencyBreakError as e:
        print("")
        print("Removal would {Style.BRIGHT}break{Style.RESET_ALL} dependencies: ".format(Style=Style))
        for p in e.dependencies:
            print("\t{Style.BRIGHT}{}{Style.RESET_ALL} depends on {Style.BRIGHT}{}{Style.RESET_ALL}".format(*p, Style=Style))
            exit(1)


    print("")
    print("This will remove the following packages: ")
    print("PACKAGES: {Style.BRIGHT}{}".format(", ".join(map(str, t.removes)), Style=Style))
    print("")
    Q.yes_no("Are you sure?")

    try:
        t.prepare()
    # @DEAD
    except DependencyBreakError as e:
        print("")
        print("Removal would {Style.BRIGHT}break{Style.RESET_ALL} dependencies: ".format(Style=Style))
        for p in e.dependencies:
            print("\t{Style.BRIGHT}{}{Style.RESET_ALL} depends on {Style.BRIGHT}{}{Style.RESET_ALL}".format(*p, Style=Style))
            exit(1)

    t.commit()
    make_full_graph()

@package.command()
@click.option('-r', '--reverse', count=True, help="Reverse results, putting the best match at the bottom")
@click.argument("term", nargs=-1)
def search(term, reverse):

    candidates = repo.search(" ".join(term))
    if reverse:
        candidates = reversed(candidates)
    for package in candidates:
        q = Query(package.name)
        local_pkg = local_repo.find_package(q)
        print("{}/{} {}".format(
            Fore.MAGENTA + package.name + Style.RESET_ALL,
            package.version,
            "" if local_pkg is None else Fore.YELLOW + "[installed={}]".format(local_pkg.version) + Style.RESET_ALL
            ))

# @ENHANCEMENT It would be great it you could visualize as part of the other
# operations
@package.command()
def visualize():
    import networkx as nx
    # How about we don't fire up a JVM just to start my script?
    from asciinet import graph_to_ascii

    G = nx.DiGraph()
    root = "Root"

    G.add_node(root)

    # @ENHANCEMENT
    # Right now we just visualize it as a stright up dependency graph. We might
    # want to show when we use provides instead in the future. This would
    # involve adding a fake node when we look for a provides and let that
    # depend on the actual implementors
    for package in local_repo.get_all_packages():
        G.add_node(package)
        if package.reason == InstallReason.REQ:
            G.add_edge(root, package)
        for dep_str in package.dependecies:
            q = Query(dep_str)
            dep = local_repo.find_package(q)
            if dep is None:
                print(package, q)
            G.add_edge(package, dep)

    print(graph_to_ascii(G))

# Show details about a package
@package.command()
@click.argument("package_q", nargs=1)
def details(package_q):
    q = Query(package_q)
    package = local_repo.find_package(q)
    if package is None:
        print("No package named {Style.BRIGHT}{}{Style.RESET_ALL}".format(q, Style=Style))
        exit(1)

    required_by = [str(p) for p in local_repo.find_dependants(package)]
    deps = [ str(d) for d in package.dependecies]

    bridges = set()
    for (b1, b2) in package.bridges:
        p1 = local_repo.find_package(Query(b1))
        p2 = local_repo.find_package(Query(b2))
        if p1 and p2:
            bridges.add("{}--{}".format(p1, p2))

    info = {
        "Name": package.name,
        "Version": package.version,
        "Installed on": package.install_date.strftime("%d/%m/%y"),
        "Depends On": "  ".join(deps),
        "Required By": "  ".join(required_by),
        "Conflicts with": "  ".join(package.conflicts),
        "Bridges": "  ".join(bridges),
        "Reason": "Explicitly installed" if package.reason == InstallReason.REQ else "Dependency",
    }
    for k,v in info.items():
        print("{Style.BRIGHT}{0:<20}{Style.RESET_ALL}: {1}".format(k,v, Style=Style))

if __name__ == '__main__':
    cli()
