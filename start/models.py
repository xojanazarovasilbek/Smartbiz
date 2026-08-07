from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Category(models.Model):
    """Biznes turi: CRM (oquv markaz), POS (dokon), Klinika va h.k."""
    MODULE_CRM = "crm"
    MODULE_POS = "pos"
    MODULE_QUR = "qur"
    MODULE_BOGCHA = "bogcha"
    MODULE_TYPE_CHOICES = [
        (MODULE_CRM, "CRM (oquv markaz, klinika va h.k.)"),
        (MODULE_POS, "POS (dokon, market)"),
        (MODULE_QUR, "QUR (qurilish mollar dokoni)"),
        (MODULE_BOGCHA, "BOGCHA (bogcha, xususiy maktab)"),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    module_type = models.CharField(
        max_length=10, choices=MODULE_TYPE_CHOICES, default=MODULE_CRM,
        help_text="Qaysi tizim ishlatilishini belgilaydi: CRM yoki POS.",
    )
    is_available = models.BooleanField(
        default=False,
        help_text="Modul tayyor bolgach True qiling. False bolsa dashboardda blok holatda korinadi.",
    )

    def __str__(self):
        return self.name


class Tenant(models.Model):
    """Har bir mijoz (masalan 'Oquv markazi 1')."""
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="tenants")
    owner_phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """Tenant'ning tolov holati. 30 kunlik trial avtomatik beriladi."""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="subscription")
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    is_trial = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = timezone.now().date() + timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """Obuna faol va muddati tugamaganmi."""
        return self.is_active and self.end_date >= timezone.now().date()

    def __str__(self):
        holat = "faol" if self.is_valid else "tugagan"
        return f"{self.tenant.name} ({holat})"


class TenantUser(AbstractUser):
    """Har bir foydalanuvchi bitta tenant'ga bog'langan. Super admin esa bog'lanmaydi.
    settings.py da: AUTH_USER_MODEL = "start.TenantUser" qilib qoyish kerak."""
    ROLE_ADMIN = "admin"
    ROLE_KASSIR = "kassir"
    ROLE_OMBORCHI = "omborchi"
    ROLE_MENEJER = "menejer"
    ROLE_DIRECTOR = "director"
    ROLE_TARBIYACHI = "tarbiyachi"
    ROLE_OSHBAZ = "oshbaz"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_KASSIR, "Kassir"),
        (ROLE_OMBORCHI, "Omborchi"),
        (ROLE_MENEJER, "Menejer"),
        (ROLE_DIRECTOR, "Direktor"),
        (ROLE_TARBIYACHI, "Tarbiyachi"),
        (ROLE_OSHBAZ, "Oshpaz"),
    ]

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="users", null=True, blank=True
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_ADMIN)
    is_super_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Teacher(models.Model):
    """CRM: oquv markazi ustozi. Har biri bitta tenant'ga bogliq."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="teachers")
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=100, blank=True, help_text="Masalan: Ingliz tili, Matematika")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Group(models.Model):
    """CRM: oquv guruhi. Bitta ustozga va bir nechta oquvchiga ega boladi."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=200, help_text="Masalan: Ingliz tili (CEFR)")
    teacher = models.ForeignKey(
        Teacher, on_delete=models.SET_NULL, related_name="groups", null=True, blank=True
    )
    price = models.DecimalField(max_digits=12, decimal_places=0, default=0, help_text="Oylik kurs narxi")
    days = models.CharField(
        max_length=50, blank=True,
        help_text="Dars kunlari, vergul bilan: mon,wed,fri",
    )
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_days_list(self):
        return [d for d in self.days.split(",") if d]

    def __str__(self):
        return self.name


