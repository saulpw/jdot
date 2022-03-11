from setuptools import setup

setup(
        name="jsom",
        version="2022.03.08",
        python_requires='>=3.6',
        py_modules=['jsom'],
        packages=["jsom"],
        entry_points={"console_scripts": ["jsom=jsom.__main__:main"]},
    )
