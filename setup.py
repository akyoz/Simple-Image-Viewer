import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="simple-image-viewer",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A simple image viewer application built with Tkinter.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/simple-image-viewer",
    py_modules=['image_viewer'],
    install_requires=[
        'Pillow',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'simple-image-viewer=image_viewer:main',
        ],
    },
)