class Student(models.Model):
    """CRM: oquv markazi uchun oquvchilar. Har biri bitta tenant'ga bogliq."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="students")
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, related_name="students", null=True, blank=True
    )
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    note = models.TextField(blank=True)
    balance = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        help_text="Musbat - oldindan tolangan summa, manfiy - qarzdorlik.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Attendance(models.Model):
    """
    Davomat: har bir oquvchi uchun kuniga bitta yozuv.
    STATUS_CHOICES:
      present  - keldi
      absent   - sababsiz kelmadi
      excused  - sababli kelmadi (masalan kasal)
    Belgilangandan keyin faqat EDIT_WINDOW_HOURS soat ichida tahrirlash mumkin.
    """
    EDIT_WINDOW_HOURS = 1

    STATUS_CHOICES = [
        ("present", "Keldi"),
        ("absent", "Sababsiz kelmadi"),
        ("excused", "Sababli kelmadi"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="attendances")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="present")
    note = models.CharField(max_length=200, blank=True, help_text="Sababli kelmasa, sababi shu yerga")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ["student", "date"]
        ordering = ["-date"]

    def is_editable(self):
        return timezone.now() - self.created_at <= timedelta(hours=self.EDIT_WINDOW_HOURS)

    def __str__(self):
        return f"{self.student.full_name} - {self.date} ({self.get_status_display()})"


class Payment(models.Model):
    """
    Har bir oquvchi uchun oylik tolov yozuvi.
    month - qaysi oy uchunligini bildiradi (masalan 2026-07-01 = 2026-yil iyul).
    due_date - shu oy uchun qaysi kungacha tolash kerak.
    """
    PAYMENT_TYPE_CHOICES = [
        ("cash", "Naqd pul"),
        ("card", "Plastik karta"),
        ("click", "Click / Payme"),
        ("transfer", "Bank otkazma"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="payments")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="payments")
    month = models.DateField(help_text="Qaysi oy uchun - kunini 1 qilib kiriting, masalan 2026-07-01")
    due_date = models.DateField(help_text="Qaysi kungacha tolash kerak")
    amount = models.DecimalField(max_digits=12, decimal_places=0, blank=True, null=True)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES, default="cash")
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(blank=True, null=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ["student", "month"]
        ordering = ["-month"]

    @property
    def is_overdue(self):
        return not self.is_paid and self.due_date < timezone.now().date()

    def __str__(self):
        holat = "tolangan" if self.is_paid else "tolanmagan"
        return f"{self.student.full_name} - {self.month.strftime('%Y-%m')} ({holat})"


class Expense(models.Model):
    """Tenant xarajatlari - moliyaviy hisobot uchun."""
    EXPENSE_TYPE_CHOICES = [
        ("rent", "Ijara"),
        ("salary", "Oylik maosh"),
        ("utilities", "Kommunal"),
        ("supplies", "Materiallar"),
        ("other", "Boshqa"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="expenses")
    title = models.CharField(max_length=200)
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default="other")
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    date = models.DateField(default=timezone.now)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.date})"


# ---------- POS (dokon) modellari ----------

class ProductCategory(models.Model):
    """Mahsulot kategoriyasi (masalan Ichimliklar, Oziq-ovqat)."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="product_categories")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Product categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    """Mahsulot + Sklad (qoldiq) bitta modelda."""
    UNIT_PIECE = "dona"
    UNIT_KG = "kg"
    UNIT_CHOICES = [
        (UNIT_PIECE, "Dona"),
        (UNIT_KG, "Kg"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL, related_name="products", null=True, blank=True
    )
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=64, blank=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default=UNIT_PIECE)
    price = models.DecimalField(max_digits=12, decimal_places=0, help_text="Sotuv narxi")
    discount_price = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        help_text="Chegirmali narx (ixtiyoriy)",
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Joriy qoldiq")
    min_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=5, help_text="Bu qoldiqdan kam bolsa ogohlantirish chiqadi")
    is_active = models.BooleanField(
        default=True,
        help_text="Sotilgan mahsulotni ochirib bolmaydi, shu sabab nofaol qilib yashirish uchun.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_quantity

    def __str__(self):
        return self.name


class Sale(models.Model):
    """Bitta chek/sotuv - bir nechta mahsulotdan iborat boladi."""
    PAYMENT_CHOICES = [
        ("cash", "Naqd"),
        ("card", "Plastik karta"),
        ("click", "Click / Payme"),
    ]
    STATUS_CHOICES = [
        ("open", "Ochiq (savat)"),
        ("completed", "Yakunlangan"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="sales")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default="cash")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    total_amount = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    created_by = models.ForeignKey(
        "TenantUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_created",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sotuv #{self.id} - {self.total_amount}"


class SaleItem(models.Model):
    """Bitta chek ichidagi bitta mahsulot qatori."""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=0, help_text="Sotilgan paytdagi narx")

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class Purchase(models.Model):
    """Yetkazib beruvchidan mahsulot kirimi - sklad qoldigini oshiradi."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="purchases")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="purchases")
    supplier = models.CharField(max_length=200, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=0, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.product.name} +{self.quantity} ({self.date})"


