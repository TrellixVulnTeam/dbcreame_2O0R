from rest_framework import serializers
from .models import Objeto, ObjetoThingi, Categoria, Tag, Usuario, ObjetoPersonalizado, Compra
from django.contrib.auth.models import User, AnonymousUser


class ObjetoSerializer(serializers.ModelSerializer):
    #images = serializers.StringRelatedField(many=True)
    #images = serializers.SlugRelatedField(many=True, read_only=True,slug_field='name')

    def liked_get(self,obj):
        print(self.context['request'].user)
        if self.context['request'].user.is_authenticated:
            return self.context['request'].user.usuario.liked_objects.filter(pk=obj.id).exists()
        else:
            return False
    liked = serializers.SerializerMethodField('liked_get')

    class Meta:
        depth = 4
        model = Objeto
        fields = ('id', 'name', 'description', 'like_count', 'main_image', 'images',
         'files', 'author', 'creation_date', 'category', 'tags', 'external_id', 'liked',
         'hidden')

class ObjetoThingiSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjetoThingi
        fields = ('id', 'external_id', 'status', 'file_list')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)

'''
Definimos el serializador de Compra con un poco mas de cuidado, para poder serializar
en forma nesteada una compra; simplificando la creacion de estas.
'''

class ObjetoPersonalizadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjetoPersonalizado
        fields = ('name','object_id','color','scale','quantity')

class CompraSerializer(serializers.ModelSerializer):
    purchased_objects = ObjetoPersonalizadoSerializer(many=True)
    class Meta:
        model = Compra
        fields = ('id','buyer','purchased_objects','date','status','delivery_address','payment_method')
