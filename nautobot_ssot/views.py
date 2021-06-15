"""Django views for Single Source of Truth (SSoT)."""

import pprint

from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from django_rq import get_queue
from django_rq.queues import get_connection
from rq import Worker

from nautobot.extras.models import JobResult
from nautobot.extras.views import ObjectChangeLogView
from nautobot.core.views.generic import BulkDeleteView, ObjectDeleteView, ObjectEditView, ObjectListView, ObjectView

from .filters import SyncFilter, SyncLogEntryFilter
from .forms import SyncFilterForm, SyncLogEntryFilterForm
from .jobs import get_data_jobs
from .models import Sync, SyncLogEntry
from .tables import DashboardTable, SyncTable, SyncLogEntryTable


class DashboardView(ObjectListView):
    """Dashboard / overview of SSoT."""

    queryset = Sync.objects.all()
    table = DashboardTable
    action_buttons = []
    template_name = "nautobot_ssot/dashboard.html"

    def extra_context(self):
        data_sources, data_targets = get_data_jobs()
        context = {
            "queryset": self.queryset,
            "data_sources": data_sources,
            "data_targets": data_targets,
            "source": {},
            "target": {},
        }
        sync_ct = ContentType.objects.get_for_model(Sync)
        for source in context["data_sources"]:
            context["source"][source.name] = self.queryset.filter(
                job_result__obj_type=sync_ct,
                job_result__name=source.class_path,
            )
        for target in context["data_targets"]:
            context["target"][target.name] = self.queryset.filter(
                job_result__obj_type=sync_ct,
                job_result__name=target.class_path,
            )

        return context

class SyncListView(ObjectListView):
    """View for listing Sync records."""

    queryset = Sync.queryset()
    filterset = SyncFilter
    filterset_form = SyncFilterForm
    table = SyncTable
    action_buttons = []
    template_name = "nautobot_ssot/history.html"

    def extra_context(self):
        data_sources, data_targets = get_data_jobs()
        return {
            "data_sources": data_sources,
            "data_targets": data_targets,
        }


class SyncDeleteView(ObjectDeleteView):
    """View for deleting a single Sync record."""

    queryset = Sync.objects.all()


class SyncBulkDeleteView(BulkDeleteView):
    """View for bulk-deleting Sync records."""

    queryset = Sync.objects.all()
    table = SyncTable


class SyncView(ObjectView):
    """View for details of a single Sync record."""

    queryset = Sync.queryset()
    template_name = "nautobot_ssot/sync_detail.html"

    def get_extra_context(self, request, instance):
        """Add additional context to the view."""
        return {
            "diff": pprint.pformat(instance.diff, width=180, compact=True),
        }


class SyncJobResultView(ObjectView):
    """View for the JobResult associated with a single Sync record."""

    queryset = Sync.objects.all()
    template_name = "nautobot_ssot/sync_jobresult.html"

    def get_extra_context(self, request, instance):
        """Add additional context to the view."""
        return {
            "active_tab": "jobresult",
        }


class SyncLogEntriesView(ObjectListView):
    """View for SyncLogEntries associated with a given Sync."""

    queryset = SyncLogEntry.objects.all()
    filterset = SyncLogEntryFilter
    filterset_form = SyncLogEntryFilterForm
    table = SyncLogEntryTable
    action_buttons = []
    template_name = "nautobot_ssot/sync_logentries.html"

    def get(self, request, pk):
        instance = get_object_or_404(Sync.objects.all(), pk=pk)
        self.queryset = SyncLogEntry.objects.filter(sync=instance)

        return super().get(request)


class SyncChangeLogView(ObjectChangeLogView):
    base_template = "nautobot_ssot/sync_header.html"


class SyncLogEntryListView(ObjectListView):
    """View for listing SyncLogEntry records."""

    queryset = SyncLogEntry.objects.all()
    filterset = SyncLogEntryFilter
    filterset_form = SyncLogEntryFilterForm
    table = SyncLogEntryTable
    action_buttons = []
    template_name = "nautobot_ssot/synclogentry_list.html"
