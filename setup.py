from setuptools import setup, find_packages

setup(
    name="proffix_api",
    version="v0.0.1",
    description="Python client for the Proffix REST API",
    url='https://github.com/lasuk/proffix_api',
    author="Lukas Elmiger",
    python_requires='>3.9',
    install_requires=["requests"],
    packages=find_packages(exclude=('tests', 'examples'))
)
