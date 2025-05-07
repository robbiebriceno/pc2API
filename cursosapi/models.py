from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    especialidad = models.CharField(max_length=100)
    fecha_contratacion = models.DateField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Profesores"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

class Curso(models.Model):
    DIAS_CHOICES = (
        ('LUN', 'Lunes'),
        ('MAR', 'Martes'),
        ('MIE', 'Miércoles'),
        ('JUE', 'Jueves'),
        ('VIE', 'Viernes'),
        ('SAB', 'Sábado'),
        ('DOM', 'Domingo'),
    )
    
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    creditos = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    profesor = models.ForeignKey(
        Profesor, 
        related_name='cursos', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    cupo_maximo = models.PositiveSmallIntegerField(default=30)
    dias = models.CharField(max_length=3, choices=DIAS_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class Estudiante(models.Model):
    matricula = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    fecha_nacimiento = models.DateField()
    fecha_ingreso = models.DateField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.matricula} - {self.apellido}, {self.nombre}"

class Inscripcion(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, 
        related_name='inscripciones', 
        on_delete=models.CASCADE
    )
    curso = models.ForeignKey(
        Curso, 
        related_name='inscripciones', 
        on_delete=models.CASCADE
    )
    fecha_inscripcion = models.DateField(auto_now_add=True)
    estado = models.CharField(
        max_length=10, 
        choices=(
            ('ACTIVO', 'Activo'),
            ('BAJA', 'Baja'),
            ('COMPLETO', 'Completo'),
        ),
        default='ACTIVO'
    )

    class Meta:
        verbose_name_plural = "Inscripciones"
        unique_together = ['estudiante', 'curso']
        ordering = ['-fecha_inscripcion']

    def __str__(self):
        return f"{self.estudiante} - {self.curso}"

class Calificacion(models.Model):
    inscripcion = models.OneToOneField(
        Inscripcion, 
        related_name='calificacion', 
        on_delete=models.CASCADE
    )
    valor = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    fecha_registro = models.DateField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Calificaciones"

    def __str__(self):
        return f"{self.inscripcion.estudiante} - {self.inscripcion.curso}: {self.valor}"

class Asistencia(models.Model):
    inscripcion = models.ForeignKey(
        Inscripcion,
        related_name='asistencias',
        on_delete=models.CASCADE
    )
    fecha = models.DateField()
    presente = models.BooleanField(default=False)
    justificada = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Asistencias"
        unique_together = ['inscripcion', 'fecha']
        ordering = ['-fecha']

    def __str__(self):
        estado = "Presente" if self.presente else "Ausente"
        return f"{self.inscripcion.estudiante} - {self.fecha} - {estado}"