import logging
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from users.signals import logout_signal


logger = logging.getLogger(__name__)


class LoginUser(LoginView):
    template_name = "users/login_form.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home:home")
        return super().get(request)

    def form_invalid(self, form):
        logger.info('login form was invalid.')
        messages.error(self.request, form.errors)
        return super().form_invalid(form)


class LogoutUser(LogoutView):
    # template_name = "users/logout.html"

    def dispatch(self, request, *args, **kwargs):
        logout_signal.send(sender=self.__class__, user=request.user)
        return super().dispatch(request, args, kwargs)
