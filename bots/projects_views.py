import base64
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import (
    ApiKey,
    Bot,
    BotStates,
    Credentials,
    Project,
    RecordingStates,
    Utterance,
    WebhookDeliveryAttempt,
    WebhookDeliveryAttemptStatus,
    WebhookSecret,
    WebhookSubscription,
    WebhookTriggerTypes,
)
from .utils import generate_recordings_json_for_bot_detail_view

logger = logging.getLogger(__name__)


class ProjectUrlContextMixin:
    def get_project_context(self, object_id, project):
        return {
            "project": project,
        }


class ProjectDashboardView(LoginRequiredMixin, ProjectUrlContextMixin, View):
    def get(self, request, object_id):
        try:
            project = get_object_or_404(Project, object_id=object_id, organization=request.user.organization)
        except:
            return redirect("/")

        # Quick start guide status checks
        zoom_credentials = Credentials.objects.filter(project=project, credential_type=Credentials.CredentialTypes.ZOOM_OAUTH).exists()

        deepgram_credentials = Credentials.objects.filter(project=project, credential_type=Credentials.CredentialTypes.DEEPGRAM).exists()

        has_api_keys = ApiKey.objects.filter(project=project).exists()

        has_ended_bots = Bot.objects.filter(project=project, state=BotStates.ENDED).exists()

        context = self.get_project_context(object_id, project)
        context.update(
            {
                "quick_start": {
                    "has_credentials": zoom_credentials and deepgram_credentials,
                    "has_api_keys": has_api_keys,
                    "has_ended_bots": has_ended_bots,
                }
            }
        )

        return render(request, "projects/project_dashboard.html", context)


class ProjectApiKeysView(LoginRequiredMixin, ProjectUrlContextMixin, View):
    def get(self, request, object_id):
        project = get_object_or_404(Project, object_id=object_id, organization=request.user.organization)
        context = self.get_project_context(object_id, project)
        context["api_keys"] = ApiKey.objects.filter(project=project).order_by("-created_at")
        return render(request, "projects/project_api_keys.html", context)


class CreateApiKeyView(LoginRequiredMixin, View):
    def post(self, request, object_id):
        project = get_object_or_404(Project, object_id=object_id, organization=request.user.organization)
        name = request.POST.get("name")

        if not name:
            return HttpResponse("Name is required", status=400)

        api_key_instance, api_key = ApiKey.create(project=project, name=name)

        # Render the success modal content
        return render(
            request,
            "projects/partials/api_key_created_modal.html",
            {"api_key": api_key, "name": name},
        )


class DeleteApiKeyView(LoginRequiredMixin, ProjectUrlContextMixin, View):
    def delete(self, request, object_id, key_object_id):
        api_key = get_object_or_404(
            ApiKey,
            object_id=key_object_id,
            project__organization=request.user.organization,
        )
        api_key.delete()
        context = self.get_project_context(object_id, api_key.project)
        context["api_keys"] = ApiKey.objects.filter(project=api_key.project).order_by("-created_at")
        return render(request, "projects/project_api_keys.html", context)


class RedirectToDashboardView(LoginRequiredMixin, View):
    def get(self, request, object_id, extra=None):
        return redirect("bots:project-dashboard", object_id=object_id)


class CreateCredentialsView(LoginRequiredMixin, ProjectUrlContextMixin, View):
    def post(self, request, object_id):
        project = get_object_or_404(Project, object_id=object_id, organization=request.user.organization)

        try:
            credential_type = int(request.POST.get("credential_type"))
            if credential_type not in [choice[0] for choice in Credentials.CredentialTypes.choices]:
                return HttpResponse("Invalid credential type", status=400)

            # Get or create the credential instance
            credential, created = Credentials.objects.get_or_create(project=project, credential_type=credential_type)

            # Parse the credentials data based on type
            if credential_type == Credentials.CredentialTypes.ZOOM_OAUTH:
                credentials_data = {
                    "client_id": request.POST.get("client_id"),
                    "client_secret": request.POST.get("client_secret"),
                }

                if not all(credentials_data.values()):
                    return HttpResponse("Missing required credentials data", status=400)

            elif credential_type == Credentials.CredentialTypes.DEEPGRAM:
                credentials_data = {"api_key": request.POST.get("api_key")}

                if not all(credentials_data.values()):
                    return HttpResponse("Missing required credentials data", status=400)
            elif credential_type == Credentials.CredentialTypes.GOOGLE_TTS:
                credentials_data = {"service_account_json": request.POST.get("service_account_json")}

                if not all(credentials_data.values()):
                    return HttpResponse("Missing required credentials data", status=400)
            else:
                return HttpResponse("Unsupported credential type", status=400)

            # Store the encrypted credentials
            credential.set_credentials(credentials_data)

            # Return the entire settings page with updated context
            context = self.get_project_context(object_id, project)
            context["credentials"] = credential.get_credentials()
            context["credential_type"] = credential.credential_type
            if credential.credential_type == Credentials.CredentialTypes.ZOOM_OAUTH:
                return render(request, "projects/partials/zoom_credentials.html", context)
            elif credential.credential_type == Credentials.CredentialTypes.DEEPGRAM:
                return render(request, "projects/partials/deepgram_credentials.html", context)
            elif credential.credential_type == Credentials.CredentialTypes.GOOGLE_TTS:
                return render(request, "projects/partials/google_tts_credentials.html", context)
            else:
                return HttpResponse("Cannot render the partial for this credential type", status=400)

        except Exception as e:
            return HttpResponse(str(e), status=400)


