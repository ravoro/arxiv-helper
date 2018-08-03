from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin, FieldListFilter
from django.shortcuts import redirect
from mptt.admin import MPTTModelAdmin, TreeRelatedFieldListFilter

from .models import Article, Category

admin.site.site_header = 'Arxiv Helper'
admin.site.site_title = admin.site.site_header
admin.site.index_template = 'app/admin/index.html'
admin.site.site_url = None


class ArticleAdmin(ModelAdmin):
    actions = None
    change_form_template = 'app/admin/change_form.html'
    change_list_template = 'app/admin/change_list_articles.html'
    fields = ['html_meta_safe', 'categories']
    filter_horizontal = ['categories']
    list_display = ['__str__', 'title', 'categories_str', 'is_processed', 'date_updated']
    list_filter = [('categories', TreeRelatedFieldListFilter)]
    ordering = ['-date_updated', '-id_arxiv']
    readonly_fields = ['html_meta_safe']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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
    fields = ['parent', 'name']


class ArticleDigest(Article):
    class Meta:
        proxy = True


class UsedDatesListFilter(FieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_generic = '%s' % field_path
        self.date_params = {k: v for k, v in params.items() if k.startswith(self.field_generic)}
        self.lookup_kwarg_date = '%s' % field_path

        dates_queryset = Article.objects.all().values('date_updated').distinct().order_by('-date_updated')
        dates = [d['date_updated'] for d in dates_queryset]
        dates_links = [(str(d), {self.lookup_kwarg_date: str(d)}) for d in dates]
        self.links = [('Any date', {})] + dates_links

        super().__init__(field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg_date]

    def choices(self, changelist):
        for title, param_dict in self.links:
            yield {
                'selected': self.date_params == param_dict,
                'query_string': changelist.get_query_string(param_dict, [self.field_generic]),
                'display': title,
            }


class ArticleDigestAdmin(ModelAdmin):
    actions = None
    change_list_template = 'app/admin/change_list.html'
    list_display = ['html_meta_safe']
    list_display_links = None
    list_filter = [('date_updated', UsedDatesListFilter), ('categories', TreeRelatedFieldListFilter)]
    ordering = ['-date_updated', 'id_arxiv']


admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ArticleDigest, ArticleDigestAdmin)
