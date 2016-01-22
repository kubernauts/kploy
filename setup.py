from setuptools import setup, find_packages

try:
   import pypandoc
   long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
   long_description = ''

setup(
    name="kploy",
    version="0.10.0",
    description="An opinionated Kubernetes deployment system for appops",
    long_description=long_description,
    author="Michael Hausenblas",
    author_email="michael.hausenblas@gmail.com",
    license="Apache",
    url="https://github.com/kubernauts/kploy",
    keywords = ['Kubernetes', 'containers', 'appops', 'deployment'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    entry_points={
        "console_scripts": [
            "kploy=kploy:main",
        ],
    },
    zip_safe=False,
    py_modules=["kploy", "kploycommon"],
    install_requires=[
        "pyk",
        "tabulate"
    ],
)