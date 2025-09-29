import django_filters
from .models import Message

class MessageFilter(django_filters.FilterSet):
    min_date = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr='gte')
    max_date = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr='lte')
    sender = django_filters.CharFilter(field_name='sender__username', lookup_expr='iexact')
    conversation = django_filters.NumberFilter(field_name='conversation__id')

    class Meta:
        model = Message
        fields = ['sender', 'conversation', 'min_date', 'max_date']
