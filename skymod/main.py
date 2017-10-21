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
import click
from path import Path
import skymod.query as Q
import humanize

from .cfg import read_config
from .cfg import config as cfg

from skymod.package import load_package
from skymod.package import InstallReason
from skymod.package import print_local_package

from skymod.repository import GitRemotePackageRepo
from skymod.repository import LocalPackageRepo
from skymod.repository import Query
from skymod.packagelist import PackageList, InstalledTag, WantedTag
from skymod.dirhashmap import DirMap

from skymod.transaction import (
    TransactionCycleError,
    DependencyBreakError,
    ConflictError,
    MissingDependencyError,
    AddTransaction,
    RemoveTransaction,
    UpgradeTransaction,
)

from skymod.handler import Downloader, NexusHandler, LoversLabHandler

from colorama import Fore, Style
import colorama

colorama.init()


@click.group()
@click.option("--config", "-c", help="Configuration file")
def cli(config):
    global down_cache, src_cache

    if config:
        read_config(Path(config))
    else:
        read_config()

    down_cache = DirMap(cfg.cache.dir)
    src_cache = DirMap(cfg.source.dir)


@cli.group()
def cache():
    pass


@cache.command()
def clear():
    if not Q.yes_no(
            "Are you sure? This will remove cache and source dir",
            default="no",
            ):
        return

    down_cache.clear()

    src_cache.clear()


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

    print("{Style.BRIGHT}Cache: {Style.RESET_ALL} {}".format(
        humanize.naturalsize(cache_size, binary=True),
        Style=Style
    ))
    print("{Style.BRIGHT}Source:{Style.RESET_ALL} {}".format(
        humanize.naturalsize(source_size, binary=True),
        Style=Style
    ))


@cli.group()
def config():
    pass


@config.command("set")
@click.argument("name", nargs=1)
@click.argument("value", nargs=1)
def set_(name, value):
    section, option = name.split(".")
    try:
        cfg[section][option] = value
    except KeyError:
        print(
            "Unknown config option {Style.BRIGHT}{}{Style.RESET_ALL}"
            .format(
                name,
                Style=Style
            )
        )


@config.command()
@click.argument("name", nargs=1)
def get(name):
    section, option = name.split(".")
    try:
        print(cfg[section][option])
    except KeyError:
        print(
            "Unknown config option {Style.BRIGHT}{}{Style.RESET_ALL}"
            .format(
                name,
                Style=Style
            )
        )


def init():
    global repo, local_repo, downloader, qs

    downloader = Downloader(down_cache)

    handler = NexusHandler()
    downloader.add_handler(handler)

    handler = LoversLabHandler()
    downloader.add_handler(handler)

    repo_dir = cfg.repo.dir
    if not repo_dir.exists():
        repo_dir.makedirs()
    repo = GitRemotePackageRepo(
        repo_dir,
        cfg.repo.url
    )

    local_dir = cfg.local.dir
    if not local_dir.exists():
        local_dir.makedirs()
    local_repo = LocalPackageRepo(local_dir)

    if cfg.mo.mods_dir == "" or not cfg.mo.mods_dir.exists():
        print(
            "ModOrganizer2 installation directory not set. Please set "
            "mo.mods_dir"
        )
        exit(1)

    if cfg.mo.profile_dir == "" or not cfg.mo.profile_dir.exists():
        print(
            "ModOrganizer2 installation directory not set. Please set "
            "mo.profile_dir"
        )
        exit(1)


@cli.group()
def remote():
    init()


@cli.group()
def local():
    init()


# @HACK This is super hacky! we should have some template or something
def make_full_graph():
    import networkx as nx
    modlist_path = cfg.mo.profile_dir / "modlist.txt"
    with open(modlist_path, "w") as f:
        G = nx.DiGraph()
        for package in local_repo.get_all_packages():
            G.add_node(package)
            for dep_name in package.dependecies:
                q = Query(dep_name)
                dep = local_repo.find_package(q)

                if dep is None:
                    # Skip mising dependecies. If we have an installed package
                    # which has a not installed dependency, then we just want
                    # to skip it. It's up to the user to make sure everything
                    # is resolved, of course assisted by the tool.
                    # @COMPLETE it might be useful give the user some way of
                    # doing a full dependency verification of the local repo
                    continue

                G.add_edge(package, dep)
        for package in nx.lexicographical_topological_sort(
                G,
                key=lambda x: x.priority):
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


