"""
SmolVLM Anti-Drone System Setup
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# 读取 requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')
else:
    requirements = []

setup(
    name="smolvlm-anti-drone",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="SmolVLM-based Anti-Drone Detection System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smolvlm-anti-drone",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        'mlx': [
            'mlx>=0.20.0',
            'mlx-lm>=0.20.0',
        ],
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-asyncio>=0.21.0',
            'flake8>=6.0.0',
            'black>=23.0.0',
            'mypy>=1.0.0',
        ],
        'api': [
            'fastapi>=0.104.0',
            'uvicorn>=0.24.0',
            'python-multipart>=0.0.6',
        ],
    },
    entry_points={
        'console_scripts': [
            'anti-drone=applications.cli:main',
        ],
    },
)
