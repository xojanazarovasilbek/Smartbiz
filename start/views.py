from decimal import Decimal, InvalidOperation
from .forms import GugurtImportForm, GugurtDealerForm, GugurtDistributionForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    Attendance, Category, Expense, Group, Payment, Product, ProductCategory,
    Purchase, Sale, SaleItem, Student, Teacher, Tenant, TenantUser,
    QurilishCategory, QurilishProduct, QurilishSale, QurilishSaleItem, QurilishPurchase,
    BogchaGroup, Child, AuthorizedPickup, ChildDailyLog, MealServing, MealLog, PickupLog,
    GugurtProduct,
    GugurtImportBatch,
    GugurtRegion,
    GugurtDealer,
    GugurtDistribution,
)




@login_required
def custom_dashboard(request):
    """
    /dashboard12/ orqali kiriladigan asosiy dashboard.

    Tenant avtomatik aniqlanadi.
    'main' kabi eski default slug ishlatilmaydi.
    """

    user = request.user

    # Super Admin bo'lsa:
    # bazadagi mavjud tenantlardan birinchisini olamiz.
    if _is_super_admin(user):
        tenant = Tenant.objects.select_related("category").first()
    else:
        # Oddiy foydalanuvchi faqat o'z tenantiga kiradi
        if not user.tenant_id:
            raise PermissionDenied(
                "Sizga hech qanday tashkilot biriktirilmagan."
            )

        tenant = get_object_or_404(
            Tenant.objects.select_related("category"),
            id=user.tenant_id
        )

    # Umuman tenant bo'lmasa
    if not tenant:
        return redirect("dashboard_categories")

    # Statistikalar
    total_students = Student.objects.filter(
        tenant=tenant
    ).count()

    total_teachers = Teacher.objects.filter(
        tenant=tenant
    ).count()

    total_groups = Group.objects.filter(
        tenant=tenant
    ).count()

    total_children = Child.objects.filter(
        tenant=tenant
    ).count()

    recent_students = Student.objects.filter(
        tenant=tenant
    ).order_by("-id")[:5]

    # Super Admin barcha tashkilotlarni ko'rsin
    if _is_super_admin(user):
        managed_tenants = Tenant.objects.select_related(
            "category"
        ).all()
    else:
        managed_tenants = Tenant.objects.filter(
            id=tenant.id
        ).select_related("category")

    context = {
        "user_name": user.first_name or user.username,

        "is_super_admin": _is_super_admin(user),

        # MUHIM:
        # haqiqiy tenant ma'lumotlari
        "tenant": tenant,
        "slug": tenant.category.slug,
        "tenant_id": tenant.id,

        # Statistikalar
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_groups": total_groups,
        "total_children": total_children,
        "recent_students": recent_students,

        # Tashkilotlar
        "managed_tenants": managed_tenants,
    }

    return render(
        request,
        "dashboard/index.html",
        context
    )





from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Tenant

# 1. Barcha Tenantlar (Tashkilotlar) ro'yxati
@login_required
def tenant_list(request, slug='main', tenant_id=1):
    tenants = Tenant.objects.all()
    context = {
        'tenants': tenants,
        'slug': slug,
        'tenant_id': tenant_id,
        'user_name': request.user.first_name or request.user.username,
    }
    return render(request, 'dashboard/tenant_list.html', context)


# 2. Yangi Tenant (Tashkilot) qo'shish
@login_required
def tenant_create(request, slug='main', tenant_id=1):
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category_id')

        # Agar kategoriya tanlanmagan bo'lsa, birinchi kategoriyani yoki mavjud bo'lmasa yangisini oladi
        if not category_id:
            category = Category.objects.first()
            if not category:
                category = Category.objects.create(name="Asosiy", slug="main")
            category_id = category.id

        if name:
            Tenant.objects.create(
                name=name,
                category_id=category_id
            )
            return redirect('tenant_list', slug=slug, tenant_id=tenant_id)

    context = {
        'categories': categories,
        'slug': slug,
        'tenant_id': tenant_id,
        'user_name': request.user.first_name or request.user.username,
    }
    return render(request, 'dashboard/tenant_create.html', context)






















def _is_super_admin(user):
    return user.is_superuser or getattr(user, "is_super_admin", False)



def home(request):
    return render(request, "reklama/reklama.html")


def _has_role(user, *allowed_roles):
    """
    Super admin va Admin roli hamma narsaga kira oladi.
    Boshqa rollar (Kassir, Omborchi, Menejer) faqat royxatda kelgan
    ruxsatlarga ega bolib qoladi.
    """
    if _is_super_admin(user):
        return True
    if getattr(user, "role", None) in (TenantUser.ROLE_ADMIN, TenantUser.ROLE_DIRECTOR):
        return True
    return getattr(user, "role", None) in allowed_roles


def _require_role(user, *allowed_roles):
    if not _has_role(user, *allowed_roles):
        raise PermissionDenied("Sizning rolingiz bu bolimga kirish uchun yetarli emas.")


@login_required
def home_redirect(request):
    """
    Login qilingandan keyingi asosiy sahifa.
    - Super admin -> kategoriyalar dashboardiga.
    - Oddiy tenant foydalanuvchisi -> togridan-togri ozining CRM tizimiga.
    """
    user = request.user
    if _is_super_admin(user):
        return redirect("dashboard_categories")

    if not user.tenant_id:
        raise PermissionDenied("Sizga hech qanday tenant biriktirilmagan.")

    tenant = get_object_or_404(Tenant, pk=user.tenant_id)
    return redirect("tenant_dashboard", slug=tenant.category.slug, tenant_id=tenant.id)


@login_required
def dashboard_categories(request):
    """
    1-bosqich: kategoriyalar royxati (kartochkalar korinishida).
    is_available=False bolgan kategoriya qulflangan (bosilmaydigan) korinadi.
    """
    categories = []
    for cat in Category.objects.all():
        categories.append({
            "name": cat.name,
            "slug": cat.slug,
            "is_available": cat.is_available,
            "tenant_count": Tenant.objects.filter(category=cat).count(),
        })

    return render(request, "start/dashboard_categories.html", {"categories": categories})


@login_required
def category_tenants(request, slug):
    """
    2-bosqich: bitta kategoriya ichidagi tenantlar royxati.
    Har bir tenant uchun "menga tegishlimi" (accessible) belgisi hisoblanadi -
    shablon shunga qarab ochiq yoki qulflangan korinishda chizadi.
    """
    category = get_object_or_404(Category, slug=slug)
    if not category.is_available:
        raise Http404("Bu modul hali mavjud emas.")

    user = request.user
    tenants = []
    for t in Tenant.objects.filter(category=category):
        tenants.append({
            "id": t.id,
            "name": t.name,
            "is_valid": t.subscription.is_valid if hasattr(t, "subscription") else False,
            "accessible": _is_super_admin(user) or user.tenant_id == t.id,
        })

    return render(request, "start/category_tenants.html", {
        "category": category,
        "tenants": tenants,
    })


def _get_accessible_tenant(request, slug, tenant_id):
    """Tenant'ni topadi va foydalanuvchi unga kira olishini tekshiradi."""
    tenant = get_object_or_404(Tenant, pk=tenant_id, category__slug=slug)
    user = request.user
    if not _is_super_admin(user) and user.tenant_id != tenant.id:
        raise PermissionDenied("Bu tenant sizga tegishli emas.")
    return tenant


@login_required
def tenant_dashboard(request, slug, tenant_id):
    """
    Tenant asosiy sahifasi. Kategoriya turiga qarab CRM yoki POS
    dashboardini korsatadi.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)

    if tenant.category.module_type == Category.MODULE_POS:
        return pos_dashboard(request, tenant)
    if tenant.category.module_type == Category.MODULE_QUR:
        return qur_dashboard(request, tenant)
    if tenant.category.module_type == Category.MODULE_BOGCHA:
        return bogcha_dashboard(request, tenant)
    if tenant.category.module_type == 'prarab' or tenant.category.slug == 'prorab':
        return redirect('qurilish_dashboard', slug=slug, tenant_id=tenant_id)
    if tenant.category.module_type == Category.MODULE_GUGURT:
        return redirect(
            "gugurt_dashboard",
            slug=tenant.category.slug,
            tenant_id=tenant.id,
    )

    today = timezone.now().date()

    students = Student.objects.filter(tenant=tenant)
    total_students = students.count()
    teachers_count = Teacher.objects.filter(tenant=tenant).count()
    groups_count = Group.objects.filter(tenant=tenant).count()

    today_records = Attendance.objects.filter(tenant=tenant, date=today).select_related("student", "student__group")
    absent_today = today_records.exclude(status="present")
    absent_today_count = absent_today.count()
    absent_unexcused = today_records.filter(status="absent")
    absent_excused = today_records.filter(status="excused")
    present_today = today_records.filter(status="present")

    # Ketma-ket 3 marta kelmagan oquvchilar (sodda hisoblash)
    streak_warnings = []
    for student in students.select_related("group"):
        last_three = list(
            Attendance.objects.filter(student=student).order_by("-date")[:3]
        )
        if len(last_three) == 3 and all(a.status != "present" for a in last_three):
            streak_warnings.append(student)

    # Tolov muddati yaqinlashgan yoki otib ketgan (5 kun ichida yoki kechikkan)
    soon = today + timezone.timedelta(days=5)
    due_soon = Payment.objects.filter(
        tenant=tenant, is_paid=False, due_date__lte=soon
    ).select_related("student").order_by("due_date")

    return render(request, "start/tenant_dashboard.html", {
        "tenant": tenant,
        "total_students": total_students,
        "teachers_count": teachers_count,
        "groups_count": groups_count,
        "absent_today_count": absent_today_count,
        "absent_unexcused": absent_unexcused,
        "absent_excused": absent_excused,
        "present_today": present_today,
        "streak_warnings": streak_warnings,
        "due_soon": due_soon,
        "today": today,
    })


def pos_dashboard(request, tenant):
    """POS (dokon) tenant uchun dashboard: mahsulot, kam qolgan, bugungi savdo."""
    today = timezone.now().date()
    products = Product.objects.filter(tenant=tenant, is_active=True)
    low_stock = products.filter(quantity__lte=models.F("min_quantity"))

    today_sales = Sale.objects.filter(tenant=tenant, status="completed", created_at__date=today)
    today_revenue = sum((s.total_amount or 0) for s in today_sales)

    return render(request, "start/pos_dashboard.html", {
        "tenant": tenant,
        "products_count": products.count(),
        "low_stock": low_stock,
        "low_stock_count": low_stock.count(),
        "today_sales_count": today_sales.count(),
        "today_revenue": today_revenue,
    })


@login_required
def tenant_students(request, slug, tenant_id):
    """
    Tanlangan tenant'ning CRM tizimi (oquvchilar royxati).
    Har bir oquvchi uchun eng yaqin tolanmagan tolov muddati va necha kun
    qolganini hisoblab, royxatga qoshib beradi.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    today = timezone.now().date()
    query = request.GET.get("q", "").strip()

    students_qs = Student.objects.filter(tenant=tenant).select_related("group")
    if query:
        students_qs = students_qs.filter(
            models.Q(full_name__icontains=query) | models.Q(phone__icontains=query)
        )
    students = list(students_qs)

    unpaid = Payment.objects.filter(tenant=tenant, is_paid=False).order_by("due_date")
    nearest_by_student = {}
    for p in unpaid:
        if p.student_id not in nearest_by_student:
            nearest_by_student[p.student_id] = p

    for s in students:
        payment = nearest_by_student.get(s.id)
        if payment:
            s.payment_due_date = payment.due_date
            s.payment_days_left = (payment.due_date - today).days
            s.payment_overdue_days = -s.payment_days_left if s.payment_days_left < 0 else 0
        else:
            s.payment_due_date = None
            s.payment_days_left = None
            s.payment_overdue_days = None

    return render(request, "start/student_list.html", {
        "students": students,
        "tenant": tenant,
        "query": query,
    })


