from setuptools import setup, find_packages
from pathlib import Path

# Чтение версии из файла VERSION
def get_version():
    version_file = Path(__file__).parent / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding='utf-8').strip()
    return "1.0.0"

# Чтение README для long_description
def get_long_description():
    readme_file = Path(__file__).parent / "README.md"
    if readme_file.exists():
        return readme_file.read_text(encoding='utf-8')
    return ""

setup(
    name="geoadjust",
    version=get_version(),
    author="GeoAdjust Team",
    author_email="geoadjust@example.com",
    description="Профессиональная система уравнивания геодезических сетей",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/geoadjust/geoadjust-pro",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,  # Включение файлов из MANIFEST.in
    package_data={
        "geoadjust": [
            "gui/resources/*.qss",
            "gui/resources/icons/*",
            "gui/resources/styles/*",
            "crs/database/*.yaml",
            "resources/**/*",
            "py.typed",  # Маркер для type checking
        ],
    },
    entry_points={
        'console_scripts': [
            'geoadjust=geoadjust.__main__:main',
        ],
    },
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "scikit-sparse>=0.4.8",
        "pyproj>=3.4.0",
        "networkx>=2.8.0",
        "PyQt5>=5.15.0",
        "PyQt5-sip>=12.8.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.12.0",
        "python-docx>=0.8.11",
        "Pillow>=9.0.0",
        "openpyxl>=3.0.0",
        "chardet>=4.0.0",
        "requests>=2.28.0",
        "pandas>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "pytest-qt>=4.0.0",
            "flake8>=4.0.0",
            "mypy>=0.931",
            "black>=22.0.0",
            "build>=0.7.0",
            "twine>=3.8.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    python_requires=">=3.8",
)
