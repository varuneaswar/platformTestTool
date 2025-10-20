from setuptools import setup, find_packages

setup(
    name="database-soak-test",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=1.4.0",
        "psycopg2-binary>=2.9.0",
        "pymysql>=1.0.0",
        "pyodbc>=4.0.0",
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "python-dotenv>=0.19.0",
        "pytest>=6.2.0",
        "pytest-cov>=2.12.0",
        "loguru>=0.5.3",
        "matplotlib>=3.4.0",
        "seaborn>=0.11.0"
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive database soak testing framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/database-soak-test",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
)