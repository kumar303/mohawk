from setuptools import setup, find_packages


setup(name='mohawk',
      version='0.1.0',
      description="Library for Hawk HTTP authorization",
      long_description='',
      author='Kumar McMillan, Austin King',
      author_email='kumar.mcmillan@gmail.com',
      license='MPL 2.0 (Mozilla Public License)',
      url='https://github.com/kumar303/mohawk',
      include_package_data=True,
      classifiers=[],
      packages=find_packages(exclude=['tests']),
      install_requires=[])
