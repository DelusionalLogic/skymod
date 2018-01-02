skymod
======
skymod is a package manager for skyrim and mod organizer. It aims to
ease the task of managing dependencies, and the installation of, mods.
In the process it also effectively separates packaging from the
development and release of a mod.

Features
--------

  * Automatic downloading of mods
  * Automatic installation
  * Automatic dependency installation
  * Automatic upgrading
  * Warning on conflicting packages
  * Support for compatibility packages that resolve conflicts
  * Community driven packaging without involvement from the mod author

Installation
------------
Currently the installation is a bit difficult, but follow these steps
and you will be alright.

1. Install python 3.6 (from https://www.python.org/downloads/). Don't
   forget to add python to your path (it's an optional step in the
   installer)
2. Download this repo from github (either clone or as a zip)
3. Open a command prompt and navigate to the downloaded repo.
4. Install skymod by running `pip install .`.
5. Configure skymod as described below.

Configuration
-------------
The first thing to do upon installation is to configure the
auto-downloader. Configure your nexus username:

    skymod config set nexus.username <USERNAME>

You can optionally configure your nexus password to avoid getting asked
for it upon package installation:

    skymod config set nexus.password <PASSWORD>

You now need to configure the MO2 installation directory. skymod uses
this to install mods directly into MO, and configuring the override
order. MO2 will still be in charge of load-order and launching the game.
Ideally skymod should have its own MO2 installation, since it will mess
with your previously installed mods.

    skymod config set mo.mods_dir <MO2_MODS_DIR>
    skymod config set mo.profile_dir <MO2_PROFILE_DIR>

There are a few other configuration options, which can be found in the
configuration file located at: `~/.modbuild/config.ini`.

Configuration options can be set with the generic syntax:

    skymod config set <section>.<key> <value>

Config options can also be queried:

    skymod config get <section>.<key>

Usage
-----
Using skymod is pretty easy once you get the hang of it, especially if
you have used a package manager previously.

Operations on the remote repo are located under the `remote` subcommand
To find a package you want to install:

    skymod remote search --reverse <TERMS>

Which will give you a list of packages matching your search term, sorted
by relevance. The reverse option places the best matching at the bottom
of the list. Once you have found the package you want to install,
install it:

    skymod remote install <PACKAGE_NAMES>

This will resolve all the dependencies of the package, and make sure you
won't have any conflicts. It will then download and unpack all the
required archives into a local cache and install the package as
specified in the modbuild file. Once the command completes the package
should be installed and ready to use.

At some point in the future you might want to update your installed
packages, this is done by running

    skymod remote sync
    
To sync the package repo, followed by

    skymod remote install --upgrade
    
To upgrade all installed packages.

As you installed packages grows skymod will continuously make sure that
new packages you install don't conflict with any of the ones already
installed.

Query Strings
-------------
The `PACKAGE_NAME` in the install operation is actually a query string,
which has optional support for a version specifier. A query string
follows the format:

    <PACKAGE_NAME>[<VER_MOD><VERSION>]

`PACKAGE_NAME` is just the name of the package. `VER_MOD` is a modifier
to the version of the package, it can be one of: `>`, `<`, `>=`, `<=`
or `=`. `VERSION` is a version specifier as described in the packaging
section below.

Query strings are understood as they are read. This means that a query
string written as: `cbbe>=1.0` means a version of the package named
`cbbe` with a version specifier greater than or equal to `1.0`. In other
words we want a version of `cbbe` at least as recent as `1.0`.

If we don't specify a `VER_MOD` or `VERSION`, we are telling skymod that
we'd be satisfied by any version. This is usually how you ask for
packages in the user interface.

Cache
-----
As mentioned in the Usage section, skymod makes use of a local cache.
This cache is used to avoid downloading the same files repeatedly from
the sources. The size of some mods can make the cache folder grow
rapidly. Fortunately skymod supports showing the size of the cache:

    skymod cache size

If the cache it too large, skymod also supports cleaning the cache.

    skymod cache clear

Packaging
---------
skymod is inspired by the Arch Linux Package Manager (ALPM) and the AUR.
As such it should be immediately familiar to anyone who has used Arch
Linux in the past.

The modbuild files are distributed as a single git repo, which skymod
will automatically clone when first run. This git repo has a folder for
every package (named after the package), which contains the actual
package definition (`modbuild.lua`).

The package definition is a lua script. Skymod reads variables from the
global scope and executes lua functions to complete operation.

The supported variables, and the values they are supposed to hold are as
follows:

```
    name: The name of the package
    version: A version specifier, which is any numbers separated by .'s.
        Letters and special characters are NOT supported. The version
        specifier follow a subset of the SemVer semantics, but with
        arbitrarily many parts.
    desc: A short description of the package. Please keep it shorter
        than 80 characters. The best descriptions continues the sentence
        "This mod is a ..." without including it.
    depends: A list of packages this package depends on, formatted as
        query strings.
    provides: A list of package this package can be used as a standin
        For. This is very useful for mods that have a compatible API.
        It's also very useful for providing alternatives within a package,
        while requiring that one of them be installed.
    conflicts: A list of packages that this package are known to not
        work with, formatted as query strings. Keep in mind that other
        packages might bridge this conflict, allowing otherwise
        incompatible packages to coexist.
    optdepends: A list of optional dependencies, and what installing
        them does for the user, formatted as <Q>::<REASON>. Q is a query
        string.
    bridges: A list of bridge specifiers, formatted as <Q1>::<Q2>, where
        Q1 and Q2 are query strings to the package this package bridges.
    sources: A list of sources needed to install this package.

    --functions--

    package: Called when the package is to be installed. Usually this is
        just a series of _install_ function calls, which takes the from
        glob as the first paramters and an optional to path as the
        second. The best way to see how this works is to check how other
        packages use it.
```

Sources
-------
The list of sources is special. It follows the format `<URI>::<NAME>`.
The `NAME` is the name of the downloaded file, which will be unpacked
into a directory of the same name with the extension removed.

`URI` is more interesting. A URI to download from the nexus looks starts
with the `nexus://` protocol, and has the location of the nexus file id.
For the nexus download url `http://www.nexusmods.com/skyrim/download/1000248470`
the source `URI` would be `nexus://1000248470/`. Loverslab urls use the
`ll` protocol, and the location is the last part of the download url.
The download `https://www.loverslab.com/files/file/676-xp32-maximum-skeleton-extended-xpmse/?do=download&r=645603&confirm=1&t=1&csrfKey=5d722ab8c840efe3c4822fc267aa6a59`
becomes `ll://676-xp32-maximum-skeleton-extended-xpmse/?do=download&r=645603&confirm=1&t=1`.
