from django.conf.urls.defaults import *

from greetme.views import index, add_greets, remove_greets, set_default_lang, deauth

from django.views.i18n import set_language

from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
                       (r'^$', index),
                       (r'^greetme/$', index),
                       (r'^greetme/add/$', add_greets),
                       (r'^greetme/remove/$',remove_greets), 
                       (r'^greetme/options/$', set_default_lang),
                       (r'^greetme/deauth/$', deauth),
                       
                       
                       (r'^i18n/set_lang/$', set_language),                       

                       
                       
                       #(r'^greetme/site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),


    # Example:
    # (r'^greetme/', include('greetme.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
     (r'^greetme/admin/', include(admin.site.urls)),
)
