"""Setup configuration for Reddit Auto Mod CLI"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
this_directory = Path(__file__).parent
long_description = ""
readme_file = this_directory / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')

setup(
    name='reddit-auto-mod',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='Automated moderation assistant for Reddit using AI',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/reddit-auto-mod',
    packages=find_packages(include=['cli', 'cli.*', 'BackEnd', 'BackEnd.*']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Communications :: Chat',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
    install_requires=[
        'praw>=7.7.0',
        'openai>=1.0.0',
        'fastapi>=0.104.0',
        'uvicorn>=0.24.0',
        'pydantic>=2.0.0',
        'requests>=2.31.0',
        'pymongo>=4.6.0',
        'transformers>=4.35.0',
        'torch>=2.1.0',
        'faiss-cpu>=1.7.4',
        'schedule>=1.2.0',
        'sentence-transformers>=2.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'black>=23.0.0',
            'flake8>=6.1.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'reddit-auto-mod=cli.main:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords='reddit moderation ai automation openai',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/reddit-auto-mod/issues',
        'Source': 'https://github.com/yourusername/reddit-auto-mod',
    },
)
