from setuptools import setup


with open('requirements.txt') as f:
    deps = f.read().strip().split('\n')


with open('README.rst') as f:
    readme = f.read()


setup(
    name='chdl',
    version='0.0.1dev',
    description='4chan image downloader written in Python asyncio',
    long_description=readme,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities',
    ],
    url='https://github.com/winny-/chdl',
    author='Winston Weinert',
    author_email='winston@ml1.net',
    license='MIT',
    packages=['chdl'],
    install_requires=deps,
    entry_points={
        'console_scripts': ['chdl=chdl:main'],
    },
)
