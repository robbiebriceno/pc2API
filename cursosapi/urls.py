from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfesorViewSet,
    CursoViewSet,
    EstudianteViewSet,
    InscripcionViewSet,
    CalificacionViewSet,
    AsistenciaViewSet,
)

router = DefaultRouter()
router.register(r'profesores', ProfesorViewSet)
router.register(r'cursos', CursoViewSet)
router.register(r'estudiantes', EstudianteViewSet)
router.register(r'inscripciones', InscripcionViewSet)
router.register(r'calificaciones', CalificacionViewSet)
router.register(r'asistencias', AsistenciaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]