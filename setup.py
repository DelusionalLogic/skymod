from setuptools import find_packages, setup

setup(
    name='skymod',
    version='0.5',
    description='A packagemanager for skyrim mods',
    url='https://github.com/DelusionalLogic/skymod',
    author='Delusional Logic',
    author_email='jesper@slashwin.dk',
    # license='GPLv3',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "networkx",
        "fuzzywuzzy",
        "requests",
        "patool",
        "humanize",
        "lupa",
        "tqdm",
        "colorama",
        "GitPython",
        "path.py",
        "PyYAML",
        "beautifulsoup4"
    ],
    entry_points='''
        [console_scripts]
        skymod=skymod.main:cli
    ''',
)
