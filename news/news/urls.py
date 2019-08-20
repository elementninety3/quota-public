"""news URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path, reverse_lazy
# from django.conf.urls import url
from django.contrib.auth import views as authviews
from django.views.generic import RedirectView

from bulletin import views, tokens

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='landing', permanent=False)),
    path('beta/', include('bulletin.urls')),
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name = 'signup'),
    re_path(r'^login/$', authviews.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    re_path(r'^activation_sent/$', views.activation_sent, name = 'activation_sent'),
    path('activate/(<str:uidb64>/<str:token>', views.activate, name='activate'),
    path('unsubscribe', views.unsubscribe, name='unsubscribe'),


]

#Add Django site authentication urls (for login, logout, password management)
urlpatterns += [

#     re_path(r'^accounts/password/reset/$',
#   authviews.PasswordResetView,
#   {
#     'post_reset_redirect': reverse_lazy('auth_password_reset_done'),
#     'html_email_template_name': 'registration/password_reset_html_email.html'
#   },
#   name='auth_password_reset'),

    path('password_reset/', authviews.PasswordResetView.as_view(
    html_email_template_name='registration/password_reset_html_email.html')),
    path('', include('django.contrib.auth.urls')),
]
