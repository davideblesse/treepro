from setuptools import setup, find_packages

setup(
    name="treepro",
    version="0.1.5",
    description="An advanced version of the Unix tree command.",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "rich",
        "click",
        "questionary",
        "pyyaml",
        "pathspec",
        "prompt_toolkit<3.0.47",
    ],
    entry_points={
        "console_scripts": [
            "treepro=treepro.cli:treepro"
        ]
    },
)
