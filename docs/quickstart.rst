Quickstart
==========

Installing opentelemetry-ext-newrelic
-------------------------------------

To start, the ``opentelemetry-ext-newrelic`` package must be installed. To install
through pip:

.. code-block:: bash

    $ pip install opentelemetry-ext-newrelic

If that fails, download the library from its GitHub page and install it using:

.. code-block:: bash

    $ python setup.py install


Using the span exporter
-----------------------

To start, the following packages must be installed.

* ``opentelemetry-ext-newrelic``

Additionally, the example code assumes you've set the following environment variables:

* ``NEW_RELIC_INSERT_KEY``

.. code-block:: python

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

Using the span exporter with auto-instrumentation
-------------------------------------------------

To start, the following packages must be installed.

* ``opentelemetry-ext-newrelic``
* ``opentelemetry-instrumentation-flask``
* ``flask``

Additionally, the example code assumes you've set the following environment variables:

* ``NEW_RELIC_INSERT_KEY``

.. code-block:: python

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


Find and use data
-----------------

Tips on how to find and query your data in New Relic:

* `Find trace/span data <https://docs.newrelic.com/docs/understand-dependencies/distributed-tracing/trace-api/introduction-trace-api#view-data>`_

For general querying information, see:

* `Query New Relic data <https://docs.newrelic.com/docs/using-new-relic/data/understand-data/query-new-relic-data>`_
* `Intro to NRQL <https://docs.newrelic.com/docs/query-data/nrql-new-relic-query-language/getting-started/introduction-nrql>`_
