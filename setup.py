from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="narrative_time",
    version="0.1.0",
    packages=find_packages(),
    url="https://github.com/text-machine-lab/narrative_time",
    license="MIT",
    requires=requirements,
)
