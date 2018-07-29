from bs4 import BeautifulSoup
from django.db.models import Model, QuerySet
from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField, CharField, DateField, TextField
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField

from app.forms.mptt import CustomTreeNodeChoiceField, CustomTreeNodeMultipleChoiceField


class ArticleQuerySet(QuerySet):
    def processed_with_categories(self):
        return self.filter(is_processed=True).exclude(categories=None)

    def unprocessed(self):
        return self.filter(is_processed=False)

    def oldest_unprocessed(self):
        return self.unprocessed().order_by('id_arxiv').first()


class CustomTreeForeignKey(TreeForeignKey):
    def formfield(self, **kwargs):
        kwargs['form_class'] = CustomTreeNodeChoiceField
        return super().formfield(**kwargs)


class CustomTreeManyToManyField(TreeManyToManyField):
    def formfield(self, **kwargs):
        kwargs['form_class'] = CustomTreeNodeMultipleChoiceField
        return super().formfield(**kwargs)


class Article(Model):
    id_arxiv = CharField(max_length=20, unique=True)
    categories = CustomTreeManyToManyField('Category',
                                           blank=True)
    # TODO - validate that only contains a whitelist of html tags
    html_meta = TextField()
    is_processed = BooleanField(default=False)
    date_submitted = DateField()
    date_updated = DateField(verbose_name='Date')

    objects = ArticleQuerySet.as_manager()

    @cached_property
    def title(self):
        soup = BeautifulSoup(self.html_meta, 'html.parser')
        title_tag = soup.select_one('.list-title')
        title_tag.select_one('span').decompose()
        return title_tag.text.strip()

    @cached_property
    def categories_str(self):
        cats = [c._name_choices_str for c in self.categories.all()]
        return mark_safe('<br>'.join(cats))

    categories_str.short_description = 'Categories'

    def html_meta_safe(self):
        return mark_safe(self.html_meta)

    html_meta_safe.short_description = 'Abstract'

    def __str__(self):
        return "arXiv:{}".format(self.id_arxiv)


class Category(MPTTModel):
    parent = CustomTreeForeignKey('self',
                                  on_delete=CASCADE,
                                  null=True,
                                  blank=True)
    name = CharField(max_length=255)
    _name_choices_str = CharField(max_length=255)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        ancestors = [str(a) for a in self.parent.get_ancestors(include_self=True)] if self.parent else []
        self._name_choices_str = '/'.join(ancestors + [self.name])
        res = super().save(*args, **kwargs)
        for child in self.get_children():
            child.save(*args, **kwargs)  # update child's _name_choices_str
        return res

    class Meta:
        verbose_name_plural = "categories"

    class MPTTMeta:
        order_insertion_by = ['name']
