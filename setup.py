from setuptools import setup

setup(
        name="jdot",
        version="0.5",
        python_requires='>=3.7',
        py_modules=['jdot'],
        packages=["jdot"],
        entry_points={"console_scripts": ["jdot=jdot.__main__:main"]},
    )
