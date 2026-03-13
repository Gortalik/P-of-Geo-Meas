from setuptools import setup, find_packages

setup(
    name="geoadjust",
    version="1.0.0",
    author="GeoAdjust Team",
    author_email="geoadjust@example.com",
    description="Профессиональная система уравнивания геодезических сетей",
    long_description=open("README.md", encoding="utf-8").read() if __import__("pathlib").Path("README.md").exists() else "",
    long_description_content_type="text/markdown",
    url="https://github.com/geoadjust/geoadjust-pro",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "geoadjust.gui.resources": ["*.qss", "icons/*"],
    },
    entry_points={
        'console_scripts': [
            'geoadjust=geoadjust.__main__:main',
        ],
    },
    install_requires=[
        "PyQt5>=5.15.0",
        "PyQt5-sip>=12.8.0",
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "matplotlib>=3.5.0",
        "python-docx>=0.8.11",
        "Pillow>=9.0.0",
        "openpyxl>=3.0.0",
    ],
    extras_require={
        "gui": [
            "seaborn>=0.12.0",
        ],
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
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