# ---------- QUR (qurilish mollari) modellari ----------

class QurilishCategory(models.Model):
    """Mahsulot kategoriyasi (masalan Fasad materiallari, Asbob-uskunalar)."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="qurilish_categories")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Qurilish categories"

    def __str__(self):
        return self.name


class QurilishProduct(models.Model):
    """Mahsulot + Sklad (qoldiq) bitta modelda."""
    UNIT_PIECE = "dona"
    UNIT_KG = "kg"
    UNIT_METR = "metr"
    UNIT_LITR = "litr"
    UNIT_CHOICES = [
        (UNIT_PIECE, "Dona"),
        (UNIT_KG, "Kg"),
        (UNIT_METR, "Metr"),
        (UNIT_LITR, "Litr"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="qurilish_products")
    category = models.ForeignKey(
        QurilishCategory, on_delete=models.SET_NULL, related_name="products", null=True, blank=True
    )
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=64, blank=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default=UNIT_PIECE)
    price = models.DecimalField(max_digits=12, decimal_places=0, help_text="Sotuv narxi")
    discount_price = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        help_text="Chegirmali narx (ixtiyoriy)",
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Joriy qoldiq")
    min_quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=5,
        help_text="Bu qoldiqdan kam bolsa ogohlantirish chiqadi",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Sotilgan mahsulotni ochirib bolmaydi, shu sabab nofaol qilib yashirish uchun.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_quantity

    def __str__(self):
        return self.name


class QurilishSale(models.Model):
    """Bitta chek/sotuv - bir nechta mahsulotdan iborat boladi."""
    PAYMENT_CHOICES = [
        ("cash", "Naqd"),
        ("card", "Plastik karta"),
        ("click", "Click / Payme"),
    ]
    STATUS_CHOICES = [
        ("open", "Ochiq (savat)"),
        ("completed", "Yakunlangan"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="qurilish_sales")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default="cash")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    total_amount = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    created_by = models.ForeignKey(
        "TenantUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="qurilish_sales_created",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sotuv #{self.id} - {self.total_amount}"


class QurilishSaleItem(models.Model):
    """Bitta chek ichidagi bitta mahsulot qatori."""
    sale = models.ForeignKey(QurilishSale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(QurilishProduct, on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=0, help_text="Sotilgan paytdagi narx")

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class QurilishPurchase(models.Model):
    """Yetkazib beruvchidan mahsulot kirimi - sklad qoldigini oshiradi."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="qurilish_purchases")
    product = models.ForeignKey(QurilishProduct, on_delete=models.CASCADE, related_name="purchases")
    supplier = models.CharField(max_length=200, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=0, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.product.name} +{self.quantity} ({self.date})"


# ---------- BOGCHA modellari ----------

class BogchaGroup(models.Model):
    """Bogcha uchun alohida guruh (sinf) modeli - CRM Group bilan aralashmaydi."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="bogcha_groups")
    name = models.CharField(max_length=200, help_text="Masalan: Kichik guruh, Orta guruh")
    tarbiyachi = models.ForeignKey(
        Teacher, on_delete=models.SET_NULL, related_name="bogcha_groups", null=True, blank=True,
    )
    min_age = models.PositiveIntegerField(default=0, help_text="Guruhga mos minimal yosh (yilda)")
    max_age = models.PositiveIntegerField(default=7, help_text="Guruhga mos maksimal yosh (yilda)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["min_age"]

    def __str__(self):
        return self.name


class Child(models.Model):
    """Bogcha/xususiy maktab uchun bola karta yozuvi."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="children")
    group = models.ForeignKey(
        BogchaGroup, on_delete=models.SET_NULL, related_name="children", null=True, blank=True,
        help_text="Tugilgan sanaga qarab avtomatik tanlanadi, kerak bolsa qolda ozgartirish mumkin",
    )
    full_name = models.CharField(max_length=200)
    photo = models.ImageField(upload_to="children/", blank=True, null=True)
    id_document = models.CharField(max_length=50, blank=True, help_text="Guvohnoma / ID / pasport raqami")
    birth_date = models.DateField()

    father_name = models.CharField(max_length=200, blank=True)
    father_id = models.CharField(max_length=50, blank=True, help_text="Otaning ID/pasport raqami")
    mother_name = models.CharField(max_length=200, blank=True)
    mother_id = models.CharField(max_length=50, blank=True, help_text="Onaning ID/pasport raqami")
    phone = models.CharField(max_length=20, blank=True, help_text="Asosiy aloqa raqami")

    health_condition = models.TextField(blank=True, help_text="Allergiya, surunkali kasallik va h.k.")
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def age_years(self):
        today = timezone.now().date()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years

    def __str__(self):
        return self.full_name


