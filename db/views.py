from db.serializers import ObjetoSerializer, ObjetoThingiSerializer, TagSerializer, CategoriaSerializer, UserSerializer
from db.models import Objeto, Tag, Categoria
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.http import Http404
from .tools import import_from_thingi
import json
import traceback


'''
Query view
'''

class CategoryView(generics.ListAPIView):
    serializer_class = ObjetoSerializer
    lookup_url_kwarg = 'category'

    def get_queryset(self):
        category = self.kwargs.get(self.lookup_url_kwarg)
        objetos = Objeto.objects.filter(category__name=category)
        return objetos

class TagView(generics.ListAPIView):
    serializer_class = ObjetoSerializer
    lookup_url_kwarg = 'tags'

    def get_queryset(self):
        tags = self.kwargs.get(self.lookup_url_kwarg).split(',')
        objetos = Objeto.objects.all()
        for tag in tags:
            objetos = objetos.filter(tags__name=tag)
        return objetos

class ObjectView(generics.RetrieveAPIView):
    serializer_class = ObjetoSerializer
    lookup_url_kwarg = 'id'

    def get_object(self):
        id = self.kwargs.get(self.lookup_url_kwarg)
        objeto = Objeto.objects.get(id=id)
        return objeto

class NameView(generics.ListAPIView):
    serializer_class = ObjetoSerializer
    lookup_url_kwarg = 'name'

    def get_queryset(self):
        name = self.kwargs.get(self.lookup_url_kwarg)
        objetos = Objeto.objects.filter(name__contains=name)
        return objetos

'''
List views
'''

class ListAllObjectsView(generics.ListAPIView):
    serializer_class = ObjetoSerializer
    def get_queryset(self):
        return Objeto.objects.all()

class ListAllCategoriesView(generics.ListAPIView):
    serializer_class = CategoriaSerializer

    def get_queryset(self):
        return Categoria.objects.all()

class ListAllTagsView(generics.ListAPIView):
    serializer_class = TagSerializer

    def get_queryset(self):
        return Tag.objects.all()

'''
Operations view
'''

class ObjectView(generics.RetrieveAPIView):
    serializer_class = ObjetoSerializer
    lookup_url_kwarg = 'id'

    def get_object(self):
        id = self.kwargs.get(self.lookup_url_kwarg)
        try:
            objeto = Objeto.objects.get(id=id)
        except Objeto.DoesNotExist:
             raise Http404
        return objeto

class ToggleLike(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    lookup_url_kwarg = 'id'

    def get_object(self):
        id = self.kwargs.get(self.lookup_url_kwarg)
        try:
            objeto = Objeto.objects.get(id=id)
        except Objeto.DoesNotExist:
             raise Http404
        return objeto

    def update(self, request, *args, **kwargs):
        objeto = self.get_object()
        id = self.kwargs.get(self.lookup_url_kwarg)
        user = request.user
        if user.usuario.liked_objects.filter(pk=id).exists():
            user.usuario.liked_objects.remove(objeto)
        else:
            user.usuario.liked_objects.add(objeto)
        serializer = ObjetoSerializer(objeto,context={'request': request})
        print(serializer)
        return Response(serializer.data)

'''
DB Operations view
'''

class AddObjectFromThingiverse(APIView):
    permission_classes = (IsAdminUser,)
    #Agregar objeto desde id y lista de archivos
    def post(self, request, format=None):
        serializer = ObjetoThingiSerializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            #Ejecutamos la importacion
            try:
                job = import_from_thingi.add_object_from_thingiverse(obj.external_id,obj.file_list)
                obj.status = 'finished'
            except:
                traceback.print_exc()
                obj.status = 'error'
            obj.save()
            return Response(ObjetoThingiSerializer(obj).data)
        return Response(serializer.errors)


'''
class UserTest(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
'''
