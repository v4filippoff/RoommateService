from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_patterns = [
    path('', include('apps.user.urls')),
    path('', include('apps.city.urls')),
    path('', include('apps.card.urls')),
    path('', include('apps.chat.urls')),
    path('', include('apps.review.urls')),
]

urlpatterns = [
    path('api/', include(api_patterns)),
    path('admin/', admin.site.urls),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
