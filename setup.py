import setuptools
from numpy.distutils.core import setup, Extension

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="StellarEvolution",
    version="1.0.0",
    author="Colin P. Johnstone",
    author_email="colin.johnstone@univie.ac.at",
    description="Stellar rotation and XUV evolution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/somethingsomething",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: No idea",
        "Operating System :: Ubuntu (at the moment)",
    ],
    python_requires='>=3.6',
    )
