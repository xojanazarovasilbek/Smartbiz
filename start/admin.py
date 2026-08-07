from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Category, Tenant, Subscription, TenantUser, Teacher, Group, Student,
    Attendance, Payment, Expense, ProductCategory, Product, Sale, SaleItem, Purchase,
    QurilishCategory, QurilishProduct, QurilishSale, QurilishSaleItem, QurilishPurchase,
    BogchaGroup, Child, AuthorizedPickup, ChildDailyLog, MealServing, MealLog, PickupLog,
)


def _tenant_scoped_queryset(request, qs):
    """Oddiy xodim faqat oz tenant'iga tegishli yozuvlarni korsin."""
    user = request.user
    if user.is_superuser or getattr(user, "is_super_admin", False):
        return qs
    return qs.filter(tenant_id=getattr(user, "tenant_id", None))


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "module_type", "is_available"]
    prepopulated_fields = {"slug": ("name",)}


class SubscriptionInline(admin.StackedInline):
    """Tenant sahifasida obuna maydonlarini birga tahrirlash uchun."""
    model = Subscription
    extra = 0


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "created_at"]
    list_filter = ["category"]
    inlines = [SubscriptionInline]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["tenant", "start_date", "end_date", "is_trial", "is_active"]
    list_filter = ["is_trial", "is_active"]


@admin.register(TenantUser)
class TenantUserAdmin(UserAdmin):
    """Standart Django UserAdmin ustiga tenant, rol va super admin maydonlarini qoshadi."""
    list_display = ["username", "tenant", "role", "is_super_admin", "is_active"]
    fieldsets = UserAdmin.fieldsets + (
        ("Tenant sozlamalari", {"fields": ("tenant", "role", "is_super_admin")}),
    )


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ["full_name", "tenant", "subject", "phone"]
    list_filter = ["tenant"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "teacher", "created_at"]
    list_filter = ["tenant"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["full_name", "tenant", "group", "phone", "created_at"]
    list_filter = ["tenant", "group"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["student", "tenant", "date", "status", "note"]
    list_filter = ["tenant", "status", "date"]
    date_hierarchy = "date"

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["student", "tenant", "month", "due_date", "amount", "is_paid"]
    list_filter = ["tenant", "is_paid", "month"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["title", "tenant", "expense_type", "amount", "date"]
    list_filter = ["tenant", "expense_type"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant"]
    list_filter = ["tenant"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "category", "unit", "price", "quantity", "min_quantity"]
    list_filter = ["tenant", "category"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ["id", "tenant", "payment_method", "total_amount", "created_at"]
    list_filter = ["tenant", "payment_method"]
    inlines = [SaleItemInline]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ["product", "tenant", "supplier", "quantity", "date"]
    list_filter = ["tenant"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(QurilishCategory)
class QurilishCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant"]
    list_filter = ["tenant"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(QurilishProduct)
class QurilishProductAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "category", "unit", "price", "quantity", "min_quantity"]
    list_filter = ["tenant", "category"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


class QurilishSaleItemInline(admin.TabularInline):
    model = QurilishSaleItem
    extra = 0


@admin.register(QurilishSale)
class QurilishSaleAdmin(admin.ModelAdmin):
    list_display = ["id", "tenant", "payment_method", "total_amount", "created_at"]
    list_filter = ["tenant", "payment_method"]
    inlines = [QurilishSaleItemInline]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(QurilishPurchase)
class QurilishPurchaseAdmin(admin.ModelAdmin):
    list_display = ["product", "tenant", "supplier", "quantity", "date"]
    list_filter = ["tenant"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


class AuthorizedPickupInline(admin.TabularInline):
    model = AuthorizedPickup
    extra = 0


@admin.register(BogchaGroup)
class BogchaGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "tarbiyachi", "min_age", "max_age"]
    list_filter = ["tenant"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ["full_name", "tenant", "group", "birth_date", "age_years"]
    list_filter = ["tenant", "group"]
    inlines = [AuthorizedPickupInline]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(ChildDailyLog)
class ChildDailyLogAdmin(admin.ModelAdmin):
    list_display = ["child", "tenant", "date", "arrival_time"]
    list_filter = ["tenant", "date"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(MealServing)
class MealServingAdmin(admin.ModelAdmin):
    list_display = ["child", "tenant", "date", "meal_type", "served"]
    list_filter = ["tenant", "date", "meal_type"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(MealLog)
class MealLogAdmin(admin.ModelAdmin):
    list_display = ["date", "tenant", "meal_type", "portions_count"]
    list_filter = ["tenant", "date"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))


@admin.register(PickupLog)
class PickupLogAdmin(admin.ModelAdmin):
    list_display = ["child", "tenant", "date", "picked_up_by_name", "relation"]
    list_filter = ["tenant", "date"]

    def get_queryset(self, request):
        return _tenant_scoped_queryset(request, super().get_queryset(request))