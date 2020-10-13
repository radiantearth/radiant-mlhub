import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="radiant_mlhub",
    version="0.0.2",
    author="Radiant Earth Foundation",
    author_email="devops@radiant.earth",
    description="A Python client for Radiant MLHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/radiantearth/radiant-mlhub",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
