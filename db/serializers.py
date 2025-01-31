from rest_framework import serializers
from django.utils import timezone
import datetime
from .models import Objeto, Categoria, Tag, Usuario, ObjetoPersonalizado, Compra, ArchivoSTL, Imagen, ModeloAR, Color, SfbRotationTracker, DireccionDeEnvio, Comentario, Valoracion
from django.contrib.auth.models import User, AnonymousUser
from django_mercadopago import models as MPModels
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.conf import settings

class ArchivoSTLSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivoSTL
        depth = 4
        fields = ('id','file','printing_time_default','size_x_default','size_y_default','size_z_default','weight_default','time_as_a_function_of_scale')

class ImagenSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(use_url=True, max_length=None)

    class Meta:
        model = Imagen
        fields = ('photo',)

class ModeloArSerializer(serializers.ModelSerializer):
    combined_dimensions =  serializers.ListField(child=serializers.FloatField())

    class Meta:
        model = ModeloAR
        fields = ('combined_stl','human_flag','sfb_file','sfb_file_rotated','combined_dimensions','rotated')

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ('id','name','code','available','sfb_color_reference')

class ComentarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comentario
        fields = ('comment', 'object_id', 'name', 'creation_date')

    name = serializers.CharField(required=False)

    def create(self, validated_data):
        user = self.context['request'].user.usuario
        return Comentario.objects.create(user=user, **validated_data)


class ValoracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Valoracion
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user.usuario
        return Valoracion.objects.create(user=user, **validated_data)



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

    def images_get(self, obj):
        queryset = obj.images.order_by('-main')
        serializer_context = {'request': self.context.get('request')}
        return ImagenSerializer(queryset, many=True, context=serializer_context).data


    main_image_thumbnail = serializers.ImageField(allow_null=True, use_url=True)
    main_image = serializers.ImageField(allow_null=True, use_url=True)
    files = ArchivoSTLSerializer(many=True)
    images = serializers.SerializerMethodField('images_get')
    ar_model = ModeloArSerializer(source='modeloar')
    suggested_color = ColorSerializer()
    comments = ComentarioSerializer(many=True)
    points = serializers.FloatField()

    class Meta:
        depth = 4
        model = Objeto
        fields = ('id', 'name', 'name_es', 'description', 'like_count', 'main_image', 'main_image_thumbnail', 'images',
         'files', 'author', 'creation_date', 'category', 'tags', 'external_id', 'liked',
         'hidden','ar_model','printing_time_default_total','suggested_color','discount','partial','origin',
         'min_dimension', 'max_dimension', 'comments', 'points')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class ObjetoPersonalizadoSerializer(serializers.ModelSerializer):
    thumbnail = serializers.ImageField(allow_empty_file=True,read_only=True,use_url=True)

    class Meta:
        model = ObjetoPersonalizado
        fields = ('name','object_id','color','scale','quantity','thumbnail')
        extra_kwargs = {'color': {'required': True}}

class PaymentPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MPModels.Preference
        fields = '__all__'

class PaymentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MPModels.Notification
        fields = '__all__'

class DireccionDeEnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = DireccionDeEnvio
        fields = ('short_address','notes','last_time_used','long_address','gmaps_id')


'''
Serializadores accesorios
'''

class SfbRotationTrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SfbRotationTracker
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username','first_name','last_name','email','date_joined')

class UsuarioSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id', required=False)
    username = serializers.CharField(source='user.username', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.CharField(source='user.email', required=False)
    date_joined = serializers.DateTimeField(source='user.username', required=False)
    address_book = DireccionDeEnvioSerializer(many=True, required=False)

    class Meta:
        model = Usuario
        depth = 1
        fields = ('id','username','first_name','last_name','email','date_joined','address_book','telephone')

    def update(self, instance, validated_data, user = None):
        if user is None:
            user = self.context['request'].user
        #Actualizamos el User
        for key, value in validated_data['user'].items():
            #Unicamente permitimos que cambien ciertos atributos de usuario
            if key in ['first_name', 'last_name', 'email', 'telephone'] and value is not None:
                setattr(user, key, value)
        #Actualizamos el Usuario
        if 'telephone' in validated_data.keys():
            user.usuario.telephone = validated_data['telephone']
        user.save()
        return user.usuario

class AppSetupInformationSerializer(serializers.Serializer):
    price_per_hour = serializers.FloatField(read_only=True)
    discount_parameter_a = serializers.FloatField(read_only=True)
    discount_parameter_b = serializers.FloatField(read_only=True)

'''
Definimos el serializador de Compra con un poco mas de cuidado, para poder serializar
en forma nesteada una compra; simplificando la creacion de estas.
'''


class CompraSerializer(serializers.ModelSerializer):
    purchased_objects = ObjetoPersonalizadoSerializer(many=True)
    payment_preferences = PaymentPreferencesSerializer(required=False, allow_null=True)
    delivery_address = DireccionDeEnvioSerializer()
    buyer = UsuarioSerializer(required=False, allow_null=True)

    class Meta:
        model = Compra
        fields = ('id','buyer','purchased_objects','date','status','payment_preferences','delivery_address')

    #DRF no soporta creacion de objetos nesteados out-of-the-box, de modo, que reemplazamos el metodo de creacion
    def create(self, validated_data):
        #Actualiamos los datos del comprador
        user = self.context['request'].user
        ## Actualizamos el User
        if 'buyer' in validated_data.keys():
            buyer_info = validated_data.pop('buyer')
            for key, value in buyer_info['user'].items():
                #Unicamente permitimos que cambien ciertos atributos de usuario
                if key in ['first_name', 'last_name', 'email'] and value is not None:
                    setattr(user, key, value)
            ## Actualizamos el Usuario
            telephone = buyer_info['telephone'] if 'telephone' in buyer_info.keys() else None
            if telephone is not None:
                user.usuario.telephone = telephone
                user.usuario.save()
            user.save()
        #Obtenemos DireccionDeEnvio a partir de delivery_address_char
        delivery_address_data = validated_data.pop('delivery_address')
        delivery_address, created = DireccionDeEnvio.objects.get_or_create(gmaps_id=delivery_address_data['gmaps_id'],  usuario=self.context['request'].user.usuario)
        notes = delivery_address_data['notes'] if 'notes' in delivery_address_data else None
        if created:
            delivery_address.notes = notes
        ## Actualizamos la ultima vez que se uso esta direccion
        else:
            delivery_address.last_time_used = datetime.datetime.now()
            if notes != None:
                delivery_address.notes = notes
        delivery_address.save()
        #Cargamos los objetos comprados
        purchased_objects_data = validated_data.pop('purchased_objects')
        compra = Compra.objects.create(delivery_address=delivery_address, **validated_data)
        for purchased_object_data in purchased_objects_data:
            ObjetoPersonalizado.objects.create(purchase=compra, **purchased_object_data)
        return compra