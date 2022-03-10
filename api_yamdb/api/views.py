from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Genre, Review, Title, User

from .filters import TitleFilter
from .mixins import CreateListDestroyViewSet, PerformViewSet
from .permissions import (AdminPermission, IsAuthorAdminModeratorOrReadOnly,
                          IsAdminOrReadOnly)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, LoginSerializer,
                          RegistrationSerializer, ReviewSerializer,
                          TitleInputSerializer, TitleOutputSerializer,
                          TokenSerializer, UserSerializer)


class TitleViewSet(viewsets.ModelViewSet):

    queryset = Title.objects.annotate(rating=Avg('reviews__score'))
    serializer_class = TitleOutputSerializer
    ordering_fields = ('name',)
    ordering = ('name',)
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter
    permission_classes = (IsAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return TitleInputSerializer
        return TitleOutputSerializer


class GenreViewSet(CreateListDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class CategoryViewSet(CreateListDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (filters.SearchFilter,)
    lookup_field = 'slug'
    permission_classes = (IsAdminOrReadOnly,)
    search_fields = ('name',)

    def retrieve(self, request, pk=None, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, pk=None, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)


class AuthViewSet(PerformViewSet):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer

    def get_access_token(self, user):
        return RefreshToken.for_user(user).access_token

    @action(methods=['post'], detail=False)
    def signup(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK,
                        headers=headers)

    @action(methods=['post'], detail=False)
    def token(self, request):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        token = serializer.validated_data['confirmation_code']
        user = get_object_or_404(User, username=username)

        user_token = get_object_or_404(Token, user=user)

        if token == user_token.key:
            access_token = str(self.get_access_token(user))
            data = {'token': access_token}
            jwt = TokenSerializer(data=data)
            jwt.is_valid()
            return Response(jwt.data, status=status.HTTP_200_OK)

        jwt = TokenSerializer(data={})
        jwt.is_valid()
        return Response(jwt.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsAuthorAdminModeratorOrReadOnly,
    ]

    def _get_title(self):
        return get_object_or_404(Title, pk=self.kwargs['title_id'])

    def get_queryset(self):
        return self._get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self._get_title())


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsAuthorAdminModeratorOrReadOnly,
    ]

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review)

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        return review.comments.all()


class UserViewSet(viewsets.ModelViewSet):

    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'username'
    permission_classes = (AdminPermission,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username', )

    @action(methods=['get', 'patch'],
            permission_classes=[IsAuthenticated], detail=False)
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        role = request.user.role
        is_admin = request.user.is_admin or request.user.is_superuser
        serializer = self.get_serializer(request.user,
                                         data=request.data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)
        if not is_admin:
            serializer.validated_data['role'] = role
        serializer.save()
        return Response(serializer.data)
