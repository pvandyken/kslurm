import setuptools

setuptools.setup(
    name="cluster_utils",
    version="0.0.1",
    author="Peter Van Dyken",
    author_email="pvandyk2@uwo.ca",
    description="Helpful tools for working on SLURM clusters",
    include_package_data=True,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    entry_points={
        "console_scripts": [
            "kbatch=app.bin.batch:main",
            "kalloc=app.bin.interactive:main",
            "ksnake=app.bin.ssnake:main"
        ]
    },
    install_requires=[
        "colorama>=0.4.4"
    ],
    python_requires=">=3.5"
)