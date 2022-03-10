from rest_framework import mixins, viewsets


class PerformViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    pass


class CreateListDestroyViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    pass