@remote.command()
def sync():
    print("Syncing remote repo")
    repo.update()


@remote.command()
@click.argument("packages", nargs=-1)
@click.option(
    "--explicit",
    "-e",
    multiple=True,
    help="Explicit package descriptor files to include"
)
@click.option('--upgrade/--no-upgrade', default=False)
def install(packages, explicit, upgrade):
    # Create the queries from the strings
    qs = [Query(p) for p in packages]
    if upgrade:
        t = UpgradeTransaction(local_repo, repo, downloader)
    else:
        t = AddTransaction(local_repo, repo, downloader, src_cache)

    # Support for loading out of tree package specifications
    for e_path in explicit:
        # @HACK this should be a config option and also maybe not specified
        # here?
        pkgins = cfg.mo.mods_dir
        if not pkgins.exists():
            pkgins.mkdir()
        pkgsrc = cfg.source.dir
        e = Path(e_path)
        if not e.exists():
            print(
                "Explicit package at {Style.BRIGHT}{}{Style.RESET_ALL} "
                "not found"
                .format(
                    e,
                    Style=Style,
                    Fore=Fore
                )
            )
            exit(1)
        package = load_package(e, pkgsrc, pkgins)
        t.add(package)

    for q in qs:
        package = repo.find_package(q)
        if package is None:
            print("No package named {Style.BRIGHT}{}{Style.RESET_ALL}".format(
                q,
                Style=Style
            ))
            return
        t.add(package)

    try:
        t.expand()
    except TransactionCycleError as e:
        # Some form of dependency cycle
        # @ENHANCEMENT We should really run visualize on the graph that failed.
        # That would be way more helpful
        # -- We can't use asciinet since installing it is a pain
        print("ERROR Cycle detected: ")
        print("\tCycle consists of: {}".format(
            ", ".join((p.name for p in e.cycle))
        ))
        exit(1)
    except ConflictError as e:
        # We found some conflicts which means we need to look for some package
        # to bridge them that aren't part of the transaction
        print("{Fore.RED}Conflicting packages{Fore.RESET}".format(Fore=Fore))
        for conflict in e.conflicts:
            print(
                "{Style.BRIGHT}{}{Style.RESET_ALL} conflicts with "
                "{Style.BRIGHT}{}{Style.RESET_ALL}"
                .format(
                    *conflict,
                    Style=Style
                )
            )
            bridges = repo.find_bridges(*conflict)
            for bridge in bridges:
                print(
                    "\t{Style.BRIGHT}{}{Style.RESET_ALL} could bridge "
                    "that conflict"
                    .format(
                        bridge,
                        Style=Style
                    )
                )
        exit(1)
    except MissingDependencyError as e:
        print("{Fore.RED}Unresolved dependencies{Fore.RESET}".format(
            Fore=Fore
        ))
        for missing in e.dependencies:
            print(
                "{Style.BRIGHT}{}{Style.RESET_ALL} requires "
                "{Style.BRIGHT}{}{Style.RESET_ALL} which wasn't found"
                .format(
                    *missing,
                    Style=Style
                )
            )
        exit(1)

    if not t.targets:
        print("Nothing to do".format(Style=Style, Fore=Fore))
        exit(0)

    print("")
    print("This will install the following packages: ")
    print("-> " + Style.BRIGHT + ", ".join(map(str, t.installs)))
    print("")
    Q.yes_no("Are you sure?")

    t.prepare()
    t.commit()
    make_full_graph()


