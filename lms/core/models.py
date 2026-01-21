from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# 1. ORGANIZATIONAL STRUCTURE

class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text='e.g. School of Engineering')
    location = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'departments'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return self.name


class Program(models.Model):
    prog_id = models.AutoField(primary_key=True)
    dept = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='programs'
    )
    name = models.CharField(max_length=255, help_text='e.g. BE Computer, B.Sc. Nursing')
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    duration_years = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = 'programs'
        verbose_name = 'Program'
        verbose_name_plural = 'Programs'

    def __str__(self):
        return f"{self.name} ({self.dept.name})"


# 2. STAFF & LEAD MANAGEMENT

class Staff(models.Model):
    ROLE_CHOICES = [
        ('counselor', 'Counselor'),
        ('admin', 'Admin'),
        ('finance', 'Finance'),
    ]

    staff_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, help_text='e.g. Counselor, Admin, Finance')

    class Meta:
        db_table = 'staff'
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff'

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class Lead(models.Model):
    SOURCE_CHOICES = [
        ('facebook', 'Facebook'),
        ('walkin', 'Walk-in'),
        ('referral', 'Referral'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted'),
        ('dropped', 'Dropped'),
    ]

    lead_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    address = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, help_text='Facebook, Walk-in, Referral')
    current_status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True,
        help_text='New, Qualified, Converted, Dropped'
    )
    assigned_staff = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads',
        help_text='Which counselor is handling this lead'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'leads'
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.current_status}"


class FollowUp(models.Model):
    MODE_CHOICES = [
        ('call', 'Call'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
    ]

    followup_id = models.AutoField(primary_key=True)
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='follow_ups'
    )
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name='follow_ups'
    )
    followup_date = models.DateTimeField()
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, help_text='Call, Email, WhatsApp')
    remarks = models.TextField(blank=True, null=True)
    next_action_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'follow_ups'
        verbose_name = 'Follow Up'
        verbose_name_plural = 'Follow Ups'
        ordering = ['-followup_date']

    def __str__(self):
        return f"Follow-up with {self.lead} on {self.followup_date.date()}"


# 3. APPLICATION & EXAMS

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('accepted', 'Accepted'),
    ]

    app_id = models.AutoField(primary_key=True)
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    app_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text='Pending, Reviewed, Accepted'
    )
    documents_url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = 'applications'
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'

    def __str__(self):
        return f"Application {self.app_id} - {self.lead} for {self.program}"


class EntranceExam(models.Model):
    TYPE_CHOICES = [
        ('online', 'Online'),
        ('physical', 'Physical'),
    ]

    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ]

    exam_id = models.AutoField(primary_key=True)
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='entrance_exam'
    )
    exam_date = models.DateTimeField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, help_text='Online, Physical')
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    result_status = models.CharField(max_length=20, choices=RESULT_CHOICES, help_text='Pass, Fail')

    class Meta:
        db_table = 'entrance_exams'
        verbose_name = 'Entrance Exam'
        verbose_name_plural = 'Entrance Exams'

    def __str__(self):
        return f"Exam {self.exam_id} - {self.application.lead} - {self.result_status}"


class Scholarship(models.Model):
    TYPE_CHOICES = [
        ('merit', 'Merit'),
        ('quota', 'Quota'),
        ('financial_aid', 'Financial Aid'),
    ]

    schol_id = models.AutoField(primary_key=True)
    exam = models.OneToOneField(
        EntranceExam,
        on_delete=models.CASCADE,
        related_name='scholarship',
        help_text='Linked to the entrance exam result'
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, help_text='Merit, Quota, Financial Aid')
    percentage_off = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_approved = models.BooleanField(default=False)

    class Meta:
        db_table = 'scholarships'
        verbose_name = 'Scholarship'
        verbose_name_plural = 'Scholarships'

    def __str__(self):
        return f"{self.type} - {self.percentage_off}% off (Approved: {self.is_approved})"


# 4. FINANCIALS

class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('application_fee', 'Application Fee'),
        ('admission_fee', 'Admission Fee'),
        ('semester_fee', 'Semester Fee'),
    ]

    METHOD_CHOICES = [
        ('esewa', 'E-Sewa'),
        ('khalti', 'Khalti'),
        ('bank_voucher', 'Bank Voucher'),
        ('connectips', 'ConnectIPS'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
    ]

    pay_id = models.AutoField(primary_key=True)
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text='Link to lead for contact info'
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text='Link to specific application'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_type = models.CharField(
        max_length=50,
        choices=PAYMENT_TYPE_CHOICES,
        help_text='Application Fee, Admission Fee, Semester Fee'
    )
    method = models.CharField(
        max_length=50,
        choices=METHOD_CHOICES,
        help_text='E-Sewa, Khalti, Bank Voucher, ConnectIPS'
    )
    transaction_ref_id = models.CharField(
        max_length=255,
        unique=True,
        help_text='Bank or wallet transaction ID'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text='Pending, Verified, Failed'
    )

    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment {self.pay_id} - {self.amount} - {self.status}"
