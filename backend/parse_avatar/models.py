"""
Модели для хранения данных о предметах Skyeng
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class SkyengSubject(models.Model):
    """
    Модель предмета (например, Физика, Математика, Английский)
    """
    SUBJECT_CHOICES = [
        ('career_guidance', 'Профориентация'),
        ('python', 'Python'),
        ('soft_skills', 'Soft Skills'),
        ('english', 'Английский'),
        ('math', 'Математика'),
        ('managment_of_project', 'Менеджмент проектов'),
        ('lessons_about_main', 'Курс Сингулярности'),
        ('onboarding', 'Онбординг'),
        ('biology', 'Биология'),
        ('history', 'История'),
        ('social_studies', 'Обществознание'),
        ('physics', 'Физика'),
        ('geography', 'География'),
        ('literature', 'Литература'),
        ('basics_of_security', 'Основы безопасности'),
        ('chemistry', 'Химия'),
        ('russian', 'Русский язык'),
    ]
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='skyeng_subjects',
        verbose_name='Пользователь'
    )
    subject_key = models.CharField(
        max_length=50,
        choices=SUBJECT_CHOICES,
        verbose_name='Ключ предмета'
    )
    subject_name = models.CharField(
        max_length=100,
        verbose_name='Название предмета'
    )
    api_version = models.CharField(
        max_length=10,
        choices=[('v1', 'API v1'), ('v2', 'API v2'), ('v3', 'API v3')],
        verbose_name='Версия API'
    )
    has_active_program = models.BooleanField(
        default=False,
        verbose_name='Есть активная программа'
    )
    last_parsed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Последний парсинг'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
        unique_together = ['user', 'subject_key']
        ordering = ['subject_name']

    def __str__(self):
        return f"{self.subject_name} ({self.get_subject_key_display()})"

    def is_outdated(self, hours=24):
        """Проверяет, устарели ли данные (старше 24 часов)"""
        return timezone.now() > self.last_parsed_at + timedelta(hours=hours)


class SkyengStream(models.Model):
    """
    Модель потока (группы студентов)
    """
    subject = models.ForeignKey(
        SkyengSubject,
        on_delete=models.CASCADE,
        related_name='streams',
        verbose_name='Предмет'
    )
    stream_id = models.IntegerField(
        verbose_name='ID потока',
        null=True,
        blank=True
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Название потока'
    )
    status = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Статус'
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата начала'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Поток'
        verbose_name_plural = 'Потоки'
        unique_together = ['subject', 'stream_id']

    def __str__(self):
        return f"{self.subject.subject_name}: {self.title}"


class SkyengProgram(models.Model):
    """
    Модель программы обучения
    """
    subject = models.ForeignKey(
        SkyengSubject,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name='Предмет'
    )
    program_id = models.IntegerField(
        verbose_name='ID программы'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Название программы'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Программа'
        verbose_name_plural = 'Программы'
        unique_together = ['subject', 'program_id']

    def __str__(self):
        return f"{self.subject.subject_name}: {self.title}"


class SkyengLesson(models.Model):
    """
    Модель урока/занятия
    """
    STATUS_CHOICES = [
        ('available', 'Доступен'),
        ('passed', 'Пройден'),
        ('locked', 'Заблокирован'),
        ('expired', 'Истёк'),
    ]
    
    TYPE_CHOICES = [
        ('self_study', 'Самостоятельная работа'),
        ('test', 'Тест'),
        ('homework', 'Домашняя работа'),
        ('lesson', 'Урок'),
    ]
    
    subject = models.ForeignKey(
        SkyengSubject,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Предмет'
    )
    lesson_id = models.IntegerField(
        verbose_name='ID урока'
    )
    task_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID задания'
    )
    title = models.CharField(
        max_length=300,
        verbose_name='Название урока'
    )
    lesson_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='Тип урока'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name='Статус'
    )
    score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Оценка'
    )
    available_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Доступен с'
    )
    deadline_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дедлайн'
    )
    homework_url = models.URLField(
        blank=True,
        verbose_name='Ссылка на ДЗ'
    )
    lesson_url = models.URLField(
        blank=True,
        verbose_name='Ссылка на урок'
    )
    teacher_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Преподаватель'
    )
    module_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Модуль'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        unique_together = ['subject', 'lesson_id']
        ordering = ['available_at']

    def __str__(self):
        return f"{self.subject.subject_name}: {self.title}"


class SkyengMetric(models.Model):
    """
    Модель метрик по предмету
    """
    subject = models.OneToOneField(
        SkyengSubject,
        on_delete=models.CASCADE,
        related_name='metrics',
        verbose_name='Предмет'
    )
    lessons_current = models.IntegerField(
        default=0,
        verbose_name='Пройдено уроков'
    )
    lessons_total = models.IntegerField(
        default=0,
        verbose_name='Всего уроков'
    )
    lessons_rating = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Рейтинг уроков'
    )
    homework_current = models.IntegerField(
        default=0,
        verbose_name='Сдано ДЗ'
    )
    homework_total = models.IntegerField(
        default=0,
        verbose_name='Всего ДЗ'
    )
    homework_rating = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Средний балл ДЗ'
    )
    tests_current = models.IntegerField(
        default=0,
        verbose_name='Пройдено тестов'
    )
    tests_total = models.IntegerField(
        default=0,
        verbose_name='Всего тестов'
    )
    tests_rating = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Средний балл тестов'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Метрика'
        verbose_name_plural = 'Метрики'

    def __str__(self):
        return f"Метрики: {self.subject.subject_name}"

    @property
    def progress_percentage(self):
        """Процент выполнения предмета"""
        if self.lessons_total == 0:
            return 0
        return round((self.lessons_current / self.lessons_total) * 100, 2)
