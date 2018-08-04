from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import reverse_lazy
from django.views.generic import RedirectView

urlpatterns = [
    url(r'^$', RedirectView.as_view(url=reverse_lazy('admin:app_article_changelist')), name='home'),
    url(r'^', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    debug_urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

    urlpatterns = debug_urlpatterns + urlpatterns
