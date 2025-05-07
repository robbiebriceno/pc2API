from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import datetime
from .models import Profesor, Curso, Estudiante, Inscripcion, Calificacion, Asistencia
from .serializers import (
    ProfesorSerializer, 
    CursoSerializer,
    CursoDetalleSerializer,
    EstudianteSerializer,
    EstudianteDetalleSerializer,
    InscripcionSerializer,
    InscripcionDetalleSerializer,
    CalificacionSerializer,
    CalificacionDetalleSerializer,
    AsistenciaSerializer,
    AsistenciaDetalleSerializer,
    HorarioEstudianteSerializer,
    ListaAsistenciaSerializer,
)

class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'apellido', 'email', 'especialidad']
    ordering_fields = ['apellido', 'nombre', 'fecha_contratacion']

    @action(detail=True, methods=['get'])
    def cursos(self, request, pk=None):
        profesor = self.get_object()
        cursos = Curso.objects.filter(profesor=profesor)
        serializer = CursoSerializer(cursos, many=True)
        return Response(serializer.data)

class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['codigo', 'nombre', 'descripcion', 'profesor__nombre', 'profesor__apellido']
    ordering_fields = ['codigo', 'nombre', 'creditos', 'fecha_inicio', 'fecha_fin']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CursoDetalleSerializer
        return CursoSerializer

    @action(detail=True, methods=['get'])
    def estudiantes(self, request, pk=None):
        curso = self.get_object()
        inscripciones = Inscripcion.objects.filter(curso=curso, estado='ACTIVO')
        estudiantes = [inscripcion.estudiante for inscripcion in inscripciones]
        serializer = EstudianteSerializer(estudiantes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def lista_asistencia(self, request, pk=None):
        curso = self.get_object()
        fecha_str = request.query_params.get('fecha', None)
        
        try:
            if fecha_str:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            else:
                fecha = datetime.now().date()
        except ValueError:
            return Response(
                {"error": "Formato de fecha inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        inscripciones = Inscripcion.objects.filter(curso=curso, estado='ACTIVO')
        
        # Verificar asistencias existentes para esa fecha
        for inscripcion in inscripciones:
            Asistencia.objects.get_or_create(
                inscripcion=inscripcion,
                fecha=fecha,
                defaults={'presente': False}
            )
            
        # Obtener asistencias actualizadas
        asistencias = Asistencia.objects.filter(
            inscripcion__curso=curso,
            inscripcion__estado='ACTIVO',
            fecha=fecha
        )
        
        data = []
        for inscripcion in inscripciones:
            try:
                asistencia = asistencias.get(inscripcion=inscripcion)
                presente = asistencia.presente
            except Asistencia.DoesNotExist:
                presente = False
                
            data.append({
                'estudiante': inscripcion.estudiante,
                'presente': presente
            })
            
        serializer = ListaAsistenciaSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def registrar_asistencia(self, request, pk=None):
        curso = self.get_object()
        fecha_str = request.data.get('fecha', None)
        asistencias = request.data.get('asistencias', [])
        
        try:
            if fecha_str:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            else:
                fecha = datetime.now().date()
        except ValueError:
            return Response(
                {"error": "Formato de fecha inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        actualizados = 0
        errores = []
        
        for asistencia_data in asistencias:
            estudiante_id = asistencia_data.get('estudiante_id')
            presente = asistencia_data.get('presente', False)
            justificada = asistencia_data.get('justificada', False)
            observaciones = asistencia_data.get('observaciones', '')
            
            try:
                inscripcion = Inscripcion.objects.get(
                    estudiante_id=estudiante_id,
                    curso=curso,
                    estado='ACTIVO'
                )
                
                asistencia, created = Asistencia.objects.update_or_create(
                    inscripcion=inscripcion,
                    fecha=fecha,
                    defaults={
                        'presente': presente,
                        'justificada': justificada,
                        'observaciones': observaciones
                    }
                )
                actualizados += 1
                
            except Inscripcion.DoesNotExist:
                errores.append(f"El estudiante con ID {estudiante_id} no está inscrito en este curso")
        
        return Response({
            "actualizados": actualizados,
            "errores": errores
        })

class EstudianteViewSet(viewsets.ModelViewSet):
    queryset = Estudiante.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['matricula', 'nombre', 'apellido', 'email']
    ordering_fields = ['apellido', 'nombre', 'matricula', 'fecha_ingreso']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EstudianteDetalleSerializer
        return EstudianteSerializer

    @action(detail=True, methods=['get'])
    def cursos(self, request, pk=None):
        estudiante = self.get_object()
        inscripciones = Inscripcion.objects.filter(estudiante=estudiante, estado='ACTIVO')
        cursos = [inscripcion.curso for inscripcion in inscripciones]
        serializer = CursoSerializer(cursos, many=True)
        return Response(serializer.data)
        
    @action(detail=True, methods=['get'])
    def calificaciones(self, request, pk=None):
        estudiante = self.get_object()
        inscripciones = Inscripcion.objects.filter(estudiante=estudiante)
        data = []
        
        for inscripcion in inscripciones:
            try:
                calificacion = inscripcion.calificacion
                valor = calificacion.valor
            except Calificacion.DoesNotExist:
                valor = None
                
            data.append({
                'curso': {
                    'id': inscripcion.curso.id,
                    'codigo': inscripcion.curso.codigo,
                    'nombre': inscripcion.curso.nombre,
                },
                'estado': inscripcion.estado,
                'fecha_inscripcion': inscripcion.fecha_inscripcion,
                'calificacion': valor
            })
                
        return Response(data)
        
    @action(detail=True, methods=['get'])
    def horario(self, request, pk=None):
        estudiante = self.get_object()
        inscripciones = Inscripcion.objects.filter(
            estudiante=estudiante,
            estado='ACTIVO'
        )
        serializer = HorarioEstudianteSerializer(inscripciones, many=True)
        return Response(serializer.data)

class InscripcionViewSet(viewsets.ModelViewSet):
    queryset = Inscripcion.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'estudiante__nombre', 'estudiante__apellido', 'estudiante__matricula',
        'curso__codigo', 'curso__nombre'
    ]
    ordering_fields = ['fecha_inscripcion', 'estado']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InscripcionDetalleSerializer
        return InscripcionSerializer

    @action(detail=False, methods=['post'])
    def inscribir_estudiante(self, request):
        estudiante_id = request.data.get('estudiante_id')
        curso_id = request.data.get('curso_id')
        
        if not estudiante_id or not curso_id:
            return Response(
                {"error": "Se requieren estudiante_id y curso_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            estudiante = Estudiante.objects.get(id=estudiante_id)
            curso = Curso.objects.get(id=curso_id)
            
            # Verificar si ya está inscrito
            if Inscripcion.objects.filter(
                estudiante=estudiante,
                curso=curso,
                estado__in=['ACTIVO', 'COMPLETO']
            ).exists():
                return Response(
                    {"error": "El estudiante ya está inscrito en este curso"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verificar cupo disponible
            inscritos_activos = Inscripcion.objects.filter(
                curso=curso, 
                estado='ACTIVO'
            ).count()
            
            if inscritos_activos >= curso.cupo_maximo:
                return Response(
                    {"error": "El curso ha alcanzado su cupo máximo"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            inscripcion = Inscripcion.objects.create(
                estudiante=estudiante,
                curso=curso,
                estado='ACTIVO'
            )
            
            serializer = InscripcionDetalleSerializer(inscripcion)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Estudiante.DoesNotExist:
            return Response(
                {"error": "Estudiante no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Curso.DoesNotExist:
            return Response(
                {"error": "Curso no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def dar_baja(self, request, pk=None):
        inscripcion = self.get_object()
        
        if inscripcion.estado != 'ACTIVO':
            return Response(
                {"error": "La inscripción no está activa"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        inscripcion.estado = 'BAJA'
        inscripcion.save()
        
        serializer = InscripcionDetalleSerializer(inscripcion)
        return Response(serializer.data)

class CalificacionViewSet(viewsets.ModelViewSet):
    queryset = Calificacion.objects.all()
    serializer_class = CalificacionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'inscripcion__estudiante__nombre', 'inscripcion__estudiante__apellido',
        'inscripcion__curso__codigo', 'inscripcion__curso__nombre'
    ]
    ordering_fields = ['fecha_registro', 'valor']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CalificacionDetalleSerializer
        return CalificacionSerializer

    @action(detail=False, methods=['post'])
    def registrar_calificacion(self, request):
        inscripcion_id = request.data.get('inscripcion_id')
        valor = request.data.get('valor')
        observaciones = request.data.get('observaciones', '')
        
        if not inscripcion_id or valor is None:
            return Response(
                {"error": "Se requieren inscripcion_id y valor"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            inscripcion = Inscripcion.objects.get(id=inscripcion_id)
            
            # Verificar que la inscripción esté activa o completa
            if inscripcion.estado == 'BAJA':
                return Response(
                    {"error": "No se puede calificar una inscripción dada de baja"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            calificacion, created = Calificacion.objects.update_or_create(
                inscripcion=inscripcion,
                defaults={
                    'valor': valor,
                    'observaciones': observaciones
                }
            )
            
            # Si la inscripción estaba activa y es final de curso, marcarla como completa
            if inscripcion.estado == 'ACTIVO' and inscripcion.curso.fecha_fin <= datetime.now().date():
                inscripcion.estado = 'COMPLETO'
                inscripcion.save()
            
            serializer = CalificacionDetalleSerializer(calificacion)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Inscripcion.DoesNotExist:
            return Response(
                {"error": "Inscripción no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )

class AsistenciaViewSet(viewsets.ModelViewSet):
    queryset = Asistencia.objects.all()
    serializer_class = AsistenciaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'inscripcion__estudiante__nombre', 'inscripcion__estudiante__apellido',
        'inscripcion__curso__codigo', 'inscripcion__curso__nombre'
    ]
    ordering_fields = ['fecha', 'presente']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AsistenciaDetalleSerializer
        return AsistenciaSerializer

    @action(detail=False, methods=['get'])
    def por_curso(self, request):
        curso_id = request.query_params.get('curso_id')
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not curso_id:
            return Response(
                {"error": "Se requiere el parámetro curso_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            curso = Curso.objects.get(id=curso_id)
            queryset = Asistencia.objects.filter(inscripcion__curso=curso)
            
            if fecha_inicio:
                try:
                    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                    queryset = queryset.filter(fecha__gte=fecha_inicio)
                except ValueError:
                    return Response(
                        {"error": "Formato de fecha_inicio inválido. Use YYYY-MM-DD"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            if fecha_fin:
                try:
                    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                    queryset = queryset.filter(fecha__lte=fecha_fin)
                except ValueError:
                    return Response(
                        {"error": "Formato de fecha_fin inválido. Use YYYY-MM-DD"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            serializer = AsistenciaDetalleSerializer(queryset, many=True)
            return Response(serializer.data)
            
        except Curso.DoesNotExist:
            return Response(
                {"error": "Curso no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def por_estudiante(self, request):
        estudiante_id = request.query_params.get('estudiante_id')
        curso_id = request.query_params.get('curso_id')
        
        if not estudiante_id:
            return Response(
                {"error": "Se requiere el parámetro estudiante_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            estudiante = Estudiante.objects.get(id=estudiante_id)
            queryset = Asistencia.objects.filter(inscripcion__estudiante=estudiante)
            
            if curso_id:
                try:
                    curso = Curso.objects.get(id=curso_id)
                    queryset = queryset.filter(inscripcion__curso=curso)
                except Curso.DoesNotExist:
                    return Response(
                        {"error": "Curso no encontrado"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
            serializer = AsistenciaDetalleSerializer(queryset, many=True)
            return Response(serializer.data)
            
        except Estudiante.DoesNotExist:
            return Response(
                {"error": "Estudiante no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )