# Copyright 2020 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
from datetime import datetime, timedelta

import pytest
from newrelic_telemetry_sdk import SpanClient
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Span, SpanContext
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor, SpanExportResult
from opentelemetry.trace import SpanKind
from opentelemetry.trace.status import Status, StatusCode

from opentelemetry_ext_newrelic import NewRelicSpanExporter


@pytest.fixture()
def span_exporter(hosts, insert_key):
    exporter = NewRelicSpanExporter(
        insert_key=insert_key,
        host=hosts["trace"],
    )
    return exporter


@pytest.fixture()
def span_processor(span_exporter):
    processor = BatchExportSpanProcessor(
        span_exporter,
        schedule_delay_millis=500,
    )
    return processor


def to_timestamp(time):
    return int((time - datetime(1970, 1, 1)).total_seconds() * 1e9)


class MockSpan(Span):
    """Redefining to allow us to manually create a span outside of a tracer."""

    def __init__(
        self,
        *args,
        context=None,
        start_time=None,
        end_time=None,
        status_code=None,
        status_description=None,
        **kwargs
    ):
        # Create necessary objects
        new_context = SpanContext(**context) if context else None

        # Run self init
        super(MockSpan, self).__init__(*args, context=new_context, **kwargs)

        # Setting post init attributes
        self.set_status(Status(status_code, status_description))
        self._start_time = start_time
        self._end_time = end_time


START_TIME = datetime.utcnow()
TIMES = [START_TIME + timedelta(seconds=x) for x in range(0, 4)]
TIMES = [to_timestamp(x) for x in TIMES]
RESOURCE = Resource.create({"service.name": "Python Application"})
EXC_DESC = "ValueError: 1 != 2"

PARENT_SPAN_DATA = {
    "name": "foo",
    "resource": RESOURCE,
    "start_time": TIMES[0],
    "end_time": TIMES[3],
    "context": {
        "trace_id": 0x7665A7DAB06A328546F626281529A044,
        "span_id": 0xC480C9007FA21FB8,
        "trace_state": {},
        "is_remote": False,
    },
    "attributes": {"custom_attribute": "ABC"},
    "set_status_on_exception": True,
    "kind": SpanKind.SERVER,
    "status_code": StatusCode.ERROR,
    "status_description": EXC_DESC,
    "trace_config": None,
}

SPAN_DATA = {
    "name": "bar",
    "resource": RESOURCE,
    "start_time": TIMES[1],
    "end_time": TIMES[2],
    "context": {
        "trace_id": 0x7665A7DAB06A328546F626281529A044,
        "span_id": 0x941ED81CAB98022C,
        "trace_state": {},
        "is_remote": False,
    },
    "attributes": {"custom_attribute": "DEF"},
    "set_status_on_exception": True,
    "kind": SpanKind.SERVER,
    "status_code": StatusCode.OK,
    "trace_config": None,
}

PARENT_SPAN = MockSpan(**PARENT_SPAN_DATA)
SPAN = MockSpan(**SPAN_DATA, parent=PARENT_SPAN.context)

WEIRD_SPAN_DATA = PARENT_SPAN_DATA.copy()
WEIRD_SPAN_DATA["status_description"] = None
WEIRD_SPAN = MockSpan(**WEIRD_SPAN_DATA)


def test_spans(http_responses, span_exporter, decompress_payload):
    duration = 1000
    timestamp = TIMES[1] // 1.0e6

    assert len(http_responses) == 0
    exporter_status_code = span_exporter.export([SPAN])
    assert exporter_status_code == SpanExportResult.SUCCESS
    assert len(http_responses) == 1
    response = http_responses.pop()

    # Verify headers
    user_agent = response.request.headers["user-agent"]
    assert user_agent.split()[-1].startswith("NewRelic-OpenTelemetry-Exporter/")

    # Verify payload
    data = json.loads(decompress_payload(response.request.body))
    assert len(data) == 1
    data = data[0]
    spans = data["spans"]
    assert len(spans) == 1
    span = spans[0]
    attributes = span["attributes"]

    assert int(span["id"], 16) == SPAN_DATA["context"]["span_id"]
    assert span["timestamp"] == timestamp
    assert int(span["trace.id"], 16) == SPAN_DATA["context"]["trace_id"]

    for name, value in SPAN.attributes.items():
        assert attributes[name] == value

    assert attributes["duration.ms"] == duration
    assert attributes["name"] == SPAN.name
    assert int(attributes["parent.id"], 16) == SPAN.parent.span_id

    assert attributes["otel.status_code"] == SPAN_DATA["status_code"].name

    assert attributes["service.name"] == "Python Application"


def test_exception_spans(http_responses, span_exporter, decompress_payload):
    assert len(http_responses) == 0
    exporter_status_code = span_exporter.export([PARENT_SPAN])
    assert exporter_status_code == SpanExportResult.SUCCESS
    assert len(http_responses) == 1
    response = http_responses.pop()

    # Verify payload
    data = json.loads(decompress_payload(response.request.body))
    assert len(data) == 1
    data = data[0]
    spans = data["spans"]
    assert len(spans) == 1
    span = spans[0]
    attributes = span["attributes"]

    assert int(span["id"], 16) == PARENT_SPAN_DATA["context"]["span_id"]
    assert attributes["name"] == PARENT_SPAN.name

    for name, value in PARENT_SPAN.attributes.items():
        assert attributes[name] == value

    assert attributes["otel.status_code"] == PARENT_SPAN_DATA["status_code"].name
    assert attributes["otel.status_description"] == EXC_DESC


def test_exception_spans_no_description(
    http_responses, span_exporter, decompress_payload
):
    assert len(http_responses) == 0
    exporter_status_code = span_exporter.export([WEIRD_SPAN])
    assert exporter_status_code == SpanExportResult.SUCCESS
    assert len(http_responses) == 1
    response = http_responses.pop()

    # Verify payload
    data = json.loads(decompress_payload(response.request.body))
    assert len(data) == 1
    data = data[0]
    spans = data["spans"]
    assert len(spans) == 1
    span = spans[0]
    attributes = span["attributes"]

    assert int(span["id"], 16) == WEIRD_SPAN_DATA["context"]["span_id"]
    assert attributes["name"] == WEIRD_SPAN.name

    for name, value in WEIRD_SPAN.attributes.items():
        assert attributes[name] == value

    assert attributes["otel.status_code"] == WEIRD_SPAN_DATA["status_code"].name
    assert "otel.status_description" not in attributes


def test_send_spans_exception(span_exporter, caplog):
    # Remove the client object to force an exception when send_spans is called
    delattr(span_exporter, "client")

    status_code = span_exporter.export([SPAN_DATA])
    assert status_code == SpanExportResult.FAILURE

    assert (
        "opentelemetry_ext_newrelic.span",
        logging.ERROR,
        "New Relic send_spans failed with an exception.",
    ) in caplog.record_tuples


@pytest.mark.http_response(status_code=500)
def test_bad_http_response(span_exporter):
    span_exporter.export([SPAN])


def test_default_exporter_values(insert_key):
    exporter = NewRelicSpanExporter(insert_key)

    assert exporter.client._pool.host == SpanClient.HOST
    assert exporter.client._pool.port == 443


def test_override_exporter_values(insert_key):
    host = "non-default-host"
    port = 8080
    exporter = NewRelicSpanExporter(
        insert_key,
        host=host,
        port=port,
    )

    assert exporter.client._pool.host == host
    assert exporter.client._pool.port == port