@local.command()
@click.argument("packages", nargs=-1)
@click.option(
    "--no-dep",
    is_flag=True,
    default=False,
    help="Skip dependency checking",
)
def remove(packages, no_dep):
    # Skipping dependency checking can be dangerous. Lets print a nice big
    # warning to make sure the user knows what they are doing.
    if no_dep:
        print(
            "{Fore.YELLOW}{Style.BRIGHT}Warning:{Style.RESET_ALL}"
            " depedency checking disabled"
            .format(Style=Style, Fore=Fore)
        )
    qs = [Query(p) for p in packages]
    t = RemoveTransaction(local_repo, repo, downloader, no_dep)
    for q in qs:
        package = local_repo.find_package(q)
        if package is None:
            print(
                "No installed package named {Style.BRIGHT}{}{Style.RESET_ALL}"
                .format(
                    q,
                    Style=Style
                )
            )
            return
        t.add(package)

    try:
        t.expand()
    except ConflictError as e:
        # Removing these packages would mean creating these new conflicts
        # This is possible because we have bridges
        print("{Fore.RED}Conflicting packages{Fore.RESET}".format(Fore=Fore))
        for (bridge, conflict) in e.conflicts:
            print(
                "Removing {Style.BRIGHT}{}{Style.RESET_ALL} would break "
                "bridge of {Style.BRIGHT}{}{Style.RESET_ALL} and "
                "{Style.BRIGHT}{}{Style.RESET_ALL}"
                .format(
                    bridge,
                    *conflict, Style=Style
                )
            )
            bridges = repo.find_bridges(*conflict, exclude=t.targets)
            for bridge in bridges:
                print(
                    "\t{Style.BRIGHT}{}{Style.RESET_ALL} is an "
                    "alternative bridge"
                    .format(
                        bridge,
                        Style=Style
                    )
                )
            if not bridges:
                print(
                    "\t {Fore.RED}Unfortunately{Fore.RESET} I don't know of "
                    "any alternative"
                    .format(
                        Fore=Fore
                    )
                )
        exit(1)
    except DependencyBreakError as e:
        print("")
        print(
            "Removal would {Style.BRIGHT}break{Style.RESET_ALL} dependencies: "
            .format(
                Style=Style
            )
        )
        for p in e.dependencies:
            print(
                "\t{Style.BRIGHT}{}{Style.RESET_ALL} depends on "
                "{Style.BRIGHT}{}{Style.RESET_ALL}"
                .format(
                    *p,
                    Style=Style
                )
            )
            exit(1)

    print("")
    print("This will remove the following packages: ")
    print("PACKAGES: {Style.BRIGHT}{}".format(
        ", ".join(map(str, t.removes)),
        Style=Style
    ))
    print("")
    Q.yes_no("Are you sure?")

    try:
        t.prepare()
    # @DEAD
    except DependencyBreakError as e:
        print("")
        print(
            "Removal would {Style.BRIGHT}break{Style.RESET_ALL} dependencies: "
            .format(
                Style=Style
            )
        )
        for p in e.dependencies:
            print(
                "\t{Style.BRIGHT}{}{Style.RESET_ALL} depends on "
                "{Style.BRIGHT}{}{Style.RESET_ALL}"
                .format(
                    *p,
                    Style=Style
                )
            )
            exit(1)

    t.commit()
    make_full_graph()


@remote.command()
@click.option(
    '-r',
    '--reverse',
    count=True,
    help="Reverse results, putting the best match at the bottom"
)
@click.argument("term", nargs=-1)
def search(term, reverse):

    candidates = repo.search(" ".join(term))
    if reverse:
        candidates = list(reversed(candidates))

    lst = PackageList(candidates)
    for package in lst:
        # Set all the tags
        q = Query(package.name)
        local_pkg = local_repo.find_package(q)

        # Having a local package means it's currently installed. Fill in the
        # tag with the version
        if local_pkg:
            lst.add_tag(package, InstalledTag(local_pkg.version))

    lst.present()


@local.command("search")
@click.option(
    '-r',
    '--reverse',
    count=True,
    help="Reverse results, putting the best match at the bottom"
)
@click.argument("term", nargs=-1)
def local_search(term, reverse):
    candidates = local_repo.search(" ".join(term))
    if reverse:
        candidates = list(reversed(candidates))

    lst = PackageList(candidates)
    for package in lst:
        # We dont tag installed packages, since we already print the local
        # version information

        # Lets tag explicitly installed packages
        if package.reason == InstallReason.REQ:
            lst.add_tag(package, WantedTag())

    lst.present()


# @ENHANCEMENT It would be great it you could visualize as part of the other
# operations
@local.command()
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
@local.command()
@click.argument("package_q", nargs=1)
def details(package_q):
    q = Query(package_q)
    package = local_repo.find_package(q)
    if package is None:
        print("No package named {Style.BRIGHT}{}{Style.RESET_ALL}".format(
            q,
            Style=Style
        ))
        exit(1)
    print_local_package(local_repo, package)


if __name__ == '__main__':
    cli()
