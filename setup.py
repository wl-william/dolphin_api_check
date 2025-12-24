from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="check_dolphin",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="DolphinScheduler workflow monitoring and retry tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/check_dolphin",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.31.0",
        "PyYAML>=6.0.1",
    ],
    entry_points={
        "console_scripts": [
            "check-dolphin=check_dolphin.cli:main",
        ],
    },
)
