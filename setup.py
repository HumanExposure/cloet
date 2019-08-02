from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()
setup(name='cloet',
      version='0.1',
      description='Command Line Occupational Exposure Tool',
      long_description=readme(),
      classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: GNU GPLv3 License',
        'Natural Language :: English',
        'Operating Systems :: Windows :: Windows 10'
        'Programming Language :: Python :: 3.5',],
      keywords='CLOET ChemSTEER chemical-exposure USEPA occupational-exposure',
      # url='https://github.com/HumanExposure/cloet',
      author='Katherine A. Phillips',
      author_email='phillips.katherine@epa.gov',
      license='GNU GPLv3',
      packages=['cloet'],
      include_package_data=True,
      zip_safe=False)
