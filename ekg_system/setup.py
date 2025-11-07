from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ekg-system",
    version="0.1.0",
    author="EKG System Team",
    description="EKG data processing system for mice",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.8.0",
        "matplotlib>=3.4.0",
        "pandas>=1.3.0",
        "pyserial>=3.5",
    ],
    entry_points={
        "console_scripts": [
            "ekg-system=ekg_system.cli:main",
        ],
    },
)
