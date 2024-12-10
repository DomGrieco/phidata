from setuptools import setup, find_packages

setup(
    name="knowledge_base_app",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "phidata>=2.6.0",
        "openai>=1.12.0",
        "pgvector>=0.2.5",
        "pypdf>=4.0.0",
        "psycopg[binary]>=3.1.18",
        "sqlalchemy>=2.0.0",
        "fastapi>=0.109.0",
        "streamlit>=1.31.0",
        "python-dotenv>=1.0.0",
        "duckduckgo-search>=4.2.0",
        "newspaper4k>=0.7.0",
        "lxml_html_clean>=0.2.0",
        "typer>=0.9.0",
        "rich>=13.7.0",
    ],
    python_requires=">=3.9",
) 