from setuptools import setup, find_packages

setup(
    name="treepro",
    version="0.1.1",
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
        "pyperclip"
    ],
    entry_points={
        "console_scripts": [
            "treepro=treepro.cli:treepro"
        ]
    },
)
