from django.core.mail import send_mail
from django.utils import timezone

from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.generics import get_object_or_404
from rest_framework.validators import UniqueValidator

from reviews.models import Category, Comment, Genre, Review, Title, User

from api_yamdb.settings import VERIFICATION_EMAIL


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        exclude = ('id',)


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        exclude = ('id',)
        model = Category


class TitleOutputSerializer(serializers.ModelSerializer):

    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.FloatField()

    class Meta:
        fields = (
            'id', 'year', 'name', 'genre', 'category', 'description',
            'rating'
        )
        model = Title


class TitleInputSerializer(serializers.ModelSerializer):

    category = serializers.SlugRelatedField(slug_field='slug',
                                            queryset=Category.objects.all())
    genre = serializers.SlugRelatedField(many=True, slug_field='slug',
                                         queryset=Genre.objects.all())

    class Meta:
        model = Title
        fields = (
            'id', 'year', 'name', 'genre', 'category', 'description',
        )

    def validate_year(self, year):
        if year > timezone.now().year:
            raise serializers.ValidationError('Cannot assign year')
        return year


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True)

    class Meta:
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        model = Review

    def validate(self, value):
        if self.context['request'].method != 'POST':
            return value
        title = self.context['view'].kwargs['title_id']
        author = self.context['request'].user
        if author.reviews.filter(title=title).exists():
            raise serializers.ValidationError(
                'Вы уже делали ревью'
            )
        return value


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True)
    review = serializers.SlugRelatedField(
        slug_field='id', read_only=True)

    class Meta:
        fields = '__all__'
        model = Comment


class RegistrationSerializer(serializers.ModelSerializer):

    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email')

    def send_confirmation_token(self, user):

        token = Token.objects.get_or_create(user=user)[0]

        subject = 'verification code'
        text = f'your verification code is: {token}'
        send_mail(subject=subject, message=text,
                  from_email=VERIFICATION_EMAIL,
                  recipient_list=[user.email])

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError('Please enter the valid name')
        return value

    def validate(self, attrs):
        name = attrs['username']
        email = attrs['email']

        if User.objects.filter(username=name, email=email).exists():
            user = User.objects.get(username=name)
            self.send_confirmation_token(user)
            raise serializers.ValidationError(
                'This user is already registered. '
                'Please check your email to get the confirmation code')

        email_exists = (User.objects.exclude(username=name)
                                    .filter(email=email).exists())
        if email_exists:
            raise serializers.ValidationError('This email is already used.')
        user_exists = (User.objects.exclude(email=email)
                                   .filter(username=name).exists())
        if user_exists:
            raise serializers.ValidationError('This username is already used.')

        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.save()
        self.send_confirmation_token(user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=200)
    confirmation_code = serializers.CharField(max_length=200)

    def validate(self, attrs):
        username = attrs['username']
        code = attrs['confirmation_code']
        user = get_object_or_404(User, username=username)
        if not Token.objects.filter(user=user, key=code).exists():
            raise serializers.ValidationError('User is not registered yet'
                                              'or confirmation code is wrong')

        return attrs


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[
        UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User

        fields = ('username', 'email', 'first_name',
                  'last_name', 'bio', 'role')
