from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    debug_urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

    urlpatterns = debug_urlpatterns + urlpatterns