@login_required
def tenant_student_detail(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    student = get_object_or_404(Student, pk=pk, tenant=tenant)
    payments = Payment.objects.filter(tenant=tenant, student=student).order_by("-month")
    attendances = Attendance.objects.filter(tenant=tenant, student=student).order_by("-date")[:30]

    total_att = Attendance.objects.filter(tenant=tenant, student=student).count()
    present_att = Attendance.objects.filter(tenant=tenant, student=student, status="present").count()
    attendance_percent = round((present_att / total_att) * 100) if total_att else None

    nearest_unpaid = payments.filter(is_paid=False).order_by("due_date").first()

    return render(request, "start/student_detail.html", {
        "student": student,
        "tenant": tenant,
        "payments": payments,
        "attendances": attendances,
        "attendance_percent": attendance_percent,
        "total_att": total_att,
        "nearest_unpaid": nearest_unpaid,
    })


UZ_MONTHS = {
    1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 5: "May", 6: "Iyun",
    7: "Iyul", 8: "Avgust", 9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr",
}


def _add_months(d, months):
    from datetime import date
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)


@login_required
def student_payment_create(request, slug, tenant_id, pk):
    """
    Oquvchi sahifasidan togridan-togri tolov qoshish. Bir nechta oyni
    birdaniga tanlab, summani ular orasida bolib tolash mumkin. Balans
    (ortiqcha/qarzdorlik) avtomatik hisoblanadi.
    """
    from datetime import date
    from decimal import Decimal

    tenant = _get_accessible_tenant(request, slug, tenant_id)
    student = get_object_or_404(Student, pk=pk, tenant=tenant)
    today = timezone.now().date()
    current_month_date = date(today.year, today.month, 1)
    group_price = student.group.price if student.group else 0

    month_options = []
    for i in range(6):
        m = _add_months(current_month_date, i)
        month_options.append({"value": m.strftime("%Y-%m"), "label": f"{UZ_MONTHS[m.month]} {m.year}"})

    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount") or 0)
        except Exception:
            amount = Decimal(0)

        payment_type = request.POST.get("payment_type", "cash")
        custom_due_date = request.POST.get("pay_until") or None
        selected_months = request.POST.getlist("months")

        if selected_months:
            count = len(selected_months)
            base_amount = amount // count
            remainder = amount - base_amount * count
            last_month_date = None

            for idx, month_str in enumerate(sorted(selected_months)):
                y, m = map(int, month_str.split("-"))
                month_date = date(y, m, 1)
                last_month_date = month_date
                pay_amount = base_amount + (remainder if idx == count - 1 else 0)

                Payment.objects.update_or_create(
                    tenant=tenant, student=student, month=month_date,
                    defaults={
                        "due_date": month_date,
                        "amount": pay_amount,
                        "payment_type": payment_type,
                        "is_paid": True,
                        "paid_date": today,
                    },
                )

            total_needed = group_price * count
            student.balance = student.balance + amount - total_needed

            # Keyingi oy uchun (hali tolanmagan) yozuv - "muddat" sifatida korinadi
            # Oldindan tolash tamoyili: keyingi oy uchun muddat oy boshigacha
            # emas, JORIY oyning 25-kuniga qoyiladi - shunda ota-ona yangi
            # oy boshlanishidan oldin tolashi kerak boladi.
            from calendar import monthrange
            last_day_of_month = monthrange(last_month_date.year, last_month_date.month)[1]
            advance_due_day = min(25, last_day_of_month)
            advance_due_date = date(last_month_date.year, last_month_date.month, advance_due_day)

            next_month = _add_months(last_month_date, 1)
            next_due = custom_due_date or advance_due_date
            Payment.objects.get_or_create(
                tenant=tenant, student=student, month=next_month,
                defaults={"due_date": next_due, "amount": group_price, "is_paid": False},
            )
        else:
            Payment.objects.update_or_create(
                tenant=tenant, student=student, month=current_month_date,
                defaults={
                    "due_date": custom_due_date or current_month_date,
                    "amount": amount,
                    "payment_type": payment_type,
                    "is_paid": True,
                    "paid_date": today,
                },
            )
            student.balance = student.balance + amount - group_price

        student.save()
        return redirect("tenant_student_detail", slug=slug, tenant_id=tenant_id, pk=pk)

    nearest_unpaid = Payment.objects.filter(
        tenant=tenant, student=student, is_paid=False
    ).order_by("due_date").first()

    return render(request, "start/student_payment_form.html", {
        "tenant": tenant,
        "student": student,
        "month_options": month_options,
        "group_price": group_price,
        "nearest_unpaid": nearest_unpaid,
    })


