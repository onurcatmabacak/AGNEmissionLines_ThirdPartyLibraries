The CapFit Package
==================

**CapFit: Linearly-Constrained Non-Linear Least-Squares Optimization**

.. image:: http://www-astro.physics.ox.ac.uk/~cappellari/software/capfit_logo.svg
    :target: https://pypi.org/project/capfit/
    :width: 100
.. image:: https://img.shields.io/pypi/v/capfit.svg
    :target: https://pypi.org/project/capfit/
.. image:: https://img.shields.io/badge/arXiv-2208.14974-orange.svg
    :target: https://arxiv.org/abs/2208.14974
.. image:: https://img.shields.io/badge/DOI-10.1093/mnras/stad2597-green.svg
    :target: https://doi.org/10.1093/mnras/stad2597

The ``CapFit`` package provides a Python implementation of a
linearly-constrained non-linear least-squares optimization method. 
This method is described in Section 3.2 of the paper by 
`Cappellari (2023) <https://ui.adsabs.harvard.edu/abs/2023MNRAS.526.3273C>`_. 

.. contents:: :depth: 2

Attribution
-----------

If you use this software for your research, please cite the 
`Cappellari (2023)`_ paper where the algorithm was introduced. 
The BibTeX entry for the paper is::

    @ARTICLE{Cappellari2023,
        author = {{Cappellari}, M.},
        title = "{Full spectrum fitting with photometry in PPXF: stellar population
            versus dynamical masses, non-parametric star formation history and
            metallicity for 3200 LEGA-C galaxies at redshift $z\approx0.8$}",
        journal = {MNRAS},
        eprint = {2208.14974},
        year = 2023,
        volume = 526,
        pages = {3273-3300},
        doi = {10.1093/mnras/stad2597}
    }

Installation
------------

To install ``CapFit``, use the following command::

    pip install capfit

If you don't have write access to the global ``site-packages`` directory,
install it with::    

    pip install --user capfit

To upgrade to the latest version, run::

    pip install --upgrade capfit

Usage Examples
--------------

Explore how to use the ``CapFit`` package by referring to the
``capfit_examples.py`` file located within the ``capfit/examples`` directory.
You can find this file in the main ``CapFit`` package installation folder
inside the `site-packages <https://stackoverflow.com/a/46071447>`_ directory.
Detailed documentation is available in the docstring of the ``capfit.py``
file or on `PyPi <https://pypi.org/project/capfit/>`_.

###########################################################################
