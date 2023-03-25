import setuptools

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "imfPy",
    version = "0.0.1",
    author = "Christopher C. Smith",
    author_email = "chriscarrollsmith@gmail.com",
    description = "Python package for downloading economic data from the International Monetary Fund JSON RESTful API endpoint.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/chriscarrollsmith/imfPy,
    project_urls = {
        "Bug Tracker": "https://github.com/chriscarrollsmith/imfPy/issues",
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir = {"": "src"},
    packages = setuptools.find_packages(where="src"),
    python_requires = ">=3.6"
)