import networkx as nx

from skymod.repository import Query


class MO(object):
    def __init__(self, config):
        self.cfg = config.mo

        if self.cfg.mods_dir == "" or not self.cfg.mods_dir.exists():
            print(
                "ModOrganizer2 installation directory not set. Please set "
                "mo.mods_dir"
            )
            exit(1)

        if self.cfg.profile_dir == "" or not self.cfg.profile_dir.exists():
            print(
                "ModOrganizer2 installation directory not set. Please set "
                "mo.profile_dir"
            )
            exit(1)

    def getModsDir(self):
        return self.cfg.mods_dir

    def getProfileDir(self):
        return self.cfg.profile_dir

    def make_profile(self, local_repo):
        modlist_path = self.cfg.profile_dir / "modlist.txt"
        with open(modlist_path, "w") as f:
            G = nx.DiGraph()
            for package in local_repo.get_all_packages():
                G.add_node(package)
                for dep_name in package.dependecies:
                    q = Query(dep_name)
                    dep = local_repo.find_package(q)

                    if dep is None:
                        # Skip mising dependecies. If we have an installed
                        # package which has a not installed dependency, then we
                        # just want to skip it. It's up to the user to make
                        # sure everything is resolved, of course assisted by
                        # the tool.  @COMPLETE it might be useful give the user
                        # some way of doing a full dependency verification of
                        # the local repo
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
