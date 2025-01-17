.. _setup:

Installation and configuration
==============================

This section summarizes the steps required to install a wis2box instance and setup your own datasets using example configurations.

Ensure you have Docker, Docker Compose and Python installed on your host, as detailed in :ref:`getting-started`.

Download
--------

Download the wis2box setup files from the `wis2box Releases`_ page.  Go to the latest release
and download the ``wis2box-setup-<release>.zip`` file from the Assets section.

.. code-block:: bash

   wget https://github.com/wmo-im/wis2box/releases/download/<release>/wis2box-setup-<release>.zip
   unzip wis2box-setup-<release>.zip
   cd wis2box-<release>


Environment variables
---------------------

wis2box uses environment variables from ``dev.env`` to its containers on startup.
An example file is provided in ``examples/config/wis2box.extended.env``. 
Copy this file to your working directory, and update it to suit your needs.

.. code-block:: bash

   cp examples/config/wis2box.env dev.env

.. note::

   You must map ``WIS2BOX_HOST_DATADIR`` to the absolute path of a directory on your host machine. This path will be mapped to ``/data/wis2box`` inside the wis2box-management container
   To enable external data sharing you must set ``WIS2BOX_URL`` to the URL pointing to where your host is exposed on the public network.

Updated variables in ``dev.env``, for example:

.. code-block:: bash

   # data-directory on your host machine that will map to /data/wis2box on the wis2box-container
   WIS2BOX_HOST_DATADIR=/home/wis2box-user/wis2box-data
   
   # update broker default credentials
   WIS2BOX_BROKER_USERNAME=wis2box-user
   WIS2BOX_BROKER_PASSWORD=wis2box123
   WIS2BOX_BROKER_HOST=mosquitto
   WIS2BOX_BROKER_PORT=1883

   WIS2BOX_BROKER_PUBLIC=mqtt://${WIS2BOX_BROKER_USERNAME}:${WIS2BOX_BROKER_PASSWORD}@mosquitto:1883

   # update storage default credentials
   WIS2BOX_STORAGE_USERNAME=wis2box-user
   WIS2BOX_STORAGE_PASSWORD=wis2box123

   # set logging and data retention
   WIS2BOX_LOGGING_LOGLEVEL=INFO
   WIS2BOX_DATA_RETENTION_DAYS=30

   # update minio settings after updating storage and broker defaults
   MINIO_ROOT_USER=${WIS2BOX_STORAGE_USERNAME}
   MINIO_ROOT_PASSWORD=${WIS2BOX_STORAGE_PASSWORD}
   MINIO_NOTIFY_MQTT_USERNAME_WIS2BOX=${WIS2BOX_BROKER_USERNAME}
   MINIO_NOTIFY_MQTT_PASSWORD_WIS2BOX=${WIS2BOX_BROKER_PASSWORD}
   MINIO_NOTIFY_MQTT_BROKER_WIS2BOX=tcp://${WIS2BOX_BROKER_HOST}:${WIS2BOX_BROKER_PORT}

Data mappings
-------------

wis2box configuration requires a data mappings file, which defines the plugins used to process your data.
Example mapping files are provided in the current directory:

* ``synop-bufr-mappings.yml``, input is BUFR data containing surface synoptic observations
* ``synop-csv-mappings.yml``, input is CSV data containing surface synoptic observations

For example, if your incoming data contains ``.bufr4`` files containing synoptic observations, and your ``WIS2BOX_HOST_DATADIR`` environment variable
is set to ``/home/wis2box-user/wis2box-data``, you can copy the following example:

.. code-block:: bash

   cat synop-bufr-mappings.yml >> /home/wis2box-user/wis2box-data/data-mappings.yml

.. note::

   The file should be called ``data-mappings.yml`` and should be placed in the directory you defined as ``WIS2BOX_HOST_DATADIR``.

Edit ``/home/wis2box-user/wis2box-data/data-mappings.yml``:
 
 * Replace ``country`` with your corresponding ISO 3166 alpha-3 country code in lowercase
 * Replace ``centre_id`` with the string identifying the centre running your wis2node in lowercase, alphanumeric characters

If you need to define multiple datasets, you can add multiple entries in your ``data-mappings.yml``. For example:

