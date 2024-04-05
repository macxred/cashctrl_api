from setuptools import setup, find_packages

setup(
    name="cashctrl_api",
    version="v0.0.1",
    description="Python client for the CashCtrl REST API",
    url='https://github.com/macxred/cashctrl_api',
    author="Lukas Elmiger",
    python_requires='>3.9',
    install_requires=["requests"],
    packages=find_packages(exclude=('tests', 'examples'))
)
