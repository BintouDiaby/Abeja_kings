from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.shortcuts import redirect
from core.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Override the default login view to support "remember me"
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
    path('login/', lambda request: redirect('/accounts/login/')),
]
