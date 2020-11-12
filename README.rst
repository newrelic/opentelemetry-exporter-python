|Community Project header|

New Relic OpenTelemetry Python Exporter
=======================================

An
`OpenTelemetry <https://github.com/open-telemetry/opentelemetry-python>`__
exporter for sending spans to New Relic using the New Relic Python
Telemetry SDK. Currently, spans as of OpenTelemetry v0.15b0 are
supported. For details on how OpenTelemetry data is mapped to New Relic
data, see documentation in `our exporter specifications
documentation <https://github.com/newrelic/newrelic-exporter-specs>`__.

Installation
------------

To start, the ``opentelemetry-ext-newrelic`` package must be installed.
To install through pip:

.. code:: python

       $ pip install opentelemetry-ext-newrelic

If that fails, download the library from its GitHub page and install it
using:

.. code:: python

       $ python setup.py install

Getting Started
---------------

In order to use the exporter, you will need to set the
``NEW_RELIC_INSERT_KEY`` environment variable with your `Insights Insert
API
Key <https://docs.newrelic.com/docs/insights/insights-data-sources/custom-data/introduction-event-api#>`__.

Usage
-----

Using the span exporter
-----------------------

The following code sample assumes you have set the
``NEW_RELIC_INSERT_KEY`` environment variable and installed the
following packages:

-  ``opentelemetry-ext-newrelic``

.. code:: python

   import os
   from opentelemetry import trace
   from opentelemetry.sdk.resources import Resource
   from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
   from opentelemetry_ext_newrelic import NewRelicSpanExporter
   from opentelemetry.sdk.trace import TracerProvider

   trace.set_tracer_provider(
       TracerProvider(resource=Resource.create({"service.name": "otel-python"}))
   )

   trace.get_tracer_provider().add_span_processor(
       BatchExportSpanProcessor(
           NewRelicSpanExporter(
               os.environ["NEW_RELIC_INSERT_KEY"], 
           ),
           schedule_delay_millis=500,
       )
   )

   tracer = trace.get_tracer(__name__)
   with tracer.start_as_current_span("foo"):
       with tracer.start_as_current_span("bar"):
           print("Hello World from OpenTelemetry Python!")

..

Using the span exporter with auto-instrumentation
-------------------------------------------------

The following code sample assumes you have set the
``NEW_RELIC_INSERT_KEY`` environment variable and installed the
following packages:

-  ``opentelemetry-ext-newrelic``
-  ``opentelemetry-instrumentation-flask``
-  ``flask``

.. code:: python

   import os
   from opentelemetry import trace
   from opentelemetry.instrumentation.flask import FlaskInstrumentor
   from opentelemetry.sdk.resources import Resource
   from opentelemetry.sdk.trace import TracerProvider
   from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
   from opentelemetry_ext_newrelic import NewRelicSpanExporter
   from flask import Flask
   app = Flask(__name__)
   FlaskInstrumentor().instrument_app(app)
   trace.set_tracer_provider(
       TracerProvider(resource=Resource.create({"service.name": "otel-python-flask"}))
   )

   trace.get_tracer_provider().add_span_processor(
       BatchExportSpanProcessor(
           NewRelicSpanExporter(os.environ["NEW_RELIC_INSERT_KEY"]),
           schedule_delay_millis=500,
       )
   )

   @app.route("/")
   def hello_world():
       return "Hello World!"

   @app.route("/error")
   def raise_500():
       raise RuntimeError("Something happened!")

   if __name__ == "__main__":
       app.run(port=8080)

Find and use your data
----------------------

For tips on how to find and query your data in New Relic, see `Find
trace/span
data <https://docs.newrelic.com/docs/understand-dependencies/distributed-tracing/trace-api/introduction-trace-api#view-data>`__.

For general querying information, see: - `Query New Relic
data <https://docs.newrelic.com/docs/using-new-relic/data/understand-data/query-new-relic-data>`__
- `Intro to
NRQL <https://docs.newrelic.com/docs/query-data/nrql-new-relic-query-language/getting-started/introduction-nrql>`__

Support
-------

New Relic hosts and moderates an online forum where customers can
interact with New Relic employees as well as other customers to get help
and share best practices. Like all official New Relic open source
projects, there’s a related Community topic in the New Relic Explorers
Hub. You can find this project’s topic/threads here:

**Support Channels**

-  `New Relic
   Documentation <https://docs.newrelic.com/docs/integrations/open-source-telemetry-integrations/open-source-telemetry-integration-list/new-relics-opentelemetry-integration>`__:
   Comprehensive guidance for using our platform
-  `New Relic
   Community <https://discuss.newrelic.com/tags/pythonagent>`__: The
   best place to engage in troubleshooting questions
-  `New Relic Developer <https://developer.newrelic.com/>`__: Resources
   for building a custom observability applications
-  `New Relic University <https://learn.newrelic.com/>`__: A range of
   online training for New Relic users of every level

Contributing
------------

We encourage your contributions to improve
opentelemetry-exporter-python! Keep in mind when you submit your pull
request, you’ll need to sign the CLA via the click-through using
CLA-Assistant. You only have to sign the CLA one time per project. If
you have any questions, or to execute our corporate CLA, required if
your contribution is on behalf of a company, please drop us an email at
opensource@newrelic.com.

License
-------

opentelemetry-exporter-python is licensed under the `Apache
2.0 <http://apache.org/licenses/LICENSE-2.0.txt>`__ License.

Limitations
-----------

The New Relic Telemetry APIs are rate limited. Please reference the
documentation for `New Relic Trace API requirements and
limits <https://docs.newrelic.com/docs/apm/distributed-tracing/trace-api/trace-api-general-requirements-limits>`__
on the specifics of the rate limits.

.. |Community Project header| image:: https://github.com/newrelic/opensource-website/raw/master/src/images/categories/Community_Project.png
   :target: https://opensource.newrelic.com/oss-category/#community-project