@login_required
def tenant_student_create(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    groups = Group.objects.filter(tenant=tenant)

    if request.method == "POST":
        Student.objects.create(
            tenant=tenant,
            group_id=request.POST.get("group") or None,
            full_name=request.POST.get("full_name", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            note=request.POST.get("note", "").strip(),
        )
        return redirect("tenant_students", slug=slug, tenant_id=tenant_id)

    return render(request, "start/student_form.html", {"tenant": tenant, "groups": groups, "student": None})


@login_required
def tenant_student_edit(request, slug, tenant_id, pk):
    """Oquvchi malumotlarini tahrirlash, shu jumladan guruhini almashtirish."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    student = get_object_or_404(Student, pk=pk, tenant=tenant)
    groups = Group.objects.filter(tenant=tenant)

    if request.method == "POST":
        student.full_name = request.POST.get("full_name", "").strip()
        student.phone = request.POST.get("phone", "").strip()
        student.note = request.POST.get("note", "").strip()
        student.group_id = request.POST.get("group") or None
        student.save()
        return redirect("tenant_student_detail", slug=slug, tenant_id=tenant_id, pk=student.id)

    return render(request, "start/student_form.html", {"tenant": tenant, "groups": groups, "student": student})


@login_required
def tenant_student_delete(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    student = get_object_or_404(Student, pk=pk, tenant=tenant)

    if request.method == "POST":
        student.delete()
        return redirect("tenant_students", slug=slug, tenant_id=tenant_id)

    return render(request, "start/student_confirm_delete.html", {"tenant": tenant, "student": student})


@login_required
def tenant_attendance_today(request, slug, tenant_id):
    """
    Bugungi kun uchun har bir oquvchining davomatini belgilash sahifasi.
    Har safar saqlaganda mavjud yozuv yangilanadi (update_or_create).
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    today = timezone.now().date()
    students = Student.objects.filter(tenant=tenant).select_related("group")

    if request.method == "POST":
        for student in students:
            status = request.POST.get(f"status_{student.id}")
            note = request.POST.get(f"note_{student.id}", "").strip()
            if status:
                Attendance.objects.update_or_create(
                    tenant=tenant, student=student, date=today,
                    defaults={"status": status, "note": note},
                )
        return redirect("tenant_dashboard", slug=slug, tenant_id=tenant_id)

    existing = {a.student_id: a for a in Attendance.objects.filter(tenant=tenant, date=today)}
    rows = [{"student": s, "attendance": existing.get(s.id)} for s in students]

    return render(request, "start/attendance_today.html", {
        "tenant": tenant,
        "rows": rows,
        "today": today,
    })


@login_required
def group_attendance(request, slug, tenant_id, group_id):
    """
    Bitta guruh uchun bugungi davomatni belgilash. Agar bu guruh uchun
    bugun allaqachon davomat olingan bolsa, qayta belgilashni bloklaydi -
    ozgartirish kerak bolsa 'Davomat hisoboti' orqali qilish kerak.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    group = get_object_or_404(Group, pk=group_id, tenant=tenant)
    today = timezone.now().date()
    students = Student.objects.filter(tenant=tenant, group=group)

    already_taken = Attendance.objects.filter(tenant=tenant, student__group=group, date=today).exists()
    if already_taken:
        return redirect(f"{_reverse_url('group_list', slug, tenant_id)}?blocked=1")

    if request.method == "POST":
        for student in students:
            status = request.POST.get(f"status_{student.id}", "present")
            note = request.POST.get(f"note_{student.id}", "").strip()
            Attendance.objects.update_or_create(
                tenant=tenant, student=student, date=today,
                defaults={"status": status, "note": note},
            )
        return redirect("group_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/group_attendance.html", {
        "tenant": tenant, "group": group, "students": students, "today": today,
    })


def _reverse_url(name, *args):
    from django.urls import reverse
    return reverse(name, args=args)


def _parse_date_param(request, default):
    raw = request.GET.get("date")
    if not raw:
        return default
    try:
        from datetime import datetime
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return default


@login_required
def attendance_report(request, slug, tenant_id):
    """
    Davomat hisoboti: tanlangan sana uchun Kelganlar / Kelmaganlar royxati,
    Kecha / Ertaga / Bugun tugmalari bilan sanalar orasida yurish mumkin.
    Belgilanmagan (hali davomat kiritilmagan) oquvchilar alohida korsatiladi.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    today = timezone.now().date()
    selected_date = _parse_date_param(request, today)

    students = Student.objects.filter(tenant=tenant).select_related("group")
    records = {
        a.student_id: a
        for a in Attendance.objects.filter(tenant=tenant, date=selected_date).select_related("student", "student__group")
    }

    present, absent, unmarked = [], [], []
    for s in students:
        record = records.get(s.id)
        if record is None:
            unmarked.append(s)
        elif record.status == "present":
            present.append(record)
        else:
            absent.append(record)

    return render(request, "start/attendance_report.html", {
        "tenant": tenant,
        "selected_date": selected_date,
        "prev_date": selected_date - timezone.timedelta(days=1),
        "next_date": selected_date + timezone.timedelta(days=1),
        "today": today,
        "present": present,
        "absent": absent,
        "unmarked": unmarked,
    })


@login_required
def attendance_quick_edit(request, slug, tenant_id, student_id):
    """Bitta oquvchining bitta kunlik davomatini tez tahrirlash/belgilash."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    student = get_object_or_404(Student, pk=student_id, tenant=tenant)
    today = timezone.now().date()
    selected_date = _parse_date_param(request, today)

    attendance = Attendance.objects.filter(tenant=tenant, student=student, date=selected_date).first()

    if attendance and not attendance.is_editable():
        raise PermissionDenied(
            f"Bu davomat yozuvini tahrirlash muddati (bugungi holatda {Attendance.EDIT_WINDOW_HOURS} soat) tugagan."
        )

    if request.method == "POST":
        status = request.POST.get("status", "present")
        note = request.POST.get("note", "").strip()
        Attendance.objects.update_or_create(
            tenant=tenant, student=student, date=selected_date,
            defaults={"status": status, "note": note},
        )
        return redirect(f"{_reverse_report(slug, tenant_id)}?date={selected_date.isoformat()}")

    return render(request, "start/attendance_quick_edit.html", {
        "tenant": tenant, "student": student, "attendance": attendance, "selected_date": selected_date,
    })


def _reverse_report(slug, tenant_id):
    from django.urls import reverse
    return reverse("attendance_report", args=[slug, tenant_id])


# ---------- Ustoz (Teacher) CRUD ----------

@login_required
def teacher_list(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    teachers = Teacher.objects.filter(tenant=tenant)
    return render(request, "start/teacher_list.html", {"tenant": tenant, "teachers": teachers})


@login_required
def teacher_create(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user)  # faqat Admin/Direktor - tarbiyachi/oshpaz qosha olmaydi

    if request.method == "POST":
        Teacher.objects.create(
            tenant=tenant,
            full_name=request.POST.get("full_name", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            subject=request.POST.get("subject", "").strip(),
        )
        return redirect("teacher_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/teacher_form.html", {"tenant": tenant, "teacher": None})


@login_required
def teacher_detail(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    teacher = get_object_or_404(Teacher, pk=pk, tenant=tenant)
    groups = Group.objects.filter(tenant=tenant, teacher=teacher)
    return render(request, "start/teacher_detail.html", {
        "tenant": tenant, "teacher": teacher, "groups": groups,
    })


@login_required
def teacher_edit(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user)
    teacher = get_object_or_404(Teacher, pk=pk, tenant=tenant)

    if request.method == "POST":
        teacher.full_name = request.POST.get("full_name", "").strip()
        teacher.phone = request.POST.get("phone", "").strip()
        teacher.subject = request.POST.get("subject", "").strip()
        teacher.save()
        return redirect("teacher_detail", slug=slug, tenant_id=tenant_id, pk=teacher.id)

    return render(request, "start/teacher_form.html", {"tenant": tenant, "teacher": teacher})


@login_required
def teacher_delete(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user)
    teacher = get_object_or_404(Teacher, pk=pk, tenant=tenant)

    if request.method == "POST":
        teacher.delete()
        return redirect("teacher_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/teacher_confirm_delete.html", {"tenant": tenant, "teacher": teacher})


# ---------- Guruh (Group) CRUD ----------

@login_required
def group_list(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    today = timezone.now().date()
    groups = list(Group.objects.filter(tenant=tenant).select_related("teacher"))

    for g in groups:
        g.attendance_taken_today = Attendance.objects.filter(
            tenant=tenant, student__group=g, date=today
        ).exists()

    return render(request, "start/group_list.html", {
        "tenant": tenant, "groups": groups, "blocked": request.GET.get("blocked"),
    })


WEEKDAYS = [
    ("mon", "Dushanba"), ("tue", "Seshanba"), ("wed", "Chorshanba"),
    ("thu", "Payshanba"), ("fri", "Juma"), ("sat", "Shanba"), ("sun", "Yakshanba"),
]


@login_required
def group_create(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    teachers = Teacher.objects.filter(tenant=tenant)

    if request.method == "POST":
        teacher_id = request.POST.get("teacher") or None
        selected_days = request.POST.getlist("days")
        Group.objects.create(
            tenant=tenant,
            name=request.POST.get("name", "").strip(),
            teacher_id=teacher_id,
            price=request.POST.get("price") or 0,
            days=",".join(selected_days),
            start_time=request.POST.get("start_time") or None,
            end_time=request.POST.get("end_time") or None,
        )
        return redirect("group_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/group_form.html", {
        "tenant": tenant, "teachers": teachers, "group": None, "weekdays": WEEKDAYS, "selected_days": [],
    })


@login_required
def group_edit(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    group = get_object_or_404(Group, pk=pk, tenant=tenant)
    teachers = Teacher.objects.filter(tenant=tenant)

    if request.method == "POST":
        selected_days = request.POST.getlist("days")
        group.name = request.POST.get("name", "").strip()
        group.teacher_id = request.POST.get("teacher") or None
        group.price = request.POST.get("price") or 0
        group.days = ",".join(selected_days)
        group.start_time = request.POST.get("start_time") or None
        group.end_time = request.POST.get("end_time") or None
        group.save()
        return redirect("group_detail", slug=slug, tenant_id=tenant_id, pk=group.id)

    return render(request, "start/group_form.html", {
        "tenant": tenant, "teachers": teachers, "group": group,
        "weekdays": WEEKDAYS, "selected_days": group.get_days_list(),
    })


@login_required
def group_delete(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    group = get_object_or_404(Group, pk=pk, tenant=tenant)

    if request.method == "POST":
        group.delete()  # Student.group SET_NULL bolgani uchun oquvchilar ochirilmaydi, faqat guruhi bosh qoladi
        return redirect("group_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/group_confirm_delete.html", {"tenant": tenant, "group": group})


@login_required
def group_detail(request, slug, tenant_id, pk):
    """
    Guruh tafsiloti: unga biriktirilgan oquvchilar va tenant ichidagi
    "erkin" (bu guruhga tegishli bolmagan) oquvchilar royxati - shu yerdan
    guruhga qoshish/chiqarish mumkin.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    group = get_object_or_404(Group, pk=pk, tenant=tenant)

    if request.method == "POST":
        action = request.POST.get("action")
        student_id = request.POST.get("student_id")
        student = get_object_or_404(Student, pk=student_id, tenant=tenant)

        if action == "add":
            student.group = group
        elif action == "remove":
            student.group = None
        student.save()
        return redirect("group_detail", slug=slug, tenant_id=tenant_id, pk=pk)

    members = Student.objects.filter(tenant=tenant, group=group)
    others = Student.objects.filter(tenant=tenant).exclude(group=group)

    return render(request, "start/group_detail.html", {
        "tenant": tenant, "group": group, "members": members, "others": others,
    })


# ---------- Tolov (Payment) ----------

@login_required
def payment_list(request, slug, tenant_id):
    """
    Tolovlar royxati - har bir oquvchi uchun faqat ENG OXIRGI tolov yozuvi
    korsatiladi (bir xil oquvchining har bir tolovi alohida qator bolib
    yopishib qolmasligi uchun). Toliq tarix oquvchi sahifasida koriladi.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)

    all_payments = (
        Payment.objects.filter(tenant=tenant)
        .select_related("student")
        .order_by("student_id", "-month", "-id")
    )

    latest_by_student = {}
    for p in all_payments:
        if p.student_id not in latest_by_student:
            latest_by_student[p.student_id] = p

    payments = sorted(latest_by_student.values(), key=lambda p: p.month, reverse=True)

    return render(request, "start/payment_list.html", {"tenant": tenant, "payments": payments})


@login_required
def payment_create(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    students = Student.objects.filter(tenant=tenant)

    if request.method == "POST":
        Payment.objects.update_or_create(
            tenant=tenant,
            student_id=request.POST.get("student"),
            month=request.POST.get("month"),
            defaults={
                "due_date": request.POST.get("due_date"),
                "amount": request.POST.get("amount") or None,
                "payment_type": request.POST.get("payment_type", "cash"),
                "note": request.POST.get("note", "").strip(),
            },
        )
        return redirect("payment_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/payment_form.html", {"tenant": tenant, "students": students})


@login_required
def payment_mark_paid(request, slug, tenant_id, pk):
    """Bitta tugma bilan tolovni 'tolangan' deb belgilash (yoki qaytarish)."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    payment = get_object_or_404(Payment, pk=pk, tenant=tenant)

    if request.method == "POST":
        payment.is_paid = not payment.is_paid
        payment.paid_date = timezone.now().date() if payment.is_paid else None
        payment.save()

    return redirect("payment_list", slug=slug, tenant_id=tenant_id)


@login_required
def payment_delete(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    payment = get_object_or_404(Payment, pk=pk, tenant=tenant)

    if request.method == "POST":
        payment.delete()
        return redirect("payment_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/payment_confirm_delete.html", {"tenant": tenant, "payment": payment})


@login_required
def payment_report(request, slug, tenant_id):
    """
    Oy boyicha jamlangan tolovlar hisoboti: jami summa, tolangan, qarzdorlik,
    va har bir oquvchining shu oy uchun holati.
    """
    from datetime import date

    tenant = _get_accessible_tenant(request, slug, tenant_id)
    today = timezone.now().date()

    month_str = request.GET.get("month")
    try:
        year, mon = map(int, month_str.split("-"))
        selected_month = date(year, mon, 1)
    except (TypeError, ValueError, AttributeError):
        selected_month = date(today.year, today.month, 1)

    prev_month = (selected_month.replace(day=1) - timezone.timedelta(days=1)).replace(day=1)
    next_month_last_day = (selected_month.replace(day=28) + timezone.timedelta(days=7))
    next_month = next_month_last_day.replace(day=1)

    payments = Payment.objects.filter(
        tenant=tenant, month__year=selected_month.year, month__month=selected_month.month
    ).select_related("student").order_by("student__full_name")

    total_amount = sum((p.amount or 0) for p in payments)
    paid_amount = sum((p.amount or 0) for p in payments if p.is_paid)
    debt_amount = total_amount - paid_amount
    paid_count = sum(1 for p in payments if p.is_paid)
    unpaid_count = sum(1 for p in payments if not p.is_paid)

    return render(request, "start/payment_report.html", {
        "tenant": tenant,
        "selected_month": selected_month,
        "prev_month": prev_month,
        "next_month": next_month,
        "payments": payments,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "debt_amount": debt_amount,
        "paid_count": paid_count,
        "unpaid_count": unpaid_count,
    })


WEEKDAY_CODES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
UZ_DAY_LABELS = {
    "mon": "Dush", "tue": "Sesh", "wed": "Chor", "thu": "Pay",
    "fri": "Jum", "sat": "Shan", "sun": "Yak",
}


@login_required
def schedule_view(request, slug, tenant_id):
    """
    Haftalik Dars Jadvali: har bir guruh qatorda, har bir kun ustunda.
    Guruhning dars kuni bo'lsa, shu kun ustida vaqt (start_time-end_time) korinadi.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    groups = Group.objects.filter(tenant=tenant).select_related("teacher")
    today = timezone.now().date()

    try:
        week_offset = int(request.GET.get("week", 0))
    except (ValueError, TypeError):
        week_offset = 0

    current_monday = today - timezone.timedelta(days=today.weekday())
    week_start = current_monday + timezone.timedelta(weeks=week_offset)

    days = []
    for i in range(7):
        d = week_start + timezone.timedelta(days=i)
        code = WEEKDAY_CODES[d.weekday()]
        days.append({"date": d, "code": code, "label": UZ_DAY_LABELS[code], "is_today": d == today})

    return render(request, "start/schedule.html", {
        "tenant": tenant,
        "groups": groups,
        "days": days,
        "week_offset": week_offset,
        "today": today,
    })


@login_required
def financial_report(request, slug, tenant_id):
    """
    Moliyaviy hisobot: tanlangan davr uchun Daromad (tolangan tolovlar),
    Xarajat va Foyda (daromad - xarajat).
    """
    from datetime import datetime

    tenant = _get_accessible_tenant(request, slug, tenant_id)
    today = timezone.now().date()

    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        start_date = today.replace(day=1)
        end_date = today

    payments = Payment.objects.filter(
        tenant=tenant, is_paid=True, paid_date__gte=start_date, paid_date__lte=end_date
    ).select_related("student").order_by("-paid_date")

    expenses = Expense.objects.filter(
        tenant=tenant, date__gte=start_date, date__lte=end_date
    ).order_by("-date")

    total_income = sum((p.amount or 0) for p in payments)
    total_expense = sum((e.amount or 0) for e in expenses)
    net_profit = total_income - total_expense

    return render(request, "start/financial_report.html", {
        "tenant": tenant,
        "payments": payments,
        "expenses": expenses,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_profit": net_profit,
        "start_date": start_date,
        "end_date": end_date,
        "today": today,
        "this_month_start": today.replace(day=1),
    })


@login_required
def add_expense(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)

    if request.method == "POST":
        Expense.objects.create(
            tenant=tenant,
            title=request.POST.get("title", "").strip(),
            expense_type=request.POST.get("expense_type", "other"),
            amount=request.POST.get("amount") or 0,
            date=request.POST.get("date") or timezone.now().date(),
            note=request.POST.get("note", "").strip(),
        )
        return redirect("financial_report", slug=slug, tenant_id=tenant_id)

    return render(request, "start/add_expense.html", {"tenant": tenant})


# ---------- POS (dokon) viewlari ----------

@login_required
def product_category_list(request, slug, tenant_id):
    """1-bosqich: mahsulot kategoriyalari royxati (kartochka korinishida)."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI, TenantUser.ROLE_MENEJER)
    categories = []
    for c in ProductCategory.objects.filter(tenant=tenant):
        categories.append({"id": c.id, "name": c.name, "count": Product.objects.filter(category=c, is_active=True).count()})
    uncategorized_count = Product.objects.filter(tenant=tenant, category__isnull=True, is_active=True).count()
    return render(request, "start/product_category_list.html", {
        "tenant": tenant, "categories": categories, "uncategorized_count": uncategorized_count,
    })


@login_required
def product_category_create(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI)

    if request.method == "POST":
        ProductCategory.objects.create(tenant=tenant, name=request.POST.get("name", "").strip())
        return redirect("product_category_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/product_category_form.html", {"tenant": tenant})


@login_required
def product_list(request, slug, tenant_id, category_id):
    """2-bosqich: tanlangan kategoriyadagi mahsulotlar. category_id=0 - kategoriyasizlar."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI, TenantUser.ROLE_MENEJER)

    if category_id == 0:
        category = None
        products = Product.objects.filter(tenant=tenant, category__isnull=True, is_active=True)
    else:
        category = get_object_or_404(ProductCategory, pk=category_id, tenant=tenant)
        products = Product.objects.filter(tenant=tenant, category=category, is_active=True)

    return render(request, "start/product_list.html", {
        "tenant": tenant, "category": category, "category_id": category_id, "products": products,
        "archived": request.GET.get("archived"),
    })


@login_required
def product_create(request, slug, tenant_id, category_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI)
    category = None if category_id == 0 else get_object_or_404(ProductCategory, pk=category_id, tenant=tenant)

    if request.method == "POST":
        Product.objects.create(
            tenant=tenant,
            category=category,
            name=request.POST.get("name", "").strip(),
            barcode=request.POST.get("barcode", "").strip(),
            unit=request.POST.get("unit", Product.UNIT_PIECE),
            price=request.POST.get("price") or 0,
            discount_price=request.POST.get("discount_price") or None,
            quantity=request.POST.get("quantity") or 0,
            min_quantity=request.POST.get("min_quantity") or 5,
        )
        return redirect("product_list", slug=slug, tenant_id=tenant_id, category_id=category_id)

    return render(request, "start/product_form.html", {
        "tenant": tenant, "product": None, "category_id": category_id, "units": Product.UNIT_CHOICES,
    })


@login_required
def product_edit(request, slug, tenant_id, category_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI)
    product = get_object_or_404(Product, pk=pk, tenant=tenant)

    if request.method == "POST":
        product.name = request.POST.get("name", "").strip()
        product.barcode = request.POST.get("barcode", "").strip()
        product.unit = request.POST.get("unit", Product.UNIT_PIECE)
        product.price = request.POST.get("price") or 0
        product.discount_price = request.POST.get("discount_price") or None
        product.quantity = request.POST.get("quantity") or 0
        product.min_quantity = request.POST.get("min_quantity") or 5
        product.save()
        return redirect("product_list", slug=slug, tenant_id=tenant_id, category_id=category_id)

    return render(request, "start/product_form.html", {
        "tenant": tenant, "product": product, "category_id": category_id, "units": Product.UNIT_CHOICES,
    })


@login_required
def product_delete(request, slug, tenant_id, category_id, pk):
    from django.db.models import ProtectedError

    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI)
    product = get_object_or_404(Product, pk=pk, tenant=tenant)

    if request.method == "POST":
        try:
            product.delete()
        except ProtectedError:
            # Bu mahsulot sotuvda ishlatilgan, shuning uchun ochira olmaymiz -
            # o'rniga nofaol qilib belgilaymiz, sotuv tarixi buzilmaydi.
            product.is_active = False
            product.save()
            return redirect(f"{_product_list_url(slug, tenant_id, category_id)}?archived=1")
        return redirect("product_list", slug=slug, tenant_id=tenant_id, category_id=category_id)

    return render(request, "start/product_confirm_delete.html", {
        "tenant": tenant, "product": product, "category_id": category_id,
    })


def _product_list_url(slug, tenant_id, category_id):
    from django.urls import reverse
    return reverse("product_list", args=[slug, tenant_id, category_id])


def _get_open_sale(tenant, user=None):
    """
    Tenant uchun ochiq (hali tolanmagan) savatni topadi, bolmasa yaratadi.
    Eski (masalan migratsiyadan qolgan) ortiqcha bosh ochiq savatlar bolsa,
    faqat eng oxirgisini qoldirib, qolganlarini ochirib tashlaydi.
    """
    open_sales = list(Sale.objects.filter(tenant=tenant, status="open").order_by("-created_at"))
    if not open_sales:
        return Sale.objects.create(tenant=tenant, status="open", total_amount=0, created_by=user)

    sale = open_sales[0]
    for extra in open_sales[1:]:
        if not extra.items.exists():
            extra.delete()
    return sale


@login_required
def sale_category_list(request, slug, tenant_id):
    """
    Sotuv boshlanish sahifasi: ochiq savat avtomatik davom etadi (yangisi
    yaratilmaydi), kategoriyalar korsatiladi, savatdagi joriy summa va
    "Tolovni yakunlash" tugmasi chiqadi.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR)

    sale = _get_open_sale(tenant, request.user)
    cart_items = sale.items.select_related("product")
    cart_count = cart_items.count()

    categories = []
    for c in ProductCategory.objects.filter(tenant=tenant):
        categories.append({"id": c.id, "name": c.name, "count": Product.objects.filter(category=c, is_active=True).count()})
    uncategorized_count = Product.objects.filter(tenant=tenant, category__isnull=True, is_active=True).count()

    return render(request, "start/sale_category_list.html", {
        "tenant": tenant, "categories": categories, "uncategorized_count": uncategorized_count,
        "sale": sale, "cart_items": cart_items, "cart_count": cart_count,
    })


@login_required
def sale_add_products(request, slug, tenant_id, category_id):
    """
    Tanlangan kategoriyadagi mahsulotlardan miqdor kiritib, JORIY OCHIQ
    savatga qoshiladi. Savat tolov qilingunga qadar saqlanib qoladi,
    boshqa kategoriyadan ham qoshish mumkin.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR)
    sale = _get_open_sale(tenant, request.user)

    if category_id == 0:
        category = None
        products = Product.objects.filter(tenant=tenant, category__isnull=True, is_active=True)
    else:
        category = get_object_or_404(ProductCategory, pk=category_id, tenant=tenant)
        products = Product.objects.filter(tenant=tenant, category=category, is_active=True)

    if request.method == "POST":
        added_total = 0

        for product in products:
            qty_str = request.POST.get(f"qty_{product.id}", "").strip()
            if not qty_str:
                continue
            try:
                qty = Decimal(qty_str)
            except InvalidOperation:
                continue
            if qty <= 0:
                continue

            qty = min(qty, product.quantity)  # ombordan ortiq sota olmaydi
            if qty <= 0:
                continue

            unit_price = product.effective_price
            existing_item = SaleItem.objects.filter(sale=sale, product=product).first()
            if existing_item:
                existing_item.quantity += qty
                existing_item.save()
            else:
                SaleItem.objects.create(sale=sale, product=product, quantity=qty, unit_price=unit_price)

            product.quantity -= qty
            product.save()
            added_total += qty * unit_price

        sale.total_amount += added_total
        sale.save()
        return redirect("sale_category_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/sale_create.html", {
        "tenant": tenant, "category": category, "category_id": category_id, "products": products, "sale": sale,
    })


@login_required
def sale_checkout(request, slug, tenant_id):
    """Joriy ochiq savatni koradi, kerak bolsa mahsulotni olib tashlaydi, tolovni yakunlaydi."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR)
    sale = _get_open_sale(tenant, request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "remove_item":
            item = get_object_or_404(SaleItem, pk=request.POST.get("item_id"), sale=sale)
            item.product.quantity += item.quantity  # ombordan olib tashlanganini qaytarish
            item.product.save()
            sale.total_amount -= item.line_total
            sale.save()
            item.delete()
            return redirect("sale_checkout", slug=slug, tenant_id=tenant_id)

        elif action == "finish":
            if sale.items.exists():
                sale.payment_method = request.POST.get("payment_method", "cash")
                sale.status = "completed"
                sale.save()
                return redirect("sale_detail", slug=slug, tenant_id=tenant_id, pk=sale.id)

    items = sale.items.select_related("product")
    return render(request, "start/sale_checkout.html", {"tenant": tenant, "sale": sale, "items": items})


@login_required
@login_required
def sale_list(request, slug, tenant_id):
    """
    Sotuvlar tarixi - bitta sanani tanlab korish (Kecha/Ertaga/Bugun
    tugmalari bilan). Excel eksport ham aynan shu tanlangan kunni yuklaydi.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR, TenantUser.ROLE_MENEJER)

    today = timezone.now().date()
    selected_date = _parse_date_param(request, today)

    day_sales = Sale.objects.filter(tenant=tenant, status="completed", created_at__date=selected_date)
    day_total = sum((s.total_amount or 0) for s in day_sales)

    return render(request, "start/sale_list.html", {
        "tenant": tenant,
        "selected_date": selected_date,
        "prev_date": selected_date - timezone.timedelta(days=1),
        "next_date": selected_date + timezone.timedelta(days=1),
        "today": today,
        "day_sales": day_sales,
        "day_total": day_total,
    })


@login_required
def sale_export(request, slug, tenant_id):
    """Tanlangan kundagi sotuvlarni Excel'da ochiladigan CSV korinishida yuklab olish."""
    import csv

    from django.http import HttpResponse

    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR, TenantUser.ROLE_MENEJER)

    today = timezone.now().date()
    selected_date = _parse_date_param(request, today)
    sales = Sale.objects.filter(tenant=tenant, status="completed", created_at__date=selected_date)

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = f'attachment; filename="sotuvlar_{selected_date.isoformat()}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Sana", "ID", "Tolov turi", "Summa"])
    for s in sales:
        writer.writerow([
            s.created_at.strftime("%d.%m.%Y %H:%M"),
            s.id,
            s.get_payment_method_display(),
            s.total_amount,
        ])

    return response


@login_required
def sale_detail(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR, TenantUser.ROLE_MENEJER)
    sale = get_object_or_404(Sale, pk=pk, tenant=tenant)
    items = sale.items.select_related("product")
    return render(request, "start/sale_detail.html", {"tenant": tenant, "sale": sale, "items": items})


@login_required
def purchase_create(request, slug, tenant_id):
    """Yetkazib beruvchidan mahsulot kirimi - sklad qoldigini oshiradi."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI)
    products = Product.objects.filter(tenant=tenant)

    if request.method == "POST":
        product = get_object_or_404(Product, pk=request.POST.get("product"), tenant=tenant)
        qty = Decimal(request.POST.get("quantity") or 0)

        Purchase.objects.create(
            tenant=tenant,
            product=product,
            supplier=request.POST.get("supplier", "").strip(),
            quantity=qty,
            unit_cost=request.POST.get("unit_cost") or None,
            date=request.POST.get("date") or timezone.now().date(),
            note=request.POST.get("note", "").strip(),
        )
        product.quantity += qty
        product.save()
        return redirect("product_category_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/purchase_form.html", {"tenant": tenant, "products": products})


@login_required
def pos_report(request, slug, tenant_id):
    """
    POS hisoboti: tanlangan davr uchun jami sotuv/daromad, mahsulot boyicha
    taqsimot, va joriy ombor qoldigi.
    """
    from datetime import datetime

    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_MENEJER)
    today = timezone.now().date()

    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        start_date = today.replace(day=1)
        end_date = today

    sales = Sale.objects.filter(
        tenant=tenant, status="completed", created_at__date__gte=start_date, created_at__date__lte=end_date
    )
    sales_count = sales.count()
    total_revenue = sum((s.total_amount or 0) for s in sales)

    product_stats = (
        SaleItem.objects.filter(sale__in=sales)
        .values("product__name")
        .annotate(
            total_qty=models.Sum("quantity"),
            total_revenue=models.Sum(models.F("quantity") * models.F("unit_price")),
        )
        .order_by("-total_revenue")
    )

    stock = Product.objects.filter(tenant=tenant).order_by("name")

    return render(request, "start/pos_report.html", {
        "tenant": tenant,
        "start_date": start_date,
        "end_date": end_date,
        "sales_count": sales_count,
        "total_revenue": total_revenue,
        "product_stats": product_stats,
        "stock": stock,
    })


# ---------- Foydalanuvchilar (xodimlar) va rollar ----------

@login_required
def staff_list(request, slug, tenant_id):
    """Tenant ichidagi barcha xodimlar royxati. Faqat Admin/super admin kira oladi."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    if not (_is_super_admin(request.user) or getattr(request.user, "role", None) == TenantUser.ROLE_ADMIN):
        raise PermissionDenied("Faqat Admin xodimlarni boshqara oladi.")

    staff = TenantUser.objects.filter(tenant=tenant)
    return render(request, "start/staff_list.html", {"tenant": tenant, "staff": staff})


@login_required
def staff_create(request, slug, tenant_id):
    """Tenant uchun yangi xodim (login+parol+rol) yaratish."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    if not (_is_super_admin(request.user) or getattr(request.user, "role", None) == TenantUser.ROLE_ADMIN):
        raise PermissionDenied("Faqat Admin xodim qosha oladi.")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", TenantUser.ROLE_KASSIR)

        if username and password:
            user = TenantUser.objects.create_user(username=username, password=password)
            user.tenant = tenant
            user.role = role
            user.save()
            return redirect("staff_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/staff_form.html", {
        "tenant": tenant, "staff_member": None, "roles": TenantUser.ROLE_CHOICES,
    })


@login_required
def staff_edit(request, slug, tenant_id, pk):
    """Xodimning rolini ozgartirish yoki parolini yangilash."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    if not (_is_super_admin(request.user) or getattr(request.user, "role", None) == TenantUser.ROLE_ADMIN):
        raise PermissionDenied("Faqat Admin xodimni tahrirlashi mumkin.")

    staff_member = get_object_or_404(TenantUser, pk=pk, tenant=tenant)

    if request.method == "POST":
        staff_member.role = request.POST.get("role", staff_member.role)
        new_password = request.POST.get("password", "").strip()
        if new_password:
            staff_member.set_password(new_password)
        staff_member.is_active = bool(request.POST.get("is_active"))
        staff_member.save()
        return redirect("staff_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/staff_form.html", {
        "tenant": tenant, "staff_member": staff_member, "roles": TenantUser.ROLE_CHOICES,
    })


# ---------- QUR (qurilish mollari) viewlari ----------

def qur_dashboard(request, tenant):
    """Qurilish mollari dokoni uchun dashboard."""
    today = timezone.now().date()
    products = QurilishProduct.objects.filter(tenant=tenant, is_active=True)
    low_stock = products.filter(quantity__lte=models.F("min_quantity"))

    today_sales = QurilishSale.objects.filter(tenant=tenant, status="completed", created_at__date=today)
    today_revenue = sum((s.total_amount or 0) for s in today_sales)

    return render(request, "start/qur_dashboard.html", {
        "tenant": tenant,
        "products_count": products.count(),
        "low_stock": low_stock,
        "low_stock_count": low_stock.count(),
        "today_sales_count": today_sales.count(),
        "today_revenue": today_revenue,
    })


@login_required
def qur_category_list(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI, TenantUser.ROLE_MENEJER)
    categories = []
    for c in QurilishCategory.objects.filter(tenant=tenant):
        categories.append({
            "id": c.id, "name": c.name,
            "count": QurilishProduct.objects.filter(category=c, is_active=True).count(),
        })
    uncategorized_count = QurilishProduct.objects.filter(
        tenant=tenant, category__isnull=True, is_active=True
    ).count()
    return render(request, "start/qur_category_list.html", {
        "tenant": tenant, "categories": categories, "uncategorized_count": uncategorized_count,
    })


@login_required
def qur_category_create(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI)

    if request.method == "POST":
        QurilishCategory.objects.create(tenant=tenant, name=request.POST.get("name", "").strip())
        return redirect("qur_category_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/qur_category_form.html", {"tenant": tenant})


@login_required
def qur_product_list(request, slug, tenant_id, category_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI, TenantUser.ROLE_MENEJER)

    if category_id == 0:
        category = None
        products = QurilishProduct.objects.filter(tenant=tenant, category__isnull=True, is_active=True)
    else:
        category = get_object_or_404(QurilishCategory, pk=category_id, tenant=tenant)
        products = QurilishProduct.objects.filter(tenant=tenant, category=category, is_active=True)

    return render(request, "start/qur_product_list.html", {
        "tenant": tenant, "category": category, "category_id": category_id, "products": products,
        "archived": request.GET.get("archived"),
    })


@login_required
def qur_product_create(request, slug, tenant_id, category_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI)
    category = None if category_id == 0 else get_object_or_404(QurilishCategory, pk=category_id, tenant=tenant)

    if request.method == "POST":
        QurilishProduct.objects.create(
            tenant=tenant,
            category=category,
            name=request.POST.get("name", "").strip(),
            barcode=request.POST.get("barcode", "").strip(),
            unit=request.POST.get("unit", QurilishProduct.UNIT_PIECE),
            price=request.POST.get("price") or 0,
            discount_price=request.POST.get("discount_price") or None,
            quantity=request.POST.get("quantity") or 0,
            min_quantity=request.POST.get("min_quantity") or 5,
        )
        return redirect("qur_product_list", slug=slug, tenant_id=tenant_id, category_id=category_id)

    return render(request, "start/qur_product_form.html", {
        "tenant": tenant, "product": None, "category_id": category_id, "units": QurilishProduct.UNIT_CHOICES,
    })


@login_required
def qur_product_edit(request, slug, tenant_id, category_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI)
    product = get_object_or_404(QurilishProduct, pk=pk, tenant=tenant)

    if request.method == "POST":
        product.name = request.POST.get("name", "").strip()
        product.barcode = request.POST.get("barcode", "").strip()
        product.unit = request.POST.get("unit", QurilishProduct.UNIT_PIECE)
        product.price = request.POST.get("price") or 0
        product.discount_price = request.POST.get("discount_price") or None
        product.quantity = request.POST.get("quantity") or 0
        product.min_quantity = request.POST.get("min_quantity") or 5
        product.save()
        return redirect("qur_product_list", slug=slug, tenant_id=tenant_id, category_id=category_id)

    return render(request, "start/qur_product_form.html", {
        "tenant": tenant, "product": product, "category_id": category_id, "units": QurilishProduct.UNIT_CHOICES,
    })


@login_required
def qur_product_delete(request, slug, tenant_id, category_id, pk):
    from django.db.models import ProtectedError

    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI)
    product = get_object_or_404(QurilishProduct, pk=pk, tenant=tenant)

    if request.method == "POST":
        try:
            product.delete()
        except ProtectedError:
            product.is_active = False
            product.save()
            return redirect(f"{_qur_product_list_url(slug, tenant_id, category_id)}?archived=1")
        return redirect("qur_product_list", slug=slug, tenant_id=tenant_id, category_id=category_id)

    return render(request, "start/qur_product_confirm_delete.html", {
        "tenant": tenant, "product": product, "category_id": category_id,
    })


def _qur_product_list_url(slug, tenant_id, category_id):
    from django.urls import reverse
    return reverse("qur_product_list", args=[slug, tenant_id, category_id])


@login_required
def qur_sale_category_list(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR)

    sale = _get_qur_open_sale(tenant, request.user)
    cart_items = sale.items.select_related("product")
    cart_count = cart_items.count()

    categories = []
    for c in QurilishCategory.objects.filter(tenant=tenant):
        categories.append({
            "id": c.id, "name": c.name,
            "count": QurilishProduct.objects.filter(category=c, is_active=True).count(),
        })
    uncategorized_count = QurilishProduct.objects.filter(
        tenant=tenant, category__isnull=True, is_active=True
    ).count()
    return render(request, "start/qur_sale_category_list.html", {
        "tenant": tenant, "categories": categories, "uncategorized_count": uncategorized_count,
        "sale": sale, "cart_items": cart_items, "cart_count": cart_count,
    })


def _get_qur_open_sale(tenant, user=None):
    """Tenant uchun ochiq savatni topadi, eski bosh savatlarni tozalaydi."""
    open_sales = list(QurilishSale.objects.filter(tenant=tenant, status="open").order_by("-created_at"))
    if not open_sales:
        return QurilishSale.objects.create(tenant=tenant, status="open", total_amount=0, created_by=user)

    sale = open_sales[0]
    for extra in open_sales[1:]:
        if not extra.items.exists():
            extra.delete()
    return sale


@login_required
def qur_sale_add_products(request, slug, tenant_id, category_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR)
    sale = _get_qur_open_sale(tenant, request.user)

    if category_id == 0:
        category = None
        products = QurilishProduct.objects.filter(tenant=tenant, category__isnull=True, is_active=True)
    else:
        category = get_object_or_404(QurilishCategory, pk=category_id, tenant=tenant)
        products = QurilishProduct.objects.filter(tenant=tenant, category=category, is_active=True)

    if request.method == "POST":
        added_total = 0

        for product in products:
            qty_str = request.POST.get(f"qty_{product.id}", "").strip()
            if not qty_str:
                continue
            try:
                qty = Decimal(qty_str)
            except InvalidOperation:
                continue
            if qty <= 0:
                continue

            qty = min(qty, product.quantity)
            if qty <= 0:
                continue

            unit_price = product.effective_price
            existing_item = QurilishSaleItem.objects.filter(sale=sale, product=product).first()
            if existing_item:
                existing_item.quantity += qty
                existing_item.save()
            else:
                QurilishSaleItem.objects.create(sale=sale, product=product, quantity=qty, unit_price=unit_price)

            product.quantity -= qty
            product.save()
            added_total += qty * unit_price

        sale.total_amount += added_total
        sale.save()
        return redirect("qur_sale_category_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/qur_sale_create.html", {
        "tenant": tenant, "category": category, "category_id": category_id, "products": products, "sale": sale,
    })


@login_required
def qur_sale_checkout(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR)
    sale = _get_qur_open_sale(tenant, request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "remove_item":
            item = get_object_or_404(QurilishSaleItem, pk=request.POST.get("item_id"), sale=sale)
            item.product.quantity += item.quantity
            item.product.save()
            sale.total_amount -= item.line_total
            sale.save()
            item.delete()
            return redirect("qur_sale_checkout", slug=slug, tenant_id=tenant_id)

        elif action == "finish":
            if sale.items.exists():
                sale.payment_method = request.POST.get("payment_method", "cash")
                sale.status = "completed"
                sale.save()
                return redirect("qur_sale_detail", slug=slug, tenant_id=tenant_id, pk=sale.id)

    items = sale.items.select_related("product")
    return render(request, "start/qur_sale_checkout.html", {"tenant": tenant, "sale": sale, "items": items})


@login_required
def qur_sale_list(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR, TenantUser.ROLE_MENEJER)

    today = timezone.now().date()
    selected_date = _parse_date_param(request, today)

    day_sales = QurilishSale.objects.filter(tenant=tenant, status="completed", created_at__date=selected_date)
    day_total = sum((s.total_amount or 0) for s in day_sales)

    return render(request, "start/qur_sale_list.html", {
        "tenant": tenant,
        "selected_date": selected_date,
        "prev_date": selected_date - timezone.timedelta(days=1),
        "next_date": selected_date + timezone.timedelta(days=1),
        "today": today,
        "day_sales": day_sales,
        "day_total": day_total,
    })


@login_required
def qur_sale_export(request, slug, tenant_id):
    """Tanlangan kundagi sotuvlarni Excel'da ochiladigan CSV korinishida yuklab olish."""
    import csv

    from django.http import HttpResponse

    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR, TenantUser.ROLE_MENEJER)

    today = timezone.now().date()
    selected_date = _parse_date_param(request, today)
    sales = QurilishSale.objects.filter(tenant=tenant, status="completed", created_at__date=selected_date)

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = f'attachment; filename="qur_sotuvlar_{selected_date.isoformat()}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Sana", "ID", "Tolov turi", "Summa"])
    for s in sales:
        writer.writerow([
            s.created_at.strftime("%d.%m.%Y %H:%M"),
            s.id,
            s.get_payment_method_display(),
            s.total_amount,
        ])

    return response


@login_required
def qur_sale_detail(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_KASSIR, TenantUser.ROLE_MENEJER)
    sale = get_object_or_404(QurilishSale, pk=pk, tenant=tenant)
    items = sale.items.select_related("product")
    return render(request, "start/qur_sale_detail.html", {"tenant": tenant, "sale": sale, "items": items})


@login_required
def qur_purchase_create(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OMBORCHI)
    products = QurilishProduct.objects.filter(tenant=tenant)

    if request.method == "POST":
        product = get_object_or_404(QurilishProduct, pk=request.POST.get("product"), tenant=tenant)
        qty = Decimal(request.POST.get("quantity") or 0)

        QurilishPurchase.objects.create(
            tenant=tenant,
            product=product,
            supplier=request.POST.get("supplier", "").strip(),
            quantity=qty,
            unit_cost=request.POST.get("unit_cost") or None,
            date=request.POST.get("date") or timezone.now().date(),
            note=request.POST.get("note", "").strip(),
        )
        product.quantity += qty
        product.save()
        return redirect("qur_category_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/qur_purchase_form.html", {"tenant": tenant, "products": products})


@login_required
def qur_report(request, slug, tenant_id):
    from datetime import datetime

    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_MENEJER)
    today = timezone.now().date()

    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        start_date = today.replace(day=1)
        end_date = today

    sales = QurilishSale.objects.filter(
        tenant=tenant, status="completed", created_at__date__gte=start_date, created_at__date__lte=end_date
    )
    sales_count = sales.count()
    total_revenue = sum((s.total_amount or 0) for s in sales)

    product_stats = (
        QurilishSaleItem.objects.filter(sale__in=sales)
        .values("product__name")
        .annotate(
            total_qty=models.Sum("quantity"),
            total_revenue=models.Sum(models.F("quantity") * models.F("unit_price")),
        )
        .order_by("-total_revenue")
    )

    stock = QurilishProduct.objects.filter(tenant=tenant).order_by("name")

    return render(request, "start/qur_report.html", {
        "tenant": tenant,
        "start_date": start_date,
        "end_date": end_date,
        "sales_count": sales_count,
        "total_revenue": total_revenue,
        "product_stats": product_stats,
        "stock": stock,
    })


