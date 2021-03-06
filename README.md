PySeidon
================

### Project description ###
* This project aims to meet multiple objectives of the EcoEII consortium
  through the setting of a dedicated server and the development of Python
  based packages. This project can be seen as two folded. On the one 
  hand, it aims to enhance data accessibility for all the partners of 
  the EcoEII consortium thanks to simple client protocols. On the other 
  hand, it aims to develop standardised numerical toolbox gathering 
  specific analysis functions for measured and simulated data (FVCOM model)
  to the EcoEII partners.
* Additionally, this project was the ideal opportunity to transport various
  scripts and packages accumulated over the years into Python. These scripts
  and packages have been extensively used by the tidal energy community for
  more than a decade. The 'Contributors' section of this document is a 
  mere attempt to acknowledge the work of those who participated more or
  less indirectly to the development of this tool box. We are consciously
  standing on the shoulders of a multitude giants...so please forgive us
  if we forgot one of them.  
* The present package is currently in Beta testing, so the more feedback,
  the better

### Installation ###
Prerequisites:
* Python 2.7: You can download Python from [here](http://www.python.org/download) 
* IPython: You can download IPython from [here](http://ipython.org/)
* Anaconda: You can download Anaconda from [here](http://continuum.io/downloads#all)
* setuptools: You can download setuptools from [here](https://pypi.python.org/pypi/setuptools#installation-instructions)
* UTide: You can download UTide from [here](https://github.com/wesleybowman/UTide)
* Pydap: You can download Pydap from [here](http://www.pydap.org/)
* NetworkX: You can download NetworkX from [here](http://networkx.github.io/documentation/latest/install.html)
* Pandas: You can download Pandas from [here](http://pandas.pydata.org/pandas-docs/stable/install.html)
* Seaborn: You can download Seaborn from [here](http://web.stanford.edu/~mwaskom/software/seaborn/installing.html)


Installation:
* Step 1a: Download PySeidon package, save it on your machine and Unzip
* Step 1b: or clone the repository
* Step 2: from a shell, change directory to PySeidon-master folder
* Step 3: from the shell, as superuser/admin, type `python setup.py install`
  or `python setup.py install --user`

Up-dating:
* The code will evolve and improve with time. To up-date, simply go through
  the installation procedure again.
* To test the installation, type *'from pyseidon import *'* in Ipython shell.

### Contribution guidelines ###
* [Tutorial 1](http://nbviewer.ipython.org/github/GrumpyNounours/PySeidon/blob/master/PySeidon%20Tutorial.ipynb)

### Contacts ###
* Project Leader: [Richard Karsten](richard.karsten@acadiau.ca)
* Repository admin: [Thomas Roc](thomas.roc@acadiau.ca)
* Developers: [Wesley Bowman](https://github.com/wesleybowman), [Thomas Roc](thomas.roc@acadiau.ca), [Jonathan Smith](https://github.com/LaVieEnRoux)

### Contributors ###
Dr. Brian Polagye, Dr. Richard Karsten, [Dr. Kristen Thyng](https://github.com/kthyng), [Aidan Bharath](https://github.com/Aidan-Bharath), Mitchell O'Flaherty-Sproul, Robie Hennigar, Justine McMillan,...

### Legal Information ###
* Authorship attributed to Wesley Bowman, Thomas Roc and Jonathan Smith
* Copyright (c) 2014 EcoEnergyII
* Licensed under an Affero GPL style license v3.0 (see License_PySeidon.txt)
