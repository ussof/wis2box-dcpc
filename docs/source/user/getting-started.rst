.. _getting-started:

Getting started
===============

wis2box can be run on any Linux instance (bare metal or cloud hosted VM) with Python, Docker and Docker Compose installed. 
The recommended OS is Ubuntu 22.04 LTS.

System requirements
-------------------

System requirements depend on the amount of data ingested.  We recommend minimum 2vCPUs, 4GB Memory and 16GB of local storage.

For example, the following Amazon AWS ec2-instance-types have been utilized as part of `wis2box demonstrations <https://demo.wis2box.wis.wmo.int>`_.

* 0 - 2000 observations per day: "t3a.medium"-instance: 2vCPUs, x86_64 architecture, 4GB Memory, up to 5 Gigabit network, 16GB attached storage (~35 USD per month for on-demand Linux based OS)
* 2000 - 10000 observations per day: "t3a.large"-instance: 2vCPUs, x86_64 architecture, 8GB Memory, up to 5 Gigabit network, 24GB attached storage (~70 USD per month for on-demand Linux based OS)

Software dependencies
---------------------

The services in wis2box are provided through a stack of `Docker`_ containers, which are configured using `Docker Compose`_. 

wis2box requires the following prior to installation:

.. csv-table::
   :header: Requirement,Version
   :align: left

   Python,3.8 or higher
   Docker Engine, 20.10.14 or higher
   Docker Compose, 1.29.2

The following commands can be used to inspect the available versions of Python, Docker and Docker Compose on your system:

.. code-block:: bash

    docker version
    docker-compose version
    python3 -V

Once you have verified these requirements, go to :ref:`setup` for a step-by-step guide to install and configure your wis2box.

.. _`Docker`: https://docs.docker.com/get-started/overview
.. _`Docker Compose`: https://github.com/docker/compose/releases
