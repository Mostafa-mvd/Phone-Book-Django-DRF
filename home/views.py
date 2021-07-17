from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils.translation import activate
from django.shortcuts import redirect, render


class ShowHome(TemplateView):
    template_name = "home.html"

    # def get(self, request, *arg, **kwarg):
    #     lang = request.GET.get("lang", 'en')

    #     if lang == 'en':
    #         activate('en')
    #     elif lang == 'fa':
    #         activate('fa')
    #     return render(template_name=self.get_template_names(), request=request)


class ShowActivities(LoginRequiredMixin, TemplateView):
    template_name = "activities.html"

    def get_context_data(self, **kwargs):
        context = super(ShowActivities, self).get_context_data()
        activities = []

        for _tuple in self.request.session.get("user_activities", []):
            activities += [{
                "action_input": _tuple[0],
                "action_message": _tuple[1]
            }]

        reversed_lst = list(reversed(activities))

        context.update({
            "activities": reversed_lst[0:5]
        })

        return context



