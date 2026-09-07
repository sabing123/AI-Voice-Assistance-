from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.shortcuts import redirect
from django.contrib import messages
from .forms import EnhancedUserCreationForm, UserUpdateForm, UserProfileUpdateForm
from .models import UserProfile

class SignUpView(CreateView):
    form_class = EnhancedUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('assistant:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('assistant:index')

    def get_success_url(self):
        return self.success_url

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('assistant:index')


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileUpdateForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'user_form' not in context:
            if self.request.method == 'POST':
                context['user_form'] = UserUpdateForm(self.request.POST, instance=self.request.user)
            else:
                context['user_form'] = UserUpdateForm(instance=self.request.user)

        context['profile_form'] = context.get('form') or self.get_form()
        context['username'] = f"{self.request.user.first_name} {self.request.user.last_name}"

        for field in context['user_form'].fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        for field in context['profile_form'].fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = self.get_form()

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile and account details have been updated successfully! ✨")
            return redirect(self.success_url)
        
        return self.render_to_response(self.get_context_data(form=profile_form, user_form=user_form))
