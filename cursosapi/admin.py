from django.contrib import admin
from .models import Profesor, Curso, Estudiante, Inscripcion, Calificacion, Asistencia

@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'email', 'especialidad', 'activo')
    list_filter = ('activo', 'especialidad', 'fecha_contratacion')
    search_fields = ('nombre', 'apellido', 'email', 'especialidad')
    ordering = ('apellido', 'nombre')

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre', 'profesor', 'creditos', 'dias', 'activo')
    list_filter = ('activo', 'creditos', 'dias', 'profesor')
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('codigo',)

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('id', 'matricula', 'nombre', 'apellido', 'email', 'activo')
    list_filter = ('activo', 'fecha_ingreso')
    search_fields = ('matricula', 'nombre', 'apellido', 'email')
    ordering = ('apellido', 'nombre')

@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('id', 'estudiante', 'curso', 'fecha_inscripcion', 'estado')
    list_filter = ('estado', 'fecha_inscripcion')
    search_fields = ('estudiante__nombre', 'estudiante__apellido', 'curso__nombre', 'curso__codigo')
    ordering = ('-fecha_inscripcion',)

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_estudiante', 'get_curso', 'valor', 'fecha_registro')
    list_filter = ('fecha_registro',)
    search_fields = (
        'inscripcion__estudiante__nombre', 
        'inscripcion__estudiante__apellido', 
        'inscripcion__curso__nombre', 
        'inscripcion__curso__codigo'
    )
    ordering = ('-fecha_registro',)
    
    def get_estudiante(self, obj):
        return f"{obj.inscripcion.estudiante.apellido}, {obj.inscripcion.estudiante.nombre}"
    get_estudiante.short_description = 'Estudiante'
    
    def get_curso(self, obj):
        return f"{obj.inscripcion.curso.codigo} - {obj.inscripcion.curso.nombre}"
    get_curso.short_description = 'Curso'

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_estudiante', 'get_curso', 'fecha', 'presente', 'justificada')
    list_filter = ('fecha', 'presente', 'justificada')
    search_fields = (
        'inscripcion__estudiante__nombre', 
        'inscripcion__estudiante__apellido', 
        'inscripcion__curso__nombre', 
        'inscripcion__curso__codigo'
    )
    ordering = ('-fecha',)
    
    def get_estudiante(self, obj):
        return f"{obj.inscripcion.estudiante.apellido}, {obj.inscripcion.estudiante.nombre}"
    get_estudiante.short_description = 'Estudiante'
    
    def get_curso(self, obj):
        return f"{obj.inscripcion.curso.codigo} - {obj.inscripcion.curso.nombre}"
    get_curso.short_description = 'Curso'