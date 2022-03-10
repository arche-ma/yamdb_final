from django.contrib import admin

from reviews.models import Category, Genre, Review, Title

admin.site.register(Title)
admin.site.register(Genre)
admin.site.register(Category)
admin.site.register(Review)
