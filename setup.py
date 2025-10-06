"""
Setup script for Email Priority Classification System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "Email Priority Classification System"

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as fh:
        requirements = [
            line.strip() 
            for line in fh 
            if line.strip() and not line.startswith("#")
        ]
else:
    requirements = [
        "pandas>=1.3.0",
        "numpy>=1.21.0", 
        "scikit-learn>=1.0.0",
        "nltk>=3.6.0",
        "tqdm>=4.62.0",
        "joblib>=1.0.0",
        "PyYAML>=5.4.0"
    ]

setup(
    name="email-priority-classifier",
    version="1.0.0",
    author="Email Priority Classification Team",
    author_email="team@email-classifier.com",
    description="A machine learning system for automatic email priority classification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/email-priority-system",
    project_urls={
        "Bug Tracker": "https://github.com/your-username/email-priority-system/issues",
        "Documentation": "https://email-priority-system.readthedocs.io",
        "Source Code": "https://github.com/your-username/email-priority-system",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Communications :: Email",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.900",
        ],
        "viz": [
            "matplotlib>=3.3.0",
            "seaborn>=0.11.0",
            "wordcloud>=1.8.0",
        ],
        "notebooks": [
            "jupyter>=1.0.0",
            "ipykernel>=6.0.0",
        ],
        "api": [
            "flask>=2.0.0",
            "fastapi>=0.70.0",
            "uvicorn>=0.15.0",
        ],
        "nlp": [
            "spacy>=3.4.0",
            "transformers>=4.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "email-priority-train=scripts.train_model:main",
            "email-priority-predict=scripts.predict:main",
        ],
    },
    include_package_data=True,
    package_data={
        "email_classifier": [
            "config/*.json",
            "config/*.yaml",
        ],
    },
    zip_safe=False,
    keywords=[
        "email", "priority", "classification", "machine-learning", 
        "nlp", "text-processing", "enron", "scikit-learn"
    ],
)