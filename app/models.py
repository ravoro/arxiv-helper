from bs4 import BeautifulSoup
from django.db.models import Model
from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField, CharField, DateField, TextField
from django.utils.functional import cached_property
from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField


class Article(Model):
    id_arxiv = CharField(max_length=20, unique=True)
    categories = TreeManyToManyField('Category',
                                     blank=True)
    # TODO - validate that only contains a whitelist of html tags
    html_meta = TextField()
    is_processed = BooleanField(default=False)
    date_submitted = DateField()
    date_updated = DateField()

    @cached_property
    def title(self):
        soup = BeautifulSoup(self.html_meta, 'html.parser')
        title_tag = soup.select_one('.list-title')
        title_tag.select_one('span').decompose()
        return title_tag.text.strip()

    @cached_property
    def categories_str(self):
        cats = [c.name for c in self.categories.all()]
        return ', '.join(cats)

    categories_str.short_description = 'Categories'

    def __str__(self):
        return "arXiv:{}".format(self.id_arxiv)


class Category(MPTTModel):
    parent = TreeForeignKey('self',
                            on_delete=CASCADE,
                            null=True,
                            blank=True)
    name = CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

    class MPTTMeta:
        order_insertion_by = ['name']
