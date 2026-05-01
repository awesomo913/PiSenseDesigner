"""Installable Sense HAT animation editor (CommonSense)."""

from setuptools import find_packages, setup

setup(
    name="commonsense-sense-hat",
    version="0.1.0",
    description="Sense HAT 8x8 LED animation editor and API",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=["pillow>=9.0"],
    extras_require={"dev": ["pytest>=7.0"]},
    entry_points={
        "console_scripts": [
            "common-sense=commonsense.sense_paint.editor:main",
        ],
    },
)
