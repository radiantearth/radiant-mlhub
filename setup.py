import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="radiant_mlhub",
    version="0.3.0",
    author="Radiant Earth Foundation",
    author_email="devops@radiant.earth",
    license='Apache License 2.0',
    license_file='LICENSE',
    description="A Python client for Radiant MLHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/radiantearth/radiant-mlhub",
    packages=setuptools.find_packages(),
    package_data={
        "": ["py.typed"]
    },
    platforms='Platform Independent',
    entry_points={
        'console_scripts': [
            'mlhub=radiant_mlhub.cli:mlhub'
        ]
    },
    install_requires=[
        'requests~=2.25',
        'pystac~=1.1',
        'click>=7.1.2,<9.0.0',
        'tqdm~=4.56',
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    project_urls={
        'Tracker': 'https://github.com/radiantearth/radiant-mlhub/issues',
        'Slack': 'https://mlhubearth.slack.com',
        'Documentation': 'https://radiant-mlhub.readthedocs.io/en/latest/'
    },
    python_requires='>=3.7',
)
