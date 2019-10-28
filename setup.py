from setuptools import setup, find_packages


setup(name='mohawk',
      version='1.1.0',
      description="Library for Hawk HTTP authorization",
      long_description="""
Hawk lets two parties securely communicate with each other using
messages signed by a shared key.
It is based on HTTP MAC access authentication (which
was based on parts of OAuth 1.0).

The Mohawk API is a little different from that of the Node library
(i.e. https://github.com/hueniverse/hawk).
It was redesigned to be more intuitive to developers, less prone to security problems, and more Pythonic.

Read more: https://github.com/kumar303/mohawk/
      """,
      author='Kumar McMillan, Austin King',
      author_email='kumar.mcmillan@gmail.com',
      license='MPL 2.0 (Mozilla Public License)',
      url='https://github.com/kumar303/mohawk',
      include_package_data=True,
      classifiers=[
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Topic :: Internet :: WWW/HTTP',
      ],
      packages=find_packages(exclude=['tests']),
      install_requires=['six'])
