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

import logging
import typing

from newrelic_telemetry_sdk import Span as NewRelicSpan
from newrelic_telemetry_sdk import SpanClient
from opentelemetry.sdk.trace.export import Span, SpanExporter, SpanExportResult
from opentelemetry.trace.status import StatusCode

try:
    from opentelemetry_exporter_python.version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "unknown"  # pragma: no cover


_logger = logging.getLogger(__name__)


class NewRelicSpanExporter(SpanExporter):
    def __init__(self, *args, **kwargs):
        self.client = SpanClient(*args, **kwargs)
        self.client.add_version_info("NewRelic-OpenTelemetry-Exporter", __version__)

    @staticmethod
    def _transform(span):
        attributes = dict(span.resource.attributes)
        attributes.update(span.attributes)
        context = span.get_span_context()
        start_time = span.start_time
        duration = span.end_time - start_time
        start_time = start_time // 10 ** 6
        duration = duration // 10 ** 6
        if span.parent:
            parent_id = "{:016x}".format(span.parent.span_id)
        else:
            parent_id = None

        if span.status.status_code is not StatusCode.UNSET:
            attributes.setdefault("otel.status_code", span.status.status_code.name)
            description = span.status.description
            if description is not None:
                attributes.setdefault("otel.status_description", description)

        return NewRelicSpan(
            name=span.name,
            tags=attributes,
            guid="{:016x}".format(context.span_id),
            trace_id="{:032x}".format(context.trace_id),
            parent_id=parent_id,
            start_time_ms=start_time,
            duration_ms=duration,
        )

    def export(self, spans: typing.Sequence[Span]) -> SpanExportResult:
        try:
            spans = [self._transform(span) for span in spans]
            response = self.client.send_batch(spans)
        except Exception:
            _logger.exception("New Relic send_spans failed with an exception.")
            return SpanExportResult.FAILURE

        if not response.ok:
            _logger.error(
                "New Relic send_spans failed with status code: %r", response.status
            )
            return SpanExportResult.FAILURE

        return SpanExportResult.SUCCESS
