

from django.utils import decorators
from info import forms, models, serializers, statics_func
from info import permissions as info_permissions

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, UpdateView, DeleteView
from django.utils.encoding import smart_str

from rest_framework import status, viewsets, filters, decorators
from rest_framework import permissions as rest_permissions
from rest_framework.response import Response

import csv, json, logging, weasyprint
from collections import defaultdict


logger = logging.getLogger(__name__)


# RestAPI View --------------------------------------------------------------


class PhoneNumberViewSet(viewsets.ModelViewSet):
    search_fields = ['phone_number', 'first_name', 'last_name', ]
    filter_backends = (filters.SearchFilter,)
    queryset = models.PhoneBook.objects.all()
    serializer_class = serializers.PhoneNumberSerializer
    permission_classes = [rest_permissions.IsAuthenticated, info_permissions.PhoneNumberCreatorOrNot]

    def create(self, request, *args, **kwargs):
        """Create User Object With API"""

        if statics_func.phone_number_exists_or_not(request):
            return super().create(request, *args, **kwargs)
        else:
            error = {"detail": "Your phone already exists"}
            return Response(data=error, status=status.HTTP_409_CONFLICT)
    
    def update(self, request, *args, **kwargs):
        """Update User Object With API"""

        if statics_func.phone_number_exists_or_not(request):
            return super().update(request, *args, **kwargs)
        else:
            error = {"detail": "Your phone already exists"}
            return Response(data=error, status=status.HTTP_409_CONFLICT)
    
    @decorators.action(detail=False, description="Download", url_path="download")
    def download_phone_numbers(self, request, *args, **kwargs):
        resp = self.list(request)
        phone_numbers_lst = json.loads(json.dumps(resp.data))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="phone_numbers.csv"'

        csv_writer = csv.writer(response, csv.excel)
        response.write(u'\ufeff'.encode('utf8'))

        # writing headers
        csv_writer.writerow([
            smart_str(u"pk"),
            smart_str(u"first_name"),
            smart_str(u"last_name"),
            smart_str(u"phone_number"),
            smart_str(u"created_time")
        ])

        for phone_number in phone_numbers_lst:
            row = []
            for val in phone_number.values():
                row.append(val)
            csv_writer.writerow(row)

        return response
    
    def filter_queryset(self, queryset):
        """Get User's Phone Number"""

        qs = super().filter_queryset(queryset)
        qs = qs.filter(user=self.request.user)
        return qs


# Normal Views --------------------------------------------------------------


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
        statics_func.add_to_session(self.request.session, "Added", new_phone_number_input)

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
        statics_func.add_to_session(self.request.session, "Not Added", new_phone_number_input)
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

        statics_func.add_to_session(self.request.session, "Searched For", phone_number_input)

        return qs


class EditPhoneNumber(LoginRequiredMixin, UpdateView):
    queryset = models.PhoneBook.objects.all()
    fields = ("phone_number",)
    qs_dict = defaultdict(dict)

    def post(self, request, *args, **kwargs):
        # the number is given by user from form's field
        new_phone_number = request.POST.get("phone_number", None)
        existing_phone_number_obj = models.PhoneBook.objects.filter(phone_number=new_phone_number)

        # for checking if new phone number is given that does exist or not
        if existing_phone_number_obj:
            # the phone number is chosen for updating in otherwise the row of table that has this phone number is our HTML
            chosen_phone_number = self.get_object()
            form = self.get_form()
            form.initial['phone_number'] = chosen_phone_number.phone_number
            form.add_error("phone_number", "Your phone number already exist.")

            return self.form_invalid(form)

        return super().post(request, *args, **kwargs)

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
        statics_func.add_to_session(self.request.session, "Edited", f'{old_phone_number_input} -> {new_phone_number_input}')

        return JsonResponse({
            'result': True,
            'messages': "You've successfully edited"
        }, status=200)

    def form_invalid(self, form):
        logger.info("Edit form was invalid.")
        old_phone_number_input = form.initial["phone_number"]
        new_phone_number_input = form.data["phone_number"]
        statics_func.add_to_session(self.request.session, "Not Edited", f'{old_phone_number_input} -> {new_phone_number_input}')

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
        statics_func.add_to_session(self.request.session, "Deleted", f'{deleted_phone_number_input}')

        return delete_respone
