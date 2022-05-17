# SPDX-License-Identifier: Apache-2.0

from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="jdot",
    version="0.5",
    description="JSON with minimal punctuation, plus Macros",
    long_description=readme(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Pre-processors",
    ],
    keywords="json jdot",
    author="Saul Pwanson",
    url="https://github.com/saulpw/jdot",
    python_requires=">=3.7",
    py_modules=["jdot"],
    packages=["jdot"],
    entry_points={"console_scripts": ["jdot=jdot.__main__:main"]},
)
