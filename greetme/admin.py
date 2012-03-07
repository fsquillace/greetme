from django.contrib import admin
from models import Greeting, Language, DefaultLanguage, ExcludedFriend


admin.site.register(Greeting)
admin.site.register(Language)
admin.site.register(DefaultLanguage)
admin.site.register(ExcludedFriend)