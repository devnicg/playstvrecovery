from setuptools import setup, find_packages

from playstvrecovery import __version__

setup(
    name="playstvrecovery",
    version=__version__,
    author="Nicola Goderis",
    description="A simple tool to recover deleted Plays.tv clips",
    long_description="playstv recovery tool",
    packages=find_packages(),
    entry_points={"console_scripts": ["playstvrec=playstvrecovery:main"]},
    install_requires=[
        "beautifulsoup4==4.12.2",
        "certifi==2023.7.22",
        "charset-normalizer==3.2.0",
        "click==8.1.6",
        "colorama==0.4.6",
        "idna==3.4",
        "iniconfig==2.0.0",
        "markdown-it-py==3.0.0",
        "mdurl==0.1.2",
        "packaging==23.1",
        "pluggy==1.2.0",
        "Pygments==2.16.1",
        "pytest==7.4.0",
        "requests==2.31.0",
        "rich==13.5.2",
        "shellingham==1.5.0.post1",
        "soupsieve==2.4.1",
        "typer==0.9.0",
        "typing_extensions==4.7.1",
        "urllib3==2.0.4",
        "waybackpy==3.0.6",
    ],
)
