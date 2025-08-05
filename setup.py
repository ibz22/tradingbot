"""
Setup script for the Enhanced Halal Trading Bot
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('TA-Lib'):
            requirements.append(line)

setup(
    name="halalbot",
    version="2.2.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Enhanced Halal Trading Bot - Islamic Finance Compliant Automated Trading",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibz22/tradingbot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'talib': ['TA-Lib>=0.4.25'],
        'jupyter': ['jupyter>=1.0.0', 'matplotlib>=3.7.0', 'seaborn>=0.12.0'],
        'dev': ['pytest>=7.4.0', 'pytest-asyncio>=0.21.0', 'black', 'flake8'],
    },
    entry_points={
        'console_scripts': [
            'halalbot=main:main',
            'halalbot-backtest=examples.backtest_example:main',
            'halalbot-screen=examples.screening_example:main',
        ],
    },
    include_package_data=True,
    package_data={
        'halalbot': ['*.yaml', '*.yml'],
    },
)