# ---------- BOGCHA viewlari ----------

def _auto_assign_group(tenant, birth_date):
    """Tugilgan sanaga qarab yosh oralig'iga mos BogchaGroup'ni topadi."""
    today = timezone.now().date()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    for g in BogchaGroup.objects.filter(tenant=tenant):
        if g.min_age <= age <= g.max_age:
            return g
    return None


def bogcha_dashboard(request, tenant):
    today = timezone.now().date()
    children = Child.objects.filter(tenant=tenant)
    groups_count = BogchaGroup.objects.filter(tenant=tenant).count()

    logged_today = ChildDailyLog.objects.filter(tenant=tenant, date=today).count()
    not_logged_count = children.count() - logged_today

    unconfirmed_meals = MealLog.objects.filter(tenant=tenant, date=today, confirmed=False)

    return render(request, "start/bogcha_dashboard.html", {
        "tenant": tenant,
        "children_count": children.count(),
        "groups_count": groups_count,
        "logged_today": logged_today,
        "not_logged_count": not_logged_count,
        "unconfirmed_meals": unconfirmed_meals,
        "today": today,
    })


@login_required
def meal_confirm(request, slug, tenant_id, pk):
    """Tarbiyachi 'Ovqatni qabul qildim' deb tasdiqlaydi - oshpaz tomonida ham korinadi."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_TARBIYACHI)
    meal = get_object_or_404(MealLog, pk=pk, tenant=tenant)

    if request.method == "POST":
        meal.confirmed = True
        meal.confirmed_by = request.user
        meal.confirmed_at = timezone.now()
        meal.save()

    return redirect("tenant_dashboard", slug=slug, tenant_id=tenant_id)


@login_required
def child_list(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    query = request.GET.get("q", "").strip()
    children = Child.objects.filter(tenant=tenant).select_related("group")
    if query:
        children = children.filter(
            models.Q(full_name__icontains=query) | models.Q(phone__icontains=query)
        )
    return render(request, "start/child_list.html", {"tenant": tenant, "children": children, "query": query})


@login_required
def child_create(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user)  # faqat Admin/Direktor (super admin ham)
    groups = BogchaGroup.objects.filter(tenant=tenant)

    if request.method == "POST":
        from datetime import datetime
        birth_date = datetime.strptime(request.POST.get("birth_date"), "%Y-%m-%d").date()
        group_id = request.POST.get("group") or None

        child = Child.objects.create(
            tenant=tenant,
            group_id=group_id,
            full_name=request.POST.get("full_name", "").strip(),
            photo=request.FILES.get("photo"),
            id_document=request.POST.get("id_document", "").strip(),
            birth_date=birth_date,
            father_name=request.POST.get("father_name", "").strip(),
            father_id=request.POST.get("father_id", "").strip(),
            mother_name=request.POST.get("mother_name", "").strip(),
            mother_id=request.POST.get("mother_id", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            health_condition=request.POST.get("health_condition", "").strip(),
            note=request.POST.get("note", "").strip(),
        )

        if not group_id:
            auto_group = _auto_assign_group(tenant, child.birth_date)
            if auto_group:
                child.group = auto_group
                child.save()

        return redirect("child_detail", slug=slug, tenant_id=tenant_id, pk=child.id)

    return render(request, "start/child_form.html", {"tenant": tenant, "groups": groups, "child": None})


@login_required
def child_detail(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    child = get_object_or_404(Child, pk=pk, tenant=tenant)
    today = timezone.now().date()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_pickup":
            AuthorizedPickup.objects.create(
                child=child,
                full_name=request.POST.get("pickup_name", "").strip(),
                relation=request.POST.get("pickup_relation", "").strip(),
                phone=request.POST.get("pickup_phone", "").strip(),
            )
        elif action == "remove_pickup":
            AuthorizedPickup.objects.filter(id=request.POST.get("pickup_id"), child=child).delete()
        return redirect("child_detail", slug=slug, tenant_id=tenant_id, pk=pk)

    today_log = ChildDailyLog.objects.filter(tenant=tenant, child=child, date=today).first()
    daily_logs = child.daily_logs.all()[:14]
    pickup_logs = child.pickup_logs.all()[:14]
    authorized = child.authorized_pickups.all()

    return render(request, "start/child_detail.html", {
        "tenant": tenant, "child": child, "today_log": today_log,
        "daily_logs": daily_logs, "pickup_logs": pickup_logs, "authorized": authorized,
        "meal_choices": MealServing.MEAL_CHOICES, "today": today,
    })


@login_required
def child_edit(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user)
    child = get_object_or_404(Child, pk=pk, tenant=tenant)
    groups = BogchaGroup.objects.filter(tenant=tenant)

    if request.method == "POST":
        child.full_name = request.POST.get("full_name", "").strip()
        if request.FILES.get("photo"):
            child.photo = request.FILES.get("photo")
        child.id_document = request.POST.get("id_document", "").strip()
        from datetime import datetime
        child.birth_date = datetime.strptime(request.POST.get("birth_date"), "%Y-%m-%d").date()
        child.father_name = request.POST.get("father_name", "").strip()
        child.father_id = request.POST.get("father_id", "").strip()
        child.mother_name = request.POST.get("mother_name", "").strip()
        child.mother_id = request.POST.get("mother_id", "").strip()
        child.phone = request.POST.get("phone", "").strip()
        child.health_condition = request.POST.get("health_condition", "").strip()
        child.note = request.POST.get("note", "").strip()
        child.group_id = request.POST.get("group") or None
        child.save()
        return redirect("child_detail", slug=slug, tenant_id=tenant_id, pk=child.id)

    return render(request, "start/child_form.html", {"tenant": tenant, "groups": groups, "child": child})


@login_required
def child_delete(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user)
    child = get_object_or_404(Child, pk=pk, tenant=tenant)

    if request.method == "POST":
        child.delete()
        return redirect("child_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/child_confirm_delete.html", {"tenant": tenant, "child": child})


@login_required
def daily_log_create(request, slug, tenant_id, pk):
    """
    Tarbiyachi kelgan vaqt va sogligi haqida izohni kiritadi. Bir marta
    saqlangach BU YOZUVNI ozgartirish uchun hech qanday tugma/yol yoq.
    """
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_TARBIYACHI)
    child = get_object_or_404(Child, pk=pk, tenant=tenant)
    today = timezone.now().date()

    existing = ChildDailyLog.objects.filter(tenant=tenant, child=child, date=today).first()
    if existing:
        return redirect("child_detail", slug=slug, tenant_id=tenant_id, pk=pk)

    if request.method == "POST":
        health_note = request.POST.get("health_note", "").strip()
        if health_note:
            ChildDailyLog.objects.create(
                tenant=tenant, child=child, date=today,
                arrival_time=request.POST.get("arrival_time") or timezone.now().time(),
                health_note=health_note,
                recorded_by=request.user if hasattr(request.user, "tenant_id") else None,
            )
        return redirect("child_detail", slug=slug, tenant_id=tenant_id, pk=pk)

    return render(request, "start/daily_log_form.html", {"tenant": tenant, "child": child, "today": today})


@login_required
def meal_serving_toggle(request, slug, tenant_id, pk):
    """Tarbiyachi 'Qabul qildim' tugmasi - bitta ovqat turini shu kun uchun belgilaydi."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_TARBIYACHI)
    child = get_object_or_404(Child, pk=pk, tenant=tenant)

    if request.method == "POST":
        meal_type = request.POST.get("meal_type")
        MealServing.objects.get_or_create(
            tenant=tenant, child=child, date=timezone.now().date(), meal_type=meal_type,
            defaults={"served": True, "served_by": request.user},
        )

    return redirect("child_detail", slug=slug, tenant_id=tenant_id, pk=pk)


