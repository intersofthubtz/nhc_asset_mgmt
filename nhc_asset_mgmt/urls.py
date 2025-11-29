from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

def home(request):
    return redirect('login')

urlpatterns = [
    path('admin/logout/',
        auth_views.LogoutView.as_view(next_page='/admin/login/'),
        name='admin_logout'
    ),
    path('admin/', admin.site.urls),
    
    
    path('accounts/', include('accounts.urls')),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),

    # Correct inclusion for the assets app
    path('assets/', include('assets.urls', namespace='assets')),
    path('requests/', include('requests.urls', namespace='requests')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



