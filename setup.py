from setuptools import setup

setup(
        name="jsom",
        version="0.5",
        python_requires='>=3.7',
        py_modules=['jsom'],
        packages=["jsom"],
        entry_points={"console_scripts": ["jsom=jsom.__main__:main"]},
    )
