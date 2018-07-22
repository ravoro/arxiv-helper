from django.contrib import admin
from mptt.admin import MPTTModelAdmin, TreeRelatedFieldListFilter

from .models import Article, Category

admin.site.site_header = 'Arxiv Helper'
admin.site.site_title = admin.site.site_header
admin.site.site_url = None


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'title', 'categories_str']
    list_filter = [('categories', TreeRelatedFieldListFilter)]


class CategoryAdmin(MPTTModelAdmin):
    pass


admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)
