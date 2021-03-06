from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect

from braces.views import LoginRequiredMixin, FormValidMessageMixin, AnonymousRequiredMixin, MessageMixin
from braces.views._access import AccessMixin
from vanilla import UpdateView, CreateView, TemplateView

from .forms import UpdateEmailForm, ProfileForm, UserForm
from .models import Profile


class DonationRequiredMixin(AccessMixin, MessageMixin):
    """Requires user to have donated a specific amount"""

    donation_amount = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.profile.amount >= self.donation_amount:
            self.messages.error(
                f'Für Zugang ist eine Unterstützung in Höhe von mindestens {self.donation_amount}€ nötig')
            return HttpResponseRedirect(reverse('donations:levels'))

        return super().dispatch(
            request, *args, **kwargs)


class RedirectMixin:
    """Mixin for looking for next parameter in GET"""
    def get_success_url(self):
        return self.request.GET.get('next') or super().get_success_url()


class UpdateOrCreateRequiredMixin:
    """
    Saves (and restores) GET parameters to session and returns view to create or update profile before continuing.
    Resets after first retrieve of user.
    """
    def get(self, request, *args, **kwargs):
        """Return update if session doesn't contain current user, marked as updated."""
        profile_pk = request.session.get('updated')
        if not profile_pk or (request.user.is_authenticated and request.user.profile.pk != profile_pk):
            # Save params to session
            request.session['get_params'] = request.GET.dict()

            redirect_url = reverse('users:update') if request.user.is_authenticated else reverse('users:create')
            return HttpResponseRedirect('{}?next={}'.format(redirect_url, request.path_info))

        # Pop url params and add to GET
        get_params = request.session.pop('get_params', {})
        request.GET = request.GET.copy()
        request.GET.update(get_params)
        return super().get(request, *args, **kwargs)

    def get_profile(self):
        """Returns updated user profile and removes session variable."""
        profile_pk = self.request.session.pop('updated', None)
        if self.request.user.is_authenticated and self.request:
            return self.request.user.profile
        if profile_pk:
            return Profile.objects.get(pk=profile_pk)


class CreateUserView(AnonymousRequiredMixin, CreateView):
    form_class = UserForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('users:signup_complete')
    authenticated_redirect_url = reverse_lazy('users:profile')


class CreatedUserView(TemplateView):
    template_name = 'registration/signup_complete.html'


class CreateProfileView(AnonymousRequiredMixin, RedirectMixin, MessageMixin, CreateView):
    form_class = UserForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:profile')
    authenticated_redirect_url = reverse_lazy('users:profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['profile_form'] = ProfileForm(self.request.POST)
        else:
            context['profile_form'] = ProfileForm()
        return context

    def form_valid(self, form):
        profile_form = ProfileForm(self.request.POST)
        if profile_form.is_valid():
            user = form.save(profile_kwargs=profile_form.cleaned_data)
            self.messages.info('Profil gespeichert')
            self.request.session['updated'] = user.profile.pk
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)


class ProfileView(LoginRequiredMixin, FormValidMessageMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'users/profile.html'
    form_valid_message = 'Profil gespeichert'
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user.profile

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session['updated'] = self.object.pk
        return response


class UpdateProfileView(RedirectMixin, ProfileView):
    template_name = 'users/profile_form.html'


class UpdateEmailView(LoginRequiredMixin, FormValidMessageMixin, UpdateView):
    form_class = UpdateEmailForm
    template_name = 'users/email_form.html'
    success_url = reverse_lazy('users:profile')
    form_valid_message = 'Email-Adresse gespeichert'

    def get_object(self):
        return self.request.user
