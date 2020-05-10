from setuptools import setup, find_packages

setup(
    name = "daytrader",
    version = ">=3.8",
    packages = find_packages() + [
        'pandas',
        'numpy',
        'boto3',
        'pytest',
    ],
)