.. code-block:: bash

   data:
      ita.italy_wmo_demo.data.core.weather.surface-based-observations.synop:
        plugins:
            bufr:
                - plugin: wis2box.data.bufr4.ObservationDataBUFR
                  notify: true
                  buckets:
                    - ${WIS2BOX_STORAGE_INCOMING}
                  file-pattern: '*'
            bufr4:
                - plugin: wis2box.data.bufr2geojson.ObservationDataBUFR2GeoJSON
                  buckets:
                    - ${WIS2BOX_STORAGE_PUBLIC}
                  file-pattern: '^WIGOS_(\d-\d+-\d+-\w+)_.*\.bufr4$'
      ita.italy_wmo_demo.data.core.weather.surface-based-observations.temp:
        plugins:
            bufr:
                - plugin: wis2box.data.bufr4.ObservationDataBUFR
                  notify: true
                  buckets:
                    - ${WIS2BOX_STORAGE_INCOMING}
                  file-pattern: '*'
            bufr4:
                - plugin: wis2box.data.bufr2geojson.ObservationDataBUFR2GeoJSON
                  buckets:
                    - ${WIS2BOX_STORAGE_PUBLIC}
                  file-pattern: '^WIGOS_(\d-\d+-\d+-\w+)_.*\.bufr4$'
      
In this case the data mappings configuration has specified 2 datasets (SYNOP, and TEMP).

.. note::

   The dataset identifier is used to define the topic hierarchy for your data (see `WIS2 topic hierarchy`_).  The top 3 levels of the WIS2 topic hierarchy (``origin/a/wis2``) are automatically included by wis2box when publishing your data.
    
   * dataset: ita.italy_wmo_demo.data.core.weather.surface-based-observations.synop
   * topic-hierarchy: origin/a/wis2/ita/italy_wmo_demo/data/core/weather/surface-based-observations/synop

.. note::
   
   In these examples, files in the ``wis2box-incoming`` storage bucket are processed to produce ``.bufr4`` stored in the ``wis2box-public`` storage bucket, using either the ``bufr4.ObservationDataBUFR`` or the ``wis2box.data.csv2bufr.ObservationDataCSV2BUFR`` plugins.

   Files in the ``wis2box-public`` storage bucket are converted to GeoJSON and stored in the wis2box API backend using the ``wis2box.data.bufr2geojson.ObservationDataBUFR2GeoJSON`` plugin.

   You can provide your own plugins as needed; for more information (see :ref:`extending-wis2box`).


Station metadata list
---------------------

wis2box requires information about the stations for which you will be sharing data.

An example of the configuration file for the stations is provided in ``station_list.csv``. 

You can copy this file to ``metadata/station/station_list.csv`` in your $WIS2BOX_HOST_DATADIR :

.. code-block:: bash

   mkdir -p /home/wis2box-user/wis2box-data/metadata/station
   cp station_list.csv /home/wis2box-user/wis2box-data/metadata/station

And edit ``metadata/station/station_list.csv`` to include the data for your stations.

.. note::

   The ``station_list.csv`` requires column names ``station_name`` and the ``wigos_station_identifier`` (WSI) with which the station is registered in `OSCAR`_.  Optionally, you can provide a ``traditional_station_identifier (TSI)`` column.
   The TSI can be left empty if your data contains a WSI. If your data contains a TSI but no WSI, the ``station_list.csv`` will be used to derive the corresponding WSI for that station.

Discovery metadata
------------------

Discovery metadata provides the data description needed for users to discover your data when searching the WIS2 Global Discovery Catalogue.

Updated discovery metadata records are shared globally through the MQTT endpoint defined in your wis2box.

Discovery metadata records can be defined using the YAML syntax shared via ``WIS2BOX_HOST_DATADIR``.

An example is provided in ``surface-weather-observations.yml``. Each dataset requires its own discovery metadata configuration file.

You can copy the file ``surface-weather-observations.yml`` to the directory you defined for ``WIS2BOX_HOST_DATADIR`` and update it to provide the correct discovery metadata for your dataset:

* replace ``[country].[centre_id].data.core.weather.surface-based-observations.synop`` with the topic as previously used in ``$WIS2BOX_HOST_DATADIR/data-mappings.yml``
* text provided in ``identification.title`` and ``identification.abstract`` will be displayed in the wis2box user interface
* provide a valid geographic bounding box in ``identification.extents.spatial.bbox``

Starting wis2box
----------------

Once you have prepared the necessary configuration files as described above you are ready to start the wis2box.

Run the following command to start wis2box:

.. code-block:: bash

   python3 wis2box-ctl.py start

This might take a while the first time, as Docker images will be downloaded.

.. note::

   The ``wis2box-ctl.py`` program is used as a convenience utility around a set of Docker Compose commands.
   You can customize the ports exposed on your host by editing ``docker-compose.override.yml``.
   
Once the command above is completed, check that all services are running (and healthy).

