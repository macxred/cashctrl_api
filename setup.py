from setuptools import find_packages, setup

setup(
    name="cashctrl_api",
    version="0.0.1",
    description="Python client for the CashCtrl REST API",
    url="https://github.com/macxred/cashctrl_api",
    author="Lukas Elmiger",
    python_requires=">=3.9",
    install_requires=[
        "requests",
        "pandas",
        "consistent_df @ https://github.com/macxred/consistent_df/tarball/main"
    ],
    packages=find_packages(exclude=("tests", "examples")),
    extras_require={
        "dev": [
            "flake8",
            "bandit",
            "pytest",
        ]
    }
)
