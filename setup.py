from setuptools import setup, find_packages

setup(
    name = "daytrader",
    python_requires = ">=3.8",
    packages = find_packages(),
    install_requires = [
        'pandas',
        'numpy',
        'boto3',
        'pytest',
    ],
)