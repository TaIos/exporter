from setuptools import setup, find_packages

with open('README.rst') as f:
    long_description = ''.join(f.readlines())

setup(
    name='fit-ctu-gitlab-exporter',
    version='1.0.0',
    description='Tool for exporting projects from FIT CTU GitLab to GitHub',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='Martin Šafránek',
    author_email='gismocz@gmail.com',
    keywords='github,gitlab,synchronization,git,fit ctu',
    license='MIT License',
    url='https://github.com/TaIos/exporter',
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': [
            'exporter=exporter.cli:main',
        ],
    },
    install_requires=['GitPython>=3.1', 'click>=6', 'requests>=2.2', 'enlighten'],
    extras_require={'test': ['pytest>=6.2', 'flexmock']},
    zip_safe=False,
    python_requires='>=3.6',
    package_data={'exporter': []},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Topic :: Software Development :: Version Control :: Git',
        'Topic :: System :: Archiving :: Mirroring',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Framework :: Pytest',
        'Framework :: tox',
        'Natural Language :: English'
    ],
)
