from setuptools import setup

setup(
        name="jdot",
        version="0.5",
        description='JSON with minimal punctuation, plus Macros',
        long_description=open('README.md').read(),
        long_description_content_type='text/markdown',
        author='Saul Pwanson',
        url='https://github.com/saulpw/jdot',
        python_requires='>=3.7',
        py_modules=['jdot'],
        packages=["jdot"],
        entry_points={"console_scripts": ["jdot=jdot.__main__:main"]},
    )
