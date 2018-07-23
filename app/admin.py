from django.conf.urls import url
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from mptt.admin import MPTTModelAdmin, TreeRelatedFieldListFilter

from .models import Article, Category

admin.site.site_header = 'Arxiv Helper'
admin.site.site_title = admin.site.site_header
admin.site.index_template = 'app/admin/index.html'
admin.site.site_url = None


class ArticleAdmin(admin.ModelAdmin):
    actions = None
    change_form_template = 'app/admin/change_form.html'
    change_list_template = 'app/admin/change_list.html'
    list_display = ['__str__', 'title', 'categories_str']
    list_filter = [('categories', TreeRelatedFieldListFilter)]
    readonly_fields = ['html_meta_safe']
    fields = ['html_meta_safe', 'categories']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # override queryset for "article list" page to only display procesed articles
        # otherwise need to use unfiltered queryset, because add/edit/etc. pages expect article being in queryset
        if request.path == reverse('admin:app_article_changelist'):
            qs = self.model.objects.processed_with_categories()
            ordering = self.get_ordering(request)
            if ordering:
                qs = qs.order_by(*ordering)
            return qs
        return super().get_queryset(request)

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context.update({
            'unprocessed_articles_count': Article.objects.unprocessed().count(),
        })
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context.update({
            'show_save_and_continue': False,
        })
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def save_form(self, request, form, change):
        form.instance.is_processed = True
        return super().save_form(request, form, change)

    def process_next_article_view(self, request):
        next_article = self.model.objects.oldest_unprocessed()
        if not next_article:
            messages.success(request, 'All done! No new articles.')
            return redirect('admin:app_article_changelist')
        unprocessed_articles_count = Article.objects.unprocessed().count()
        remaining_unprocessed_articles_count = unprocessed_articles_count - 1 if unprocessed_articles_count > 0 else 0
        context = {
            'show_custom_submit_row': True,
            'remaining_unprocessed_articles_count': remaining_unprocessed_articles_count,
        }
        return super().change_view(request, object_id=str(next_article.id), extra_context=context)

    def response_change(self, request, obj):
        return redirect('admin:process-next-article')

    def get_urls(self):
        old_urls = super().get_urls()
        new_urls = [
            url(r'^process-next-article/$',
                view=admin.site.admin_view(self.process_next_article_view),
                name='process-next-article'),
        ]
        return new_urls + old_urls


class CategoryAdmin(MPTTModelAdmin):
    pass


admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)
