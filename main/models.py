from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extension of the standard Django user.
    Django already has a User model with fields: username, password, email.
    We add additional information to it via a one-to-one relationship (OneToOneField).

    In simple terms: each User has exactly one UserProfile, 
    and it contains what is not in the standard User — company name and avatar.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # if User is deleted — delete the profile too
        related_name='profile'     # to allow writing user.profile
    )
    company_name = models.CharField(
        max_length=255,
        blank=True,      # can be left empty in the form
        default='',      # empty string by default
        verbose_name='Company Name'
    )
    avatar = models.ImageField(
        upload_to='avatars/',   # avatar files are saved to the media/avatars/ folder
        blank=True,
        null=True,
        verbose_name='Avatar'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # profile creation date

    def __str__(self):
        return f"{self.user.username} - {self.company_name or 'No Company'}"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class Dataset(models.Model):
    """
    Metadata of the uploaded file (Excel/CSV).
    
    We DO NOT store the file content in the DB — the file itself is on the disk.
    In the DB we only record: who uploaded it, when, what the file is named,
    and what state it is currently in (uploading / processing / error).

    In simple terms: this is a "catalog card" for each file.
    """
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # if User is deleted — delete their files too
        related_name='datasets'    # to allow: user.datasets.all()
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Dataset Name'
    )
    file = models.FileField(
        upload_to='datasets/',     # files are saved in media/datasets/
        verbose_name='File'
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name='Original Filename'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploading',
        verbose_name='Processing Status'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    rows_count = models.IntegerField(default=0, verbose_name='Rows Count')
    columns_count = models.IntegerField(default=0, verbose_name='Columns Count')

    def __str__(self):
        return f"{self.name} ({self.original_filename}) - {self.get_status_display()}"

    class Meta:
        verbose_name = 'Dataset'
        verbose_name_plural = 'Datasets'
        ordering = ['-uploaded_at']  # new files — on top


class ColumnMapping(models.Model):
    """
    Column mapping: the connection between the column name in the user's file
    and the standard internal name in our system.

    Example:
        user_column_name = "product"        (as the user calls it)
        standard_name    = "goods_name"   (as we call it in the system for analytics)

    Why this is needed: the auto-analyst must understand what is in the column.
    The user can name the column whatever they want, and we "map" it 
    to a standard name so that charts and formulas work the same for everyone.
    """
    STANDARD_COLUMNS = [
        ('goods_name', 'Product Name'),
        ('goods_category', 'Product Category'),
        ('quantity', 'Quantity'),
        ('price', 'Price'),
        ('total', 'Total / Revenue'),
        ('cost', 'Cost'),
        ('date', 'Date'),
        ('time', 'Time'),
        ('datetime', 'Date and Time'),
        ('supplier', 'Supplier'),
        ('customer', 'Customer / Buyer'),
        ('customer_group', 'Customer Group'),
        ('order_id', 'Order ID'),
        ('status', 'Status'),
        ('payment_method', 'Payment Method'),
        ('store', 'Store / Point of Sale'),
        ('city', 'City / Region'),
        ('manager', 'Manager / Employee'),
        ('discount', 'Discount'),
        ('promo', 'Promo / Campaign'),
        ('other', 'Other'),
    ]

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='column_mappings'
    )
    user_column_name = models.CharField(
        max_length=255,
        verbose_name='Column Name by User'
    )
    standard_name = models.CharField(
        max_length=50,
        choices=STANDARD_COLUMNS,
        default='other',
        verbose_name='Standard System Name'
    )

    def __str__(self):
        return f"{self.user_column_name} -> {self.get_standard_name_display()}"

    class Meta:
        verbose_name = 'Column Mapping'
        verbose_name_plural = 'Column Mappings'
        unique_together = ['dataset', 'user_column_name']  # one column — one mapping


class DashboardWidget(models.Model):
    """
    Widget on the user's dashboard.
    Stores: what type of visualization, which dataset it is tied to, position on the page.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_widgets')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='widgets')
    analytics_id = models.CharField(max_length=100, verbose_name='Analytics ID from Catalog')
    position = models.IntegerField(default=0, verbose_name='Position on Dashboard')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.analytics_id} - {self.dataset.name} (pos {self.position})"

    class Meta:
        verbose_name = 'Dashboard Widget'
        verbose_name_plural = 'Dashboard Widgets'
        ordering = ['position']


class Employee(models.Model):
    """
    Employee - account generated by the administrator.
    
    The administrator creates an employee for a specific dataset.
    The system generates a login and password. The employee logs in with these
    credentials and only sees the form for adding rows to the table,
    where form fields = column names of the administrator's dataset.
    
    owner - administrator who created this employee
    user - Django User account of the employee (for authorization)
    dataset - dataset to which the employee is attached
    display_name - readable name of the employee (e.g., "Manager Ivan")
    generated_password - password in plain text (to show the admin once)
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name='Administrator'
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name='Employee Account'
    )
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name='Attached Dataset'
    )
    display_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Employee Name'
    )
    generated_password = models.CharField(
        max_length=50,
        verbose_name='Generated Password'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.display_name or self.user.username} -> {self.dataset.name}"

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['-created_at']
