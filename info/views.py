import logging
from django.views.generic.base import View
import rest_framework
import weasyprint
from collections import defaultdict
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS, PermissionDenied
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, UpdateView, DeleteView
from info.helper_functions import add_to_session
from . import forms, models


from .serializers import AddPhoneNumberSerializer
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.mixins import CreateModelMixin
from rest_framework.generics import CreateAPIView
from rest_framework.viewsets import ViewSetMixin, ModelViewSet
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from info import serializers


logger = logging.getLogger(__name__)


class PhoneNumberViewSet(ModelViewSet):
    queryset = models.PhoneBook.objects.all()
    serializer_class = serializers.AddPhoneNumberSerializer
    # permission_classes = [permissions.IsAuthenticated]



class AddPhoneNumber(LoginRequiredMixin, FormView):
    form_class = forms.AddInfoFrom
    qs_dict = defaultdict(dict)

    def get(self, request, *args, **kwargs):
        return render(request, "add_info.html", context={'form': self.form_class})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        phone_number = self.request.POST.get("phone_number", None)
        phone_number_qs = models.PhoneBook.objects.filter(user=request.user.id).filter(phone_number=phone_number)

        if not phone_number_qs:
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            logger.info("phone number qs not found.")
            form.add_error("phone_number", "phone number already exists in your phone book")
            return self.form_invalid(form)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.save()

        # Edit Cache
        qs = models.PhoneBook.objects.filter(user=form.instance.user)
        self.qs_dict[self.request.GET.get("page", "1")] = qs
        cache.set(f"{self.request.user.id}", self.qs_dict, 120)

        # Add to session
        new_phone_number_input = form.data["phone_number"]
        add_to_session(self.request.session, "Added", new_phone_number_input)

        return JsonResponse(
            {
                "messages": "Your information successfully saved",
                "new_info_row": form.cleaned_data,
                "result": True
            },
            status=200
        )

    def form_invalid(self, form):
        error_messages = []

        for field in form:
            for error in field.errors:
                error_messages.append({field.name: error})

        new_phone_number_input = form.data["phone_number"]
        add_to_session(self.request.session, "Not Added", new_phone_number_input)
        logger.info("Add form was invalid.")

        return JsonResponse(
            {
                "messages": error_messages,
                "result": False
            },
            status=201
        )


class SearchPhoneNumber(LoginRequiredMixin, ListView):
    model = models.PhoneBook
    template_name = "search.html"
    phone_number_input = None

    def get(self, request, *args, **kwargs):
        self.phone_number_input = self.request.GET.get('phone_number', None)

        if self.phone_number_input:
            qs = self.get_queryset()
            results_count = qs.count()
            return JsonResponse(
                {
                    "results": list(qs.values()),
                    "results_count": results_count
                }, status=200)
        else:
            return render(request, self.template_name)

    def get_queryset(self):
        phone_number_input = self.phone_number_input
        radio_box_number = self.request.GET['checked_radio_box_number']

        qs = super().get_queryset()
        qs = qs.filter(user=self.request.user)

        if radio_box_number == "1":
            qs = qs.filter(phone_number=phone_number_input)
        elif radio_box_number == "2":
            qs = qs.filter(phone_number__startswith=phone_number_input)
        elif radio_box_number == "3":
            qs = qs.filter(phone_number__endswith=phone_number_input)
        else:
            qs = qs.filter(phone_number__contains=phone_number_input)

        add_to_session(self.request.session, "Searched For", phone_number_input)

        return qs


class EditPhoneNumber(LoginRequiredMixin, UpdateView):
    success_url = reverse_lazy("info:show_info")
    fields = ("phone_number",)
    qs_dict = defaultdict(dict)

    def get_object(self, queryset=None):
        pk = self.request.GET.get("pk", None)

        if pk:
            if pk.isdigit():
                user = self.request.user
                phone_obj = get_object_or_404(klass=models.PhoneBook, pk=pk)

                if user == phone_obj.user:
                    return phone_obj
                else:
                    # It is common to use 404 error instead of other error for preventing dissemination of information
                    # raise PermissionDenied
                    logger.error("HTTP404 occurred because user has no permission to write.")
                    raise Http404
            else:
                # The requested resource could not be found
                logger.error("HTTP404 occurred because pk was not digit.")
                raise Http404
        else:
            logger.error("HTTP404 occurred because pk was none.")
            raise Http404

    def form_valid(self, form):
        form.save()

        # Edit Cache
        qs = models.PhoneBook.objects.filter(user=form.instance.user)
        self.qs_dict[self.request.GET.get("page", "1")] = qs
        cache.set(f"{self.request.user.id}", self.qs_dict, 120)

        # Add to session
        old_phone_number_input = form.initial["phone_number"]
        new_phone_number_input = form.data["phone_number"]
        add_to_session(self.request.session, "Edited", f'{old_phone_number_input} -> {new_phone_number_input}')

        return JsonResponse({
            'result': True,
            'messages': "You've successfully edited"
        }, status=200)

    def form_invalid(self, form):
        logger.info("Edit form was invalid.")
        old_phone_number_input = form.initial["phone_number"]
        new_phone_number_input = form.data["phone_number"]
        add_to_session(self.request.session, "Not Edited", f'{old_phone_number_input} -> {new_phone_number_input}')

        return JsonResponse({
            'result': False,
            'messages': form.errors
        }, status=422)


class ShowPhoneNumbers(LoginRequiredMixin, ListView):
    model = models.PhoneBook
    template_name = "show_and_edit.html"
    paginate_by = 3
    qs_dict = defaultdict(dict)

    def get_queryset(self):

        # Low-Level Cache
        user_cache = cache.get(f"{self.request.user.id}", defaultdict(dict))  # dict
        qs = user_cache.get(self.request.GET.get("page", "1"), None)  # queryset

        if not qs:
            qs = super().get_queryset()
            qs = qs.filter(user=self.request.user).order_by("created_time")
            self.qs_dict[self.request.GET.get("page", "1")] = qs
            cache.set(f"{self.request.user.id}", self.qs_dict, 120)

        return qs


class DownloadPhoneBook(LoginRequiredMixin, ListView):
    model = models.PhoneBook
    template_name = "download_phone_number_page.html"

    def get(self, request, *args, **kwargs):
        response =  super().get(request, *args, **kwargs)
        content = response.rendered_content
        download_pdf = weasyprint.HTML(string=content, base_url='http://127.0.0.1:8000').write_pdf()
        pdf_response = HttpResponse(download_pdf, content_type="application/pdf")
        return pdf_response

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(user=self.request.user)
        return qs


class DeletePhoneNumber(LoginRequiredMixin, DeleteView):
    model = models.PhoneBook
    success_url = reverse_lazy("info:show_info")
    qs_dict = defaultdict(dict)

    def delete(self, request, *args, **kwargs):
        delete_respone = super().delete(request, *args, **kwargs)

        # Edit Cache
        user_cache = cache.get(f"{self.request.user.id}", defaultdict(dict))
        qs = user_cache.get(self.request.GET.get("page", "1"), None)
        self.qs_dict[self.request.GET.get("page", "1")] = qs.exclude(pk=kwargs['pk']).all()
        cache.set(f"{self.request.user.id}", self.qs_dict, 120)

        # Add to session
        deleted_phone_number_input = self.object.phone_number
        add_to_session(self.request.session, "Deleted", f'{deleted_phone_number_input}')

        return delete_respone

