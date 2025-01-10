from setuptools import setup, find_packages

setup(
    name="audiobook-tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "mutagen>=1.45.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=1.0.0",
            "pylint>=2.15.0",
            "tox>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "audiobook-tools=audiobook_tools.cli.main:main",
        ],
    },
    author="Antony Stubbs",
    description="A tool to combine audio files and add chapter markers using CUE sheets",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="audiobook, m4b, cue, chapters",
    url="https://github.com/astubbs/audiobook-tools",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.8",
) 