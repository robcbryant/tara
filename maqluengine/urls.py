"""urlconf for the maqlu-engine application"""


from django.urls import path
from . import views

app_name = "maqluengine"
urlpatterns = [
    path('', views.index, name='index'),
]
