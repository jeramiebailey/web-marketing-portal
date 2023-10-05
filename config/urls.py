from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views
from config.views import index

handler400 = 'rest_framework.exceptions.bad_request'

urlpatterns = [
    path("", index, name="home"),
    path("reporting/", include("reporting.urls", namespace="reporting")),
    # Django Admin, use {% url 'admin:index' %}
    # User management
    url(r'^', include('django.contrib.auth.urls')),
    path("accounts/", include("allauth.urls")),
    # path("anymail/", include("anymail.urls")),
    path('api/', include('api.urls', namespace="api")),
    path(settings.ADMIN_URL, admin.site.urls),
] + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
        url(r'^silk/', include('silk.urls', namespace='silk')),
    ] 
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
