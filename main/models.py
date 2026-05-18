from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Расширение стандартного пользователя Django.
    Django уже имеет модель User с полями: username, password, email.
    Мы добавляем к ней доп. информацию через связь один-к-одному (OneToOneField).

    Простыми словами: у каждого User ровно один UserProfile, 
    и в нём лежит то, чего нет в стандартном User — название компании и аватарка.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # если User удалён — удаляем и профиль
        related_name='profile'     # чтобы можно было писать user.profile
    )
    company_name = models.CharField(
        max_length=255,
        blank=True,      # можно оставить пустым в форме
        default='',      # по умолчанию — пустая строка
        verbose_name='Название компании'
    )
    avatar = models.ImageField(
        upload_to='avatars/',   # файлы аватарок сохраняются в папку media/avatars/
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # дата создания профиля

    def __str__(self):
        return f"{self.user.username} — {self.company_name or 'Без компании'}"

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'


class Dataset(models.Model):
    """
    Метаданные загруженного файла (Excel/CSV).
    
    Мы НЕ храним содержимое файла в БД — сам файл лежит на диске.
    В БД мы записываем только: кто загрузил, когда, как называется файл,
    и в каком состоянии он сейчас (загружается / обработан / ошибка).

    Простыми словами: это "каталожная карточка" для каждого файла.
    """
    STATUS_CHOICES = [
        ('uploading', 'Загружается'),
        ('processing', 'Обрабатывается'),
        ('ready', 'Готов'),
        ('error', 'Ошибка'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # если User удалён — удаляем и его файлы
        related_name='datasets'    # чтобы можно было: user.datasets.all()
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Название датасета'
    )
    file = models.FileField(
        upload_to='datasets/',     # файлы сохраняются в media/datasets/
        verbose_name='Файл'
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name='Оригинальное имя файла'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploading',
        verbose_name='Статус обработки'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    rows_count = models.IntegerField(default=0, verbose_name='Количество строк')
    columns_count = models.IntegerField(default=0, verbose_name='Количество колонок')

    def __str__(self):
        return f"{self.name} ({self.original_filename}) — {self.get_status_display()}"

    class Meta:
        verbose_name = 'Датасет'
        verbose_name_plural = 'Датасеты'
        ordering = ['-uploaded_at']  # новые файлы — сверху


class ColumnMapping(models.Model):
    """
    Маппинг колонок: связь между названием колонки в файле пользователя
    и стандартным внутренним названием в нашей системе.

    Пример:
        user_column_name = "товар"        (как называет пользователь)
        standard_name    = "goods_name"   (как называем мы в системе для аналитики)

    Зачем это нужно: автоаналитик должен понимать, что в колонке лежит.
    Пользователь может назвать колонку как угодно, а мы "маппим" её 
    на стандартное имя, чтобы графики и формулы работали одинаково для всех.
    """
    STANDARD_COLUMNS = [
        ('goods_name', 'Название товара'),
        ('goods_category', 'Категория товара'),
        ('quantity', 'Количество'),
        ('price', 'Цена'),
        ('total', 'Сумма / Выручка'),
        ('cost', 'Себестоимость'),
        ('date', 'Дата'),
        ('time', 'Время'),
        ('datetime', 'Дата и Время'),
        ('supplier', 'Поставщик'),
        ('customer', 'Клиент / Покупатель'),
        ('customer_group', 'Группа клиентов'),
        ('order_id', 'Номер заказа'),
        ('status', 'Статус'),
        ('payment_method', 'Способ оплаты'),
        ('store', 'Магазин / Точка'),
        ('city', 'Город / Регион'),
        ('manager', 'Менеджер / Сотрудник'),
        ('discount', 'Скидка'),
        ('promo', 'Промокод / Акция'),
        ('other', 'Прочее'),
    ]

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='column_mappings'
    )
    user_column_name = models.CharField(
        max_length=255,
        verbose_name='Название колонки у пользователя'
    )
    standard_name = models.CharField(
        max_length=50,
        choices=STANDARD_COLUMNS,
        default='other',
        verbose_name='Стандартное название в системе'
    )

    def __str__(self):
        return f"{self.user_column_name} → {self.get_standard_name_display()}"

    class Meta:
        verbose_name = 'Маппинг колонки'
        verbose_name_plural = 'Маппинги колонок'
        unique_together = ['dataset', 'user_column_name']  # одна колонка — один маппинг


class DashboardWidget(models.Model):
    """
    Виджет на дашборде пользователя.
    Хранит: какой тип визуализации, к какому датасету привязан, позиция на странице.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_widgets')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='widgets')
    analytics_id = models.CharField(max_length=100, verbose_name='ID аналитики из каталога')
    position = models.IntegerField(default=0, verbose_name='Позиция на дашборде')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.analytics_id} — {self.dataset.name} (pos {self.position})"

    class Meta:
        verbose_name = 'Виджет дашборда'
        verbose_name_plural = 'Виджеты дашборда'
        ordering = ['position']