@login_required
def pickup_log_create(request, slug, tenant_id, pk):
    """Bola ketayotganda kim olib ketayotgani yoziladi."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_TARBIYACHI)
    child = get_object_or_404(Child, pk=pk, tenant=tenant)

    if request.method == "POST":
        PickupLog.objects.create(
            tenant=tenant, child=child,
            picked_up_by_name=request.POST.get("picked_up_by_name", "").strip(),
            relation=request.POST.get("relation", "other"),
            time=request.POST.get("time") or timezone.now().time(),
            recorded_by=request.user,
        )
        return redirect("child_detail", slug=slug, tenant_id=tenant_id, pk=pk)

    return render(request, "start/pickup_log_form.html", {"tenant": tenant, "child": child})


@login_required
def meal_log_create(request, slug, tenant_id):
    """Oshpaz hisoboti: shu kun uchun necha porsiya ovqat tayyorlangani."""
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user, TenantUser.ROLE_OSHBAZ)

    if request.method == "POST":
        MealLog.objects.update_or_create(
            tenant=tenant,
            date=request.POST.get("date") or timezone.now().date(),
            meal_type=request.POST.get("meal_type"),
            defaults={
                "portions_count": request.POST.get("portions_count") or 0,
                "note": request.POST.get("note", "").strip(),
                "recorded_by": request.user,
            },
        )
        return redirect("meal_log_create", slug=slug, tenant_id=tenant_id)

    today = timezone.now().date()
    recent = MealLog.objects.filter(tenant=tenant).order_by("-date")[:14]
    return render(request, "start/meal_log_form.html", {"tenant": tenant, "today": today, "recent": recent})


# ---------- BOGCHA guruh (BogchaGroup) CRUD ----------

@login_required
def bogcha_group_list(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    groups = BogchaGroup.objects.filter(tenant=tenant).select_related("tarbiyachi")
    return render(request, "start/bogcha_group_list.html", {"tenant": tenant, "groups": groups})


@login_required
def bogcha_group_create(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user)
    teachers = Teacher.objects.filter(tenant=tenant)

    if request.method == "POST":
        BogchaGroup.objects.create(
            tenant=tenant,
            name=request.POST.get("name", "").strip(),
            tarbiyachi_id=request.POST.get("tarbiyachi") or None,
            min_age=request.POST.get("min_age") or 0,
            max_age=request.POST.get("max_age") or 7,
        )
        return redirect("bogcha_group_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/bogcha_group_form.html", {"tenant": tenant, "teachers": teachers, "group": None})


@login_required
def bogcha_group_edit(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user)
    group = get_object_or_404(BogchaGroup, pk=pk, tenant=tenant)
    teachers = Teacher.objects.filter(tenant=tenant)

    if request.method == "POST":
        group.name = request.POST.get("name", "").strip()
        group.tarbiyachi_id = request.POST.get("tarbiyachi") or None
        group.min_age = request.POST.get("min_age") or 0
        group.max_age = request.POST.get("max_age") or 7
        group.save()
        return redirect("bogcha_group_detail", slug=slug, tenant_id=tenant_id, pk=group.id)

    return render(request, "start/bogcha_group_form.html", {"tenant": tenant, "teachers": teachers, "group": group})


@login_required
def bogcha_group_delete(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    _require_role(request.user)
    group = get_object_or_404(BogchaGroup, pk=pk, tenant=tenant)

    if request.method == "POST":
        group.delete()  # Child.group SET_NULL, bolalar ochirilmaydi
        return redirect("bogcha_group_list", slug=slug, tenant_id=tenant_id)

    return render(request, "start/bogcha_group_confirm_delete.html", {"tenant": tenant, "group": group})


@login_required
def bogcha_group_detail(request, slug, tenant_id, pk):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    group = get_object_or_404(BogchaGroup, pk=pk, tenant=tenant)
    children = Child.objects.filter(tenant=tenant, group=group)
    return render(request, "start/bogcha_group_detail.html", {
        "tenant": tenant, "group": group, "children": children,
    })


def permission_denied_view(request, exception=None):
    """
    Ruxsat rad etilganda (PermissionDenied) standart Django 403 sahifasi
    orniga chiroyli, tushunarli xabar korsatadi.
    """
    message = str(exception) if exception else "Sizning rolingiz bu amal uchun ruxsat berilmagan."
    return render(request, "start/access_denied.html", {"message": message}, status=403)



@login_required
def audit_log_list(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)
    logs = AuditLog.objects.filter(tenant=tenant)[:100]
    return render(request, "start/audit_log_list.html", {"tenant": tenant, "logs": logs})





@login_required
def gugurt_dashboard(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)

    # Faqat GUGURT moduli uchun
    if tenant.category.module_type != Category.MODULE_GUGURT:
        raise PermissionDenied(
            "Bu tenant Gugurt moduliga tegishli emas."
        )

    # Subscription tekshirish
    if not _is_super_admin(request.user):
        subscription = getattr(tenant, "subscription", None)

        if not subscription or not subscription.is_valid:
            return HttpResponse(
                """
                <div style="
                    max-width:600px;
                    margin:100px auto;
                    padding:40px;
                    text-align:center;
                    font-family:Arial;
                    border-radius:20px;
                    box-shadow:0 10px 40px rgba(0,0,0,.1);
                ">
                    <h1>🔒 Obuna muddati tugagan</h1>

                    <p>
                        Ushbu Gugurt biznes modulidan foydalanish uchun
                        obunani yangilang.
                    </p>

                    <a href="/dashboard/"
                       style="
                       display:inline-block;
                       padding:12px 25px;
                       background:#111;
                       color:white;
                       text-decoration:none;
                       border-radius:10px;
                       ">
                       Dashboardga qaytish
                    </a>
                </div>
                """,
                status=403,
            )

    # =========================
    # MAHSULOTLAR
    # =========================

    products = GugurtProduct.objects.filter(
        tenant=tenant,
        is_active=True,
    )

    # =========================
    # IMPORT PARTIYALAR
    # =========================

    batches = GugurtImportBatch.objects.filter(
        tenant=tenant
    ).select_related("product").order_by(
        "-import_date",
        "-id"
    )

    # =========================
    # 12 TA VILOYAT
    # =========================

    existing_regions = set(
        GugurtRegion.objects.filter(
            tenant=tenant
        ).values_list(
            "name",
            flat=True
        )
    )

    for code, name in GugurtRegion.REGION_CHOICES:

        if code not in existing_regions:
            GugurtRegion.objects.create(
                tenant=tenant,
                name=code,
            )

    regions = GugurtRegion.objects.filter(
        tenant=tenant
    ).order_by("name")

    # =========================
    # DEALERLAR
    # =========================

    dealers = GugurtDealer.objects.filter(
        tenant=tenant,
        is_active=True,
    ).select_related("region")

    # =========================
    # TARQATISHLAR
    # =========================

    distributions = GugurtDistribution.objects.filter(
        tenant=tenant
    ).select_related(
        "batch",
        "batch__product",
        "dealer",
        "dealer__region",
    ).order_by(
        "-dispatch_date",
        "-id"
    )

    # =========================
    # UMUMIY OMBOR
    # =========================

    total_stock_kg = sum(
        (
            product.stock_kg
            for product in products
        ),
        Decimal("0")
    )

    # =========================
    # JAMI IMPORT
    # =========================

    total_import_kg = sum(
        (
            batch.quantity_kg
            for batch in batches
        ),
        Decimal("0")
    )

    # =========================
    # JAMI TARQATILGAN
    # =========================

    total_distribution_kg = sum(
        (
            distribution.quantity_kg
            for distribution in distributions
            if distribution.status in [
                "sent",
                "received"
            ]
        ),
        Decimal("0")
    )

    # =========================
    # VILOYATLAR STATISTIKASI
    # =========================

    region_stats = []

    for region in regions:

        distributions_region = distributions.filter(
            dealer__region=region,
            status__in=[
                "sent",
                "received"
            ],
        )

        sent_kg = sum(
            (
                item.quantity_kg
                for item in distributions_region
            ),
            Decimal("0")
        )

        dealer_count_region = dealers.filter(
            region=region
        ).count()

        region_stats.append({
            "region": region,
            "name": region.get_name_display(),
            "kg": sent_kg,
            "tonna": sent_kg / Decimal("1000"),
            "dealer_count": dealer_count_region,
        })

    # =========================
    # CONTEXT
    # =========================

    context = {
        "tenant": tenant,

        "products": products,
        "batches": batches,
        "regions": regions,
        "dealers": dealers,
        "distributions": distributions,

        # Ombor
        "total_stock_kg": total_stock_kg,
        "total_stock_tonna": (
            total_stock_kg / Decimal("1000")
        ),

        # Import
        "total_import_kg": total_import_kg,
        "total_import_tonna": (
            total_import_kg / Decimal("1000")
        ),

        # Tarqatish
        "total_distribution_kg": total_distribution_kg,
        "total_distribution_tonna": (
            total_distribution_kg / Decimal("1000")
        ),

        # Dealer
        "dealer_count": dealers.count(),

        # Viloyatlar
        "region_stats": region_stats,
    }

    return render(
        request,
        "start/gugurt_dashboard.html",
        context,
    )



def gugurt_import_create(request, slug, tenant_id):
    tenant = _get_accessible_tenant(request, slug, tenant_id)

    # Faqat GUGURT moduli
    if tenant.category.module_type != Category.MODULE_GUGURT:
        raise PermissionDenied("Bu sahifa GUGURT moduli uchun.")

    # Super admin subscriptionga qaramaydi
    if not _is_super_admin(request.user):
        subscription = getattr(tenant, "subscription", None)

        if not subscription or not subscription.is_valid:
            return HttpResponse(
                """
                <div style="
                    max-width:600px;
                    margin:100px auto;
                    text-align:center;
                    font-family:Arial;
                ">
                    <h1>🔒 Obuna tugagan</h1>
                    <p>Ushbu tenant uchun aktiv obuna mavjud emas.</p>
                </div>
                """,
                status=403,
            )

    if request.method == "POST":
        form = GugurtImportForm(
            request.POST,
            tenant=tenant
        )

        if form.is_valid():

            with transaction.atomic():

                # Mahsulotni tenant bo‘yicha tekshiramiz
                product_id = form.cleaned_data["product"].id

                product = get_object_or_404(
                    GugurtProduct.objects.select_for_update(),
                    id=product_id,
                    tenant=tenant,
                    is_active=True,
                )

                quantity_kg = form.cleaned_data["quantity_kg"]

                # Import batch yaratish
                batch = GugurtImportBatch(
                    tenant=tenant,
                    product=product,
                    batch_number=form.cleaned_data["batch_number"],
                    country=form.cleaned_data["country"],
                    quantity_kg=quantity_kg,
                    product_cost=form.cleaned_data["product_cost"],
                    transport_cost=form.cleaned_data["transport_cost"],
                    customs_cost=form.cleaned_data["customs_cost"],
                    other_cost=form.cleaned_data["other_cost"],
                    import_date=form.cleaned_data["import_date"],
                    note=form.cleaned_data["note"],
                )

                batch.save()

                # Omborga qo‘shish
                product.stock_kg += quantity_kg
                product.save(update_fields=["stock_kg"])

            messages.success(
                request,
                f"{quantity_kg:,.2f} kg mahsulot omborga qo‘shildi."
            )

            return redirect(
                "gugurt_dashboard",
                slug=tenant.category.slug,
                tenant_id=tenant.id,
            )

    else:
        form = GugurtImportForm(
            tenant=tenant
        )

    return render(
        request,
        "start/gugurt_import.html",
        {
            "tenant": tenant,
            "form": form,
        }
    )



def gugurt_dealer_create(request, slug, tenant_id):

    tenant = _get_accessible_tenant(
        request,
        slug,
        tenant_id
    )

    if tenant.category.module_type != Category.MODULE_GUGURT:
        raise PermissionDenied(
            "Bu sahifa GUGURT moduli uchun."
        )

    if request.method == "POST":

        form = GugurtDealerForm(
            request.POST,
            tenant=tenant
        )

        if form.is_valid():

            dealer = form.save(commit=False)

            dealer.tenant = tenant

            dealer.save()

            messages.success(
                request,
                f"{dealer.name} muvaffaqiyatli qo‘shildi."
            )

            return redirect(
                "gugurt_dealers",
                slug=tenant.category.slug,
                tenant_id=tenant.id,
            )

    else:

        form = GugurtDealerForm(
            tenant=tenant
        )

    return render(
        request,
        "start/gugurt_dealer_form.html",
        {
            "tenant": tenant,
            "form": form,
        }
    )
def gugurt_dealers(request, slug, tenant_id):

    tenant = _get_accessible_tenant(
        request,
        slug,
        tenant_id
    )

    if tenant.category.module_type != Category.MODULE_GUGURT:
        raise PermissionDenied(
            "Bu sahifa GUGURT moduli uchun."
        )

    dealers = GugurtDealer.objects.filter(
        tenant=tenant
    ).select_related(
        "region"
    ).order_by("-id")

    return render(
        request,
        "start/gugurt_dealers.html",
        {
            "tenant": tenant,
            "dealers": dealers,
        }
    )

def gugurt_distribution_create(request, slug, tenant_id):

    tenant = _get_accessible_tenant(
        request,
        slug,
        tenant_id
    )

    if tenant.category.module_type != Category.MODULE_GUGURT:
        raise PermissionDenied(
            "Bu sahifa GUGURT moduli uchun."
        )

    # Subscription
    if not _is_super_admin(request.user):

        subscription = getattr(
            tenant,
            "subscription",
            None
        )

        if not subscription or not subscription.is_valid:

            return HttpResponse(
                """
                <div style="
                    max-width:600px;
                    margin:100px auto;
                    text-align:center;
                    font-family:Arial;
                ">
                    <h1>🔒 Obuna tugagan</h1>
                    <p>
                        Ushbu tenant uchun
                        aktiv obuna mavjud emas.
                    </p>
                </div>
                """,
                status=403
            )

    if request.method == "POST":

        form = GugurtDistributionForm(
            request.POST,
            tenant=tenant
        )

        if form.is_valid():

            batch_id = form.cleaned_data["batch"].id
            dealer_id = form.cleaned_data["dealer"].id
            quantity_kg = form.cleaned_data["quantity_kg"]

            with transaction.atomic():

                # Partiyani bloklaymiz
                batch = get_object_or_404(
                    GugurtImportBatch.objects.select_for_update(),
                    id=batch_id,
                    tenant=tenant,
                )

                # Mahsulotni bloklaymiz
                product = get_object_or_404(
                    GugurtProduct.objects.select_for_update(),
                    id=batch.product_id,
                    tenant=tenant,
                    is_active=True,
                )

                # Dealerni tekshiramiz
                dealer = get_object_or_404(
                    GugurtDealer,
                    id=dealer_id,
                    tenant=tenant,
                    is_active=True,
                )

                # Omborda yetarli mahsulot bormi?
                if quantity_kg > product.stock_kg:

                    form.add_error(
                        "quantity_kg",
                        (
                            f"Omborda yetarli mahsulot yo‘q. "
                            f"Qoldiq: {product.stock_kg} kg."
                        )
                    )

                else:

                    # Shu batchdan oldin qancha yuborilgan?
                    already_sent = sum(
                        (
                            item.quantity_kg
                            for item in
                            GugurtDistribution.objects.filter(
                                batch=batch,
                                status__in=[
                                    "sent",
                                    "received",
                                ]
                            )
                        ),
                        Decimal("0")
                    )

                    batch_remaining = (
                        batch.quantity_kg -
                        already_sent
                    )

                    # Partiyada yetarli mahsulot bormi?
                    if quantity_kg > batch_remaining:

                        form.add_error(
                            "quantity_kg",
                            (
                                f"Bu partiyada faqat "
                                f"{batch_remaining} kg "
                                f"qolgan."
                            )
                        )

                    else:

                        distribution = form.save(
                            commit=False
                        )

                        distribution.tenant = tenant
                        distribution.batch = batch
                        distribution.dealer = dealer

                        distribution.save()

                        # Faqat yuborilgan/qabul qilingan
                        # statuslarda ombor kamayadi
                        if distribution.status in [
                            "sent",
                            "received",
                        ]:

                            product.stock_kg -= quantity_kg

                            product.save(
                                update_fields=[
                                    "stock_kg"
                                ]
                            )

                        messages.success(
                            request,
                            (
                                f"{quantity_kg:,.2f} kg "
                                f"{dealer.name} dealeriga "
                                f"yuborildi."
                            )
                        )

                        return redirect(
                            "gugurt_dashboard",
                            slug=tenant.category.slug,
                            tenant_id=tenant.id,
                        )

    else:

        form = GugurtDistributionForm(
            tenant=tenant
        )

    return render(
        request,
        "start/gugurt_distribution_form.html",
        {
            "tenant": tenant,
            "form": form,
        }
    )










# prorab qurilishlari

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Tenant, ConstructionSite, ConstructionMaterial, MaterialReceipt, MaterialConsumption

# 1. Qurilish Ob'yektlari va Materiallar Balansi (Qoldig'i)
@login_required
def qurilish_sites_list(request, slug='main', tenant_id=1):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    sites = ConstructionSite.objects.filter(tenant=tenant)
    materials = ConstructionMaterial.objects.filter(tenant=tenant)

    context = {
        'sites': sites,
        'materials': materials,
        'slug': slug,
        'tenant_id': tenant_id,
        'user_name': request.user.first_name or request.user.username,
    }
    return render(request, 'dashboard/qurilish/sites_list.html', context)


# 2. Material Kirimi (Prarab/Ta'minotchi ob'yektga yuk kelganda kiritadi)
@login_required
def material_receipt_create(request, slug='main', tenant_id=1):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    sites = ConstructionSite.objects.filter(tenant=tenant)
    materials = ConstructionMaterial.objects.filter(tenant=tenant)

    if request.method == 'POST':
        site_id = request.POST.get('site_id')
        material_id = request.POST.get('material_id')
        quantity = request.POST.get('quantity')
        supplier_name = request.POST.get('supplier_name')
        date = request.POST.get('date')
        note = request.POST.get('note')

        if site_id and material_id and quantity:
            MaterialReceipt.objects.create(
                tenant=tenant,
                site_id=site_id,
                material_id=material_id,
                quantity=quantity,
                supplier_name=supplier_name,
                date=date,
                note=note
            )
            return redirect('qurilish_sites_list', slug=slug, tenant_id=tenant_id)

    context = {
        'sites': sites,
        'materials': materials,
        'slug': slug,
        'tenant_id': tenant_id,
    }
    return render(request, 'dashboard/qurilish/receipt_create.html', context)


# 3. Material Chiqimi (Prarab ob'yektda qancha ishlatganini kiritadi)
@login_required
def material_consumption_create(request, slug='main', tenant_id=1):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    sites = ConstructionSite.objects.filter(tenant=tenant)
    materials = ConstructionMaterial.objects.filter(tenant=tenant)

    if request.method == 'POST':
        site_id = request.POST.get('site_id')
        material_id = request.POST.get('material_id')
        quantity = request.POST.get('quantity')
        date = request.POST.get('date')
        used_for = request.POST.get('used_for')

        if site_id and material_id and quantity:
            MaterialConsumption.objects.create(
                tenant=tenant,
                site_id=site_id,
                material_id=material_id,
                quantity=quantity,
                date=date,
                used_for=used_for,
                prarab_name=request.user.get_full_name() or request.user.username
            )
            return redirect('qurilish_sites_list', slug=slug, tenant_id=tenant_id)

    context = {
        'sites': sites,
        'materials': materials,
        'slug': slug,
        'tenant_id': tenant_id,
    }
    return render(request, 'dashboard/qurilish/consumption_create.html', context)







@login_required
def qurilish_pro_dashboard(request, slug='main', tenant_id=1):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    sites = ConstructionSite.objects.filter(tenant=tenant)
    materials = ConstructionMaterial.objects.filter(tenant=tenant)
    
    # Oxirgi kirim va chiqimlar
    recent_receipts = MaterialReceipt.objects.filter(tenant=tenant).order_by('-date')[:5]
    recent_consumptions = MaterialConsumption.objects.filter(tenant=tenant).order_by('-date')[:5]

    context = {
        'tenant': tenant,
        'slug': slug,
        'tenant_id': tenant_id,
        'sites': sites,
        'materials': materials,
        'recent_receipts': recent_receipts,
        'recent_consumptions': recent_consumptions,
        'user_name': request.user.first_name or request.user.username,
    }
    return render(request, 'dashboard/qurilish/dashboard.html', context)



@login_required
def qurilish_site_create(request, slug='main', tenant_id=1):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        
        if name:
            ConstructionSite.objects.create(
                tenant=tenant,
                name=name,
                address=address
            )
            return redirect('qurilish_sites_list', slug=slug, tenant_id=tenant_id)
            
    context = {
        'slug': slug,
        'tenant_id': tenant_id,
    }
    return render(request, 'dashboard/qurilish/site_create.html', context)



@login_required
def qurilish_material_create(request, slug='main', tenant_id=1):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        unit = request.POST.get('unit', 'kg') # o'lchov birligi (kg, tonna, dona, metr va h.k.)
        
        if name:
            ConstructionMaterial.objects.create(
                tenant=tenant,
                name=name,
                unit=unit
            )
            return redirect('qurilish_sites_list', slug=slug, tenant_id=tenant_id)
            
    context = {
        'slug': slug,
        'tenant_id': tenant_id,
    }
    return render(request, 'dashboard/qurilish/material_create.html', context)


@login_required
def qurilish_site_detail(request, slug='main', tenant_id=1, pk=1):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    site = get_object_or_404(ConstructionSite, id=pk, tenant=tenant)
    
    # Shu ob'yektga tegishli kirim va chiqimlar
    receipts = MaterialReceipt.objects.filter(site=site, tenant=tenant).order_by('-date')
    consumptions = MaterialConsumption.objects.filter(site=site, tenant=tenant).order_by('-date')
    
    context = {
        'slug': slug,
        'tenant_id': tenant_id,
        'tenant': tenant,
        'site': site,
        'receipts': receipts,
        'consumptions': consumptions,
    }
    return render(request, 'dashboard/qurilish/site_detail.html', context)