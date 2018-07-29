from mptt.forms import TreeNodeChoiceField, TreeNodeMultipleChoiceField


class CustomTreeNodeChoiceField(TreeNodeChoiceField):
    def label_from_instance(self, obj):
        return obj._name_choices_str


class CustomTreeNodeMultipleChoiceField(TreeNodeMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj._name_choices_str
