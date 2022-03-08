from setuptools import setup, find_packages

setup(
        name="jsom",
        version="2022.03.08",
        packages=["jsom"],
        entry_points = {"console_scripts": ["jsom = jsom.__main__:main"]},
    )
