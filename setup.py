"""
GRIMOIRE v2.1 — setup.py
The Death Note of the digital world

Developer  : Light
Alias      : Neok1ra
GitHub     : https://github.com/ne0k1r4
"""

from setuptools import setup, find_packages

setup(
    name="grimoire-suite",
    version="2.1.0",
    description="GRIMOIRE — Unified Operator Suite by Light (Neok1ra)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Light",
    author_email="neok1ra@proton.me",
    url="https://github.com/ne0k1r4/grimoire",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=["flask>=2.0"],
    extras_require={
        "web":  ["flask>=2.0"],
        "evtx": ["python-evtx"],
    },
    entry_points={
        "console_scripts": [
            "grimoire=grimoire.core.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Topic :: Security",
        "Environment :: Console",
        "Development Status :: 4 - Beta",
    ],
    keywords="grimoire neok1ra red-team pentest recon steganography c2 blue-team sentinel",
)