.. code-block:: bash

   python3 wis2box-ctl.py status

Which should display the following:

.. code-block:: bash

            Name                       Command                  State                           Ports
   -----------------------------------------------------------------------------------------------------------------------
   cadvisor                 /usr/bin/cadvisor -logtostderr   Up (healthy)   8080/tcp
   elasticsearch            /bin/tini -- /usr/local/bi ...   Up (healthy)   9200/tcp, 9300/tcp
   grafana                  /run.sh                          Up             0.0.0.0:3000->3000/tcp
   loki                     /usr/bin/loki -config.file ...   Up             3100/tcp
   mosquitto                /docker-entrypoint.sh /usr ...   Up             0.0.0.0:1883->1883/tcp, 0.0.0.0:8884->8884/tcp
   mqtt_metrics_collector   python3 -u mqtt_metrics_co ...   Up             8000/tcp, 0.0.0.0:8001->8001/tcp
   nginx                    /docker-entrypoint.sh ngin ...   Up             0.0.0.0:80->80/tcp
   prometheus               /bin/prometheus --config.f ...   Up             9090/tcp
   wis2box                  /entrypoint.sh wis2box pub ...   Up
   wis2box-api              /app/docker/es-entrypoint.sh     Up
   wis2box-auth             /entrypoint.sh                   Up
   wis2box-minio            /usr/bin/docker-entrypoint ...   Up (healthy)   0.0.0.0:9000->9000/tcp, 0.0.0.0:9001->9001/tcp
   wis2box-ui               /docker-entrypoint.sh ngin ...   Up             0.0.0.0:9999->80/tcp

Refer to the :ref:`troubleshooting` section if this is not the case. 

You should now be able to view collections on the wis2box API by visiting ``http://localhost/oapi/collections`` in a web browser, which should appear as follows:

.. image:: ../_static/wis2box-api-initial.png
  :width: 800
  :alt: Initial wis2box API collections list

The API will show one (initially empty) collection 'Data Notifications'. 
This collection will be filled when you start ingesting data and publishing WIS2 notifications.

.. note::

   Additional collections will be added during the runtime configuration.

Runtime configuration
---------------------

The following last design time steps are then required once wis2box is running.

Login to the wis2box-management container

.. code-block:: bash

   python3 wis2box-ctl.py login

.. note::

   ``$WIS2BOX_DATADIR`` is the location that ``$WIS2BOX_HOST_DATADIR`` binds to **inside** the container. 
   This allows wis2box to access the configuration files from **inside** the wis2box-management container.
   By default, ``WIS2BOX_DATADIR`` points to ``/data/wis2box`` **inside** the wis2box-management container.

The first step is add the new dataset as defined by the YAML file for your discovery metadata record defined previously, using the following command:

.. code-block:: bash

   wis2box data add-collection $WIS2BOX_DATADIR/surface-weather-observations.yml

.. note::

   If you see an error like ``ValueError: No plugins for XXX defined in data mappings``, exit the wis2box-container and edit the ``data-mappings.yml`` file in the directory defined by ``WIS2BOX_HOST_DATADIR``

You can view the collection you just added, by re-visiting ``http://localhost/oapi/collections`` in a web browser.

.. image:: ../_static/wis2box-api-added-collection.png
  :width: 800
  :alt: wis2box API collections list with added collection

The second step is to publish discovery metadata and cache its content in the wis2box API:

.. code-block:: bash

   wis2box metadata discovery publish $WIS2BOX_DATADIR/surface-weather-observations.yml

This command publishes an MQTT message with information about your dataset to the WIS2 Global Discovery Catalogue. Repeat this command whenever you have to provide updated metadata about your dataset.

You can review the discovery metadata just cached through the new link in  ``http://localhost/oapi/collections``:

.. image:: ../_static/wis2box-api-discovery-metadata.png
  :width: 800
  :alt: wis2box API collections list with added discovery metadata

The final step is to publish your station information to the wis2box API from the station metadata list you prepared:

.. code-block:: bash

   wis2box metadata station publish-collection

You can review the stations you just cached through the new link in  ``http://localhost/oapi/collections``:

.. image:: ../_static/wis2box-api-stations.png
  :width: 800
  :alt: wis2box API collections list with added stations

You can now logout of wis2box-management container:

.. code-block:: bash

   exit

The next is the :ref:`data-ingest`.

.. _`wis2box Releases`: https://github.com/wmo-im/wis2box/releases
.. _`WIS2 topic hierarchy`: https://github.com/wmo-im/wis2-topic-hierarchy
.. _`OSCAR`: https://oscar.wmo.int/surface
