from setuptools import setup, find_packages
from evince_synctex import __doc__ as DESCRIPTION, CONSOLE_SCRIPTS


headline = DESCRIPTION.split('\n', 1)[0].rstrip('.')


setup(
    name='evince-synctex',
    version='0.1',
    description=headline,
    long_description=DESCRIPTION,
    author='https://github.com/Mortal',
    url='https://github.com/Mortal/evince-synctex',
    py_modules=['evince_synctex'],
    include_package_data=True,
    license='GPLv3',
    entry_points={
        'console_scripts': 'evince-synctex = evince_synctex:main',
    },
    classifiers=[
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