class AuthorizedPickup(models.Model):
    """Bolani olib ketishga ruxsat berilgan shaxslar royxati."""
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="authorized_pickups")
    full_name = models.CharField(max_length=200)
    relation = models.CharField(max_length=100, blank=True, help_text="Masalan: buvi, tog'a")
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.child.full_name})"


class ChildDailyLog(models.Model):
    """
    Tarbiyachi tomonidan kuniga bir marta toldiriladigan yozuv:
    kelgan vaqti va sogligi haqida izoh. Bir marta saqlangach
    HECH QACHON ozgartirib bolmaydi (view darajasida taqiqlanadi).
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="child_daily_logs")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="daily_logs")
    date = models.DateField(default=timezone.now)
    arrival_time = models.TimeField()
    health_note = models.TextField(help_text="Majburiy: bolaning sogligi haqida qisqa izoh")
    recorded_by = models.ForeignKey(
        "TenantUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="daily_logs_recorded",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["child", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.child.full_name} - {self.date}"


class MealServing(models.Model):
    """Tarbiyachi 'qabul qildim' deb belgilaydigan ovqatlantirish yozuvi."""
    MEAL_CHOICES = [
        ("breakfast", "Nonushta"),
        ("lunch", "Tushlik"),
        ("snack", "Poldnik"),
        ("dinner", "Kechki ovqat"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="meal_servings")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="meal_servings")
    date = models.DateField(default=timezone.now)
    meal_type = models.CharField(max_length=10, choices=MEAL_CHOICES)
    served = models.BooleanField(default=True)
    served_by = models.ForeignKey(
        "TenantUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="meals_served",
    )
    served_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["child", "date", "meal_type"]

    def __str__(self):
        return f"{self.child.full_name} - {self.get_meal_type_display()} ({self.date})"


class MealLog(models.Model):
    """Oshpaz hisoboti: shu kun uchun necha porsiya ovqat tayyorlangani."""
    MEAL_CHOICES = MealServing.MEAL_CHOICES

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="meal_logs")
    date = models.DateField(default=timezone.now)
    meal_type = models.CharField(max_length=10, choices=MEAL_CHOICES)
    portions_count = models.PositiveIntegerField()
    note = models.CharField(max_length=200, blank=True)
    recorded_by = models.ForeignKey(
        "TenantUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="meal_logs_recorded",
    )
    confirmed = models.BooleanField(default=False, help_text="Tarbiyachi ovqatni qabul qilganini tasdiqladimi")
    confirmed_by = models.ForeignKey(
        "TenantUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="meal_logs_confirmed",
    )
    confirmed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ["tenant", "date", "meal_type"]

    def __str__(self):
        return f"{self.date} - {self.get_meal_type_display()} ({self.portions_count} porsiya)"


class PickupLog(models.Model):
    """Bola ketayotganda kim olib ketayotgani haqida yozuv."""
    RELATION_CHOICES = [
        ("father", "Ota"),
        ("mother", "Ona"),
        ("other", "Boshqa"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="pickup_logs")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="pickup_logs")
    date = models.DateField(default=timezone.now)
    picked_up_by_name = models.CharField(max_length=200)
    relation = models.CharField(max_length=10, choices=RELATION_CHOICES, default="other")
    time = models.TimeField(default=timezone.now)
    recorded_by = models.ForeignKey(
        "TenantUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="pickups_recorded",
    )

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.child.full_name} - {self.picked_up_by_name} ({self.date})"




class AuditLog(models.Model):
    """Muhim amallar tarixi - kim, qachon, nima qildi."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="audit_logs")
    user = models.ForeignKey("TenantUser", on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=200, help_text="Masalan: 'Mahsulot ochirdi', 'Tolovni belgiladi'")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.action} ({self.created_at})"