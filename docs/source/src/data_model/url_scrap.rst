URLScrap
========

Overview
--------

Model representing external (scraped or predefined) URLs linked to railway stops.
Each entry stores:
- A unique URL
- Its type (enumerated in ``URLType``)
- An optional relation to a ``Stop`` (via ``stop_id``)

Typical data source example (see ``data/urls_r2nord.json``):

.. code-block:: json

    {
      "url_type": "ADIF_WEB",
      "url": "https://www.adif.es/w/71801-barcelona-sants",
      "stop": "71801"
    }

Example
-------

Creating an instance from a JSON-like dictionary:

.. code-block:: python

    from src.data_model.url_scrap import URLScrap
    raw = {
        "url": "https://www.adif.es/w/71801-barcelona-sants",
        "url_type": "ADIF_WEB",
        "stop": "71801"
    }
    obj = URLScrap.object_hook(raw)   # Returns a URLScrap instance (or None if keys missing)

Code
----

.. autoclass:: src.data_model.url_scrap.URLScrap
   :members:
   :exclude-members: __tablename__, __table_args__, url, url_id, url_type, stop_id, stop
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: src.data_model.url_scrap.URLType
   :members:
   :exclude-members: ADIF_WEB, ADIF_JS_INFO
   :undoc-members:
   :show-inheritance:
   :private-members:

.. autoclass:: src.data_model.url_scrap.URLScrapParams
   :members:
   :exclude-members:
   :undoc-members:
   :show-inheritance:
   :private-members:
