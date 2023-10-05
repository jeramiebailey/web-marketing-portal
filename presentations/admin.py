from django.contrib import admin
from .models import SlideDeckTemplate, SlideDeck, Slide, SlideTemplate


admin.site.register(SlideDeckTemplate)
admin.site.register(SlideDeck)
admin.site.register(Slide)
admin.site.register(SlideTemplate)