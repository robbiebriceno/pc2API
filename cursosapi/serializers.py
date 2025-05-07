from rest_framework import serializers
from .models import Profesor, Curso, Estudiante, Inscripcion, Calificacion, Asistencia
from django.db.models import Q

class ProfesorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profesor
        fields = '__all__'

class CursoSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Curso
        fields = '__all__'
    
    def get_profesor_nombre(self, obj):
        if obj.profesor:
            return f"{obj.profesor.nombre} {obj.profesor.apellido}"
        return None

class CursoDetalleSerializer(CursoSerializer):
    estudiantes_inscritos = serializers.SerializerMethodField()
    
    class Meta(CursoSerializer.Meta):
        fields = CursoSerializer.Meta.fields + ('estudiantes_inscritos',)
    
    def get_estudiantes_inscritos(self, obj):
        return obj.inscripciones.filter(estado='ACTIVO').count()

class EstudianteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estudiante
        fields = '__all__'

class EstudianteDetalleSerializer(EstudianteSerializer):
    cursos_inscritos = serializers.SerializerMethodField()
    
    class Meta(EstudianteSerializer.Meta):
        fields = EstudianteSerializer.Meta.fields + ('cursos_inscritos',)
    
    def get_cursos_inscritos(self, obj):
        cursos = []
        inscripciones = obj.inscripciones.filter(estado='ACTIVO')
        for inscripcion in inscripciones:
            cursos.append({
                'id': inscripcion.curso.id,
                'codigo': inscripcion.curso.codigo,
                'nombre': inscripcion.curso.nombre,
                'profesor': inscripcion.curso.profesor.nombre if inscripcion.curso.profesor else None
            })
        return cursos

class InscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscripcion
        fields = '__all__'

    def validate(self, data):
        # Verificar si el estudiante ya está inscrito en este curso
        if Inscripcion.objects.filter(
            Q(estudiante=data['estudiante']) & 
            Q(curso=data['curso']) & 
            ~Q(estado='BAJA')
        ).exists():
            raise serializers.ValidationError("El estudiante ya está inscrito en este curso.")
        
        # Verificar si hay cupo disponible
        curso = data['curso']
        inscritos_activos = Inscripcion.objects.filter(
            curso=curso, 
            estado='ACTIVO'
        ).count()
        
        if inscritos_activos >= curso.cupo_maximo:
            raise serializers.ValidationError("El curso ha alcanzado su cupo máximo.")
        
        return data

class InscripcionDetalleSerializer(InscripcionSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    curso_nombre = serializers.SerializerMethodField()
    calificacion_valor = serializers.SerializerMethodField()
    
    class Meta(InscripcionSerializer.Meta):
        fields = InscripcionSerializer.Meta.fields + ('estudiante_nombre', 'curso_nombre', 'calificacion_valor')
    
    def get_estudiante_nombre(self, obj):
        return f"{obj.estudiante.nombre} {obj.estudiante.apellido}"
    
    def get_curso_nombre(self, obj):
        return f"{obj.curso.codigo} - {obj.curso.nombre}"
    
    def get_calificacion_valor(self, obj):
        try:
            return obj.calificacion.valor
        except Calificacion.DoesNotExist:
            return None

class CalificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calificacion
        fields = '__all__'

class CalificacionDetalleSerializer(CalificacionSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    curso_nombre = serializers.SerializerMethodField()
    
    class Meta(CalificacionSerializer.Meta):
        fields = CalificacionSerializer.Meta.fields + ('estudiante_nombre', 'curso_nombre')
    
    def get_estudiante_nombre(self, obj):
        return f"{obj.inscripcion.estudiante.nombre} {obj.inscripcion.estudiante.apellido}"
    
    def get_curso_nombre(self, obj):
        return f"{obj.inscripcion.curso.codigo} - {obj.inscripcion.curso.nombre}"

class AsistenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asistencia
        fields = '__all__'

class AsistenciaDetalleSerializer(AsistenciaSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    curso_nombre = serializers.SerializerMethodField()
    
    class Meta(AsistenciaSerializer.Meta):
        fields = AsistenciaSerializer.Meta.fields + ('estudiante_nombre', 'curso_nombre')
    
    def get_estudiante_nombre(self, obj):
        return f"{obj.inscripcion.estudiante.nombre} {obj.inscripcion.estudiante.apellido}"
    
    def get_curso_nombre(self, obj):
        return f"{obj.inscripcion.curso.codigo} - {obj.inscripcion.curso.nombre}"

class HorarioEstudianteSerializer(serializers.Serializer):
    dia = serializers.CharField(source='curso.get_dias_display')
    hora_inicio = serializers.TimeField(source='curso.hora_inicio')
    hora_fin = serializers.TimeField(source='curso.hora_fin')
    curso = serializers.CharField(source='curso.nombre')
    codigo = serializers.CharField(source='curso.codigo')
    profesor = serializers.SerializerMethodField()
    
    def get_profesor(self, obj):
        if obj.curso.profesor:
            return f"{obj.curso.profesor.nombre} {obj.curso.profesor.apellido}"
        return None

class ListaAsistenciaSerializer(serializers.Serializer):
    estudiante_id = serializers.IntegerField(source='estudiante.id')
    matricula = serializers.CharField(source='estudiante.matricula')
    nombre = serializers.SerializerMethodField()
    presente = serializers.BooleanField(required=False, default=False)
    
    def get_nombre(self, obj):
        return f"{obj.estudiante.apellido}, {obj.estudiante.nombre}"