from setuptools import setup, find_packages

setup(name='battleship',
      version='0.1.0',
      description='sound art game of battleship',
      author='Pavel Katsev',
      author_email='pkatsev@gmail.com',
      packages=find_packages(exclude=["test.*", "test"]),
      include_package_data=True,
      install_requires=[
          'fysom',
          'bintrees',
          'rtmidi2',
      ],
      test_suite='battleship.test',
      zip_safe=False,
      entry_points={'console_scripts': [
          'battleship = battleship.game:run'
      ]})