class ProjectSettingsView(LoginRequiredMixin, ProjectUrlContextMixin, View):
    def get(self, request, object_id):
        project = get_object_or_404(Project, object_id=object_id, organization=request.user.organization)

        # Try to get existing credentials
        zoom_credentials = Credentials.objects.filter(project=project, credential_type=Credentials.CredentialTypes.ZOOM_OAUTH).first()

        deepgram_credentials = Credentials.objects.filter(project=project, credential_type=Credentials.CredentialTypes.DEEPGRAM).first()

        google_tts_credentials = Credentials.objects.filter(project=project, credential_type=Credentials.CredentialTypes.GOOGLE_TTS).first()

        context = self.get_project_context(object_id, project)
        context.update(
            {
                "zoom_credentials": zoom_credentials.get_credentials() if zoom_credentials else None,
                "zoom_credential_type": Credentials.CredentialTypes.ZOOM_OAUTH,
                "deepgram_credentials": deepgram_credentials.get_credentials() if deepgram_credentials else None,
                "deepgram_credential_type": Credentials.CredentialTypes.DEEPGRAM,
                "google_tts_credentials": google_tts_credentials.get_credentials() if google_tts_credentials else None,
                "google_tts_credential_type": Credentials.CredentialTypes.GOOGLE_TTS,
            }
        )

        return render(request, "projects/project_settings.html", context)


class ProjectBotsView(LoginRequiredMixin, ProjectUrlContextMixin, View):
    def get(self, request, object_id):
        project = get_object_or_404(Project, object_id=object_id, organization=request.user.organization)

        bots = Bot.objects.filter(project=project).order_by("-created_at")

        context = self.get_project_context(object_id, project)
        context.update(
            {
                "bots": bots,
                "BotStates": BotStates,
            }
        )

        return render(request, "projects/project_bots.html", context)


class ProjectBotDetailView(LoginRequiredMixin, ProjectUrlContextMixin, View):
    def get(self, request, object_id, bot_object_id):
        project = get_object_or_404(Project, object_id=object_id, organization=request.user.organization)

        bot = get_object_or_404(Bot, object_id=bot_object_id, project=project)

        # Prefetch recordings with their utterances and participants
        bot.recordings.all().prefetch_related(models.Prefetch("utterances", queryset=Utterance.objects.select_related("participant")))

        # Prefetch bot events with their debug screenshots
        bot.bot_events.prefetch_related("debug_screenshots")

        # Get webhook delivery attempts for this bot
        webhook_delivery_attempts = WebhookDeliveryAttempt.objects.filter(bot=bot).select_related("webhook_subscription").order_by("-created_at")

        context = self.get_project_context(object_id, project)
        context.update(
            {
                "bot": bot,
                "BotStates": BotStates,
                "RecordingStates": RecordingStates,
                "recordings": generate_recordings_json_for_bot_detail_view(bot),
                "webhook_delivery_attempts": webhook_delivery_attempts,
                "WebhookDeliveryAttemptStatus": WebhookDeliveryAttemptStatus,
            }
        )

        return render(request, "projects/project_bot_detail.html", context)


class ProjectWebhooksView(LoginRequiredMixin, ProjectUrlContextMixin, View):
    def get(self, request, object_id):
        project = get_object_or_404(Project, object_id=object_id, organization=request.user.organization)
        context = self.get_project_context(object_id, project)
        context["webhooks"] = WebhookSubscription.objects.filter(project=project).order_by("-created_at")
        context["webhook_options"] = [trigger_type for trigger_type in WebhookTriggerTypes]
        return render(request, "projects/project_webhooks.html", context)


class CreateWebhookView(LoginRequiredMixin, ProjectUrlContextMixin, View):
    def post(self, request, object_id):
        project = get_object_or_404(Project, object_id=object_id, organization=request.user.organization)
        url = request.POST.get("url")
        triggers = request.POST.getlist("triggers[]")

        # Check if URL is valid
        if not url.startswith("https://"):
            return HttpResponse("URL must start with https://", status=400)
        if WebhookSubscription.objects.filter(url=url, project=project).exists():
            return HttpResponse("URL already subscribed", status=400)
        # There is a limit of 2 webhooks per projects for now
        if WebhookSubscription.objects.filter(project=project).count() >= 2:
            return HttpResponse("You have reached the maximum number of webhooks", status=400)

        # Check the event is subscribable
        subscribed_triggers = [int(x) for x in triggers]
        for trigger in subscribed_triggers:
            if trigger not in [trigger.value for trigger in WebhookTriggerTypes]:
                return HttpResponse(f"Invalid event type: {trigger}", status=400)

        # Get the project's secret for the webhook subscription. If new project, create a new one
        webhook_secret, created = WebhookSecret.objects.get_or_create(project=project)

        # Create the webhook subscription
        WebhookSubscription.objects.create(
            project=project,
            url=url,
            triggers=subscribed_triggers,
        )

        # Render the success modal content
        return render(
            request,
            "projects/partials/webhook_subscription_created_modal.html",
            {
                "secret": base64.b64encode(webhook_secret.get_secret()).decode("utf-8"),
                "url": url,
                "triggers": [WebhookTriggerTypes.trigger_type_to_api_code(x) for x in subscribed_triggers],
            },
        )


class DeleteWebhookView(LoginRequiredMixin, ProjectUrlContextMixin, View):
    def delete(self, request, object_id, webhook_object_id):
        webhook = get_object_or_404(
            WebhookSubscription,
            object_id=webhook_object_id,
            project__organization=request.user.organization,
        )
        webhook.delete()
        context = self.get_project_context(object_id, webhook.project)
        context["webhooks"] = WebhookSubscription.objects.filter(project=webhook.project).order_by("-created_at")
        context["webhook_options"] = [trigger_type for trigger_type in WebhookTriggerTypes]
        return render(request, "projects/project_webhooks.html", context)
