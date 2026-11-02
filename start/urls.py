from django.contrib.auth import views as auth_views
from django.urls import path

from . import views 

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    path("gome/", views.home_redirect, name="home_redirect"),
    path("dashboard/", views.dashboard_categories, name="dashboard_categories"),
    path("dashboard/<slug:slug>/", views.category_tenants, name="category_tenants"),
    path("dashboard/<slug:slug>/<int:tenant_id>/", views.tenant_dashboard, name="tenant_dashboard"),

    # Oquvchilar
    path("dashboard/<slug:slug>/<int:tenant_id>/students/", views.tenant_students, name="tenant_students"),
    path("dashboard/<slug:slug>/<int:tenant_id>/students/add/", views.tenant_student_create, name="tenant_student_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/students/<int:pk>/", views.tenant_student_detail, name="tenant_student_detail"),
    path("dashboard/<slug:slug>/<int:tenant_id>/students/<int:pk>/edit/", views.tenant_student_edit, name="tenant_student_edit"),
    path("dashboard/<slug:slug>/<int:tenant_id>/students/<int:pk>/delete/", views.tenant_student_delete, name="tenant_student_delete"),
    path("dashboard/<slug:slug>/<int:tenant_id>/students/<int:pk>/payments/add/", views.student_payment_create, name="student_payment_create"),

    # Davomat
    path("dashboard/<slug:slug>/<int:tenant_id>/attendance/", views.tenant_attendance_today, name="tenant_attendance_today"),
    path("dashboard/<slug:slug>/<int:tenant_id>/attendance/report/", views.attendance_report, name="attendance_report"),
    path("dashboard/<slug:slug>/<int:tenant_id>/attendance/report/<int:student_id>/edit/", views.attendance_quick_edit, name="attendance_quick_edit"),
    path("dashboard/<slug:slug>/<int:tenant_id>/groups/<int:group_id>/attendance/", views.group_attendance, name="group_attendance"),

    # Ustozlar
    path("dashboard/<slug:slug>/<int:tenant_id>/teachers/", views.teacher_list, name="teacher_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/teachers/add/", views.teacher_create, name="teacher_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/teachers/<int:pk>/", views.teacher_detail, name="teacher_detail"),
    path("dashboard/<slug:slug>/<int:tenant_id>/teachers/<int:pk>/edit/", views.teacher_edit, name="teacher_edit"),
    path("dashboard/<slug:slug>/<int:tenant_id>/teachers/<int:pk>/delete/", views.teacher_delete, name="teacher_delete"),

    # Guruhlar
    path("dashboard/<slug:slug>/<int:tenant_id>/groups/", views.group_list, name="group_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/groups/add/", views.group_create, name="group_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/groups/<int:pk>/", views.group_detail, name="group_detail"),
    path("dashboard/<slug:slug>/<int:tenant_id>/groups/<int:pk>/edit/", views.group_edit, name="group_edit"),
    path("dashboard/<slug:slug>/<int:tenant_id>/groups/<int:pk>/delete/", views.group_delete, name="group_delete"),

    # Tolovlar
    path("dashboard/<slug:slug>/<int:tenant_id>/payments/", views.payment_list, name="payment_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/payments/add/", views.payment_create, name="payment_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/payments/<int:pk>/toggle/", views.payment_mark_paid, name="payment_mark_paid"),
    path("dashboard/<slug:slug>/<int:tenant_id>/payments/<int:pk>/delete/", views.payment_delete, name="payment_delete"),
    path("dashboard/<slug:slug>/<int:tenant_id>/payments/report/", views.payment_report, name="payment_report"),
    path("dashboard/<slug:slug>/<int:tenant_id>/schedule/", views.schedule_view, name="schedule_view"),
    path("dashboard/<slug:slug>/<int:tenant_id>/finance/", views.financial_report, name="financial_report"),
    path("dashboard/<slug:slug>/<int:tenant_id>/finance/expense/add/", views.add_expense, name="add_expense"),

    # POS (dokon)
    path("dashboard/<slug:slug>/<int:tenant_id>/products/", views.product_category_list, name="product_category_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/products/categories/add/", views.product_category_create, name="product_category_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/products/<int:category_id>/", views.product_list, name="product_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/products/<int:category_id>/add/", views.product_create, name="product_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/products/<int:category_id>/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("dashboard/<slug:slug>/<int:tenant_id>/products/<int:category_id>/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("dashboard/<slug:slug>/<int:tenant_id>/sales/", views.sale_list, name="sale_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/sales/export/", views.sale_export, name="sale_export"),
    path("dashboard/<slug:slug>/<int:tenant_id>/sales/new/", views.sale_category_list, name="sale_category_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/sales/new/<int:category_id>/", views.sale_add_products, name="sale_add_products"),
    path("dashboard/<slug:slug>/<int:tenant_id>/sales/checkout/", views.sale_checkout, name="sale_checkout"),
    path("dashboard/<slug:slug>/<int:tenant_id>/sales/<int:pk>/", views.sale_detail, name="sale_detail"),
    path("dashboard/<slug:slug>/<int:tenant_id>/purchases/add/", views.purchase_create, name="purchase_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/pos-report/", views.pos_report, name="pos_report"),

    # Xodimlar (rollar)
    path("dashboard/<slug:slug>/<int:tenant_id>/staff/", views.staff_list, name="staff_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/staff/add/", views.staff_create, name="staff_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/staff/<int:pk>/edit/", views.staff_edit, name="staff_edit"),

    # QUR (qurilish mollari)
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/products/", views.qur_category_list, name="qur_category_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/products/categories/add/", views.qur_category_create, name="qur_category_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/products/<int:category_id>/", views.qur_product_list, name="qur_product_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/products/<int:category_id>/add/", views.qur_product_create, name="qur_product_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/products/<int:category_id>/<int:pk>/edit/", views.qur_product_edit, name="qur_product_edit"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/products/<int:category_id>/<int:pk>/delete/", views.qur_product_delete, name="qur_product_delete"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/sales/", views.qur_sale_list, name="qur_sale_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/sales/export/", views.qur_sale_export, name="qur_sale_export"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/sales/new/", views.qur_sale_category_list, name="qur_sale_category_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/sales/new/<int:category_id>/", views.qur_sale_add_products, name="qur_sale_add_products"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/sales/checkout/", views.qur_sale_checkout, name="qur_sale_checkout"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/sales/<int:pk>/", views.qur_sale_detail, name="qur_sale_detail"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/purchases/add/", views.qur_purchase_create, name="qur_purchase_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qur/report/", views.qur_report, name="qur_report"),

    # BOGCHA
    path("dashboard/<slug:slug>/<int:tenant_id>/children/", views.child_list, name="child_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/children/add/", views.child_create, name="child_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/children/<int:pk>/", views.child_detail, name="child_detail"),
    path("dashboard/<slug:slug>/<int:tenant_id>/children/<int:pk>/edit/", views.child_edit, name="child_edit"),
    path("dashboard/<slug:slug>/<int:tenant_id>/children/<int:pk>/delete/", views.child_delete, name="child_delete"),
    path("dashboard/<slug:slug>/<int:tenant_id>/children/<int:pk>/daily-log/", views.daily_log_create, name="daily_log_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/children/<int:pk>/meal/", views.meal_serving_toggle, name="meal_serving_toggle"),
    path("dashboard/<slug:slug>/<int:tenant_id>/children/<int:pk>/pickup/", views.pickup_log_create, name="pickup_log_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/meal-log/", views.meal_log_create, name="meal_log_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/meal-log/<int:pk>/confirm/", views.meal_confirm, name="meal_confirm"),

    # BOGCHA guruh
    path("dashboard/<slug:slug>/<int:tenant_id>/bogcha-groups/", views.bogcha_group_list, name="bogcha_group_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/bogcha-groups/add/", views.bogcha_group_create, name="bogcha_group_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/bogcha-groups/<int:pk>/", views.bogcha_group_detail, name="bogcha_group_detail"),
    path("dashboard/<slug:slug>/<int:tenant_id>/bogcha-groups/<int:pk>/edit/", views.bogcha_group_edit, name="bogcha_group_edit"),
    path("dashboard/<slug:slug>/<int:tenant_id>/bogcha-groups/<int:pk>/delete/", views.bogcha_group_delete, name="bogcha_group_delete"),
    path("dashboard/<slug:slug>/<int:tenant_id>/audit-log/", views.audit_log_list, name="audit_log_list"),


    path('dashboard12/<slug:slug>/<int:tenant_id>/tenants/', views.tenant_list, name='tenant_list'),
    path('dashboard12/<slug:slug>/<int:tenant_id>/tenants/create/', views.tenant_create, name='tenant_create'),




    path(
        "dashboard/<slug:slug>/<int:tenant_id>/gugurt/",
        views.gugurt_dashboard,
        name="gugurt_dashboard",
    ),


    path(
        "dashboard/<slug:slug>/<int:tenant_id>/gugurt/import/",
        views.gugurt_import_create,
        name="gugurt_import_create",
    ),

    path(
        "dashboard/<slug:slug>/<int:tenant_id>/gugurt/dealers/",
        views.gugurt_dealers,
        name="gugurt_dealers",
    ),

    path(
        "dashboard/<slug:slug>/<int:tenant_id>/gugurt/dealers/add/",
        views.gugurt_dealer_create,
        name="gugurt_dealer_create",
    ),

    

    path(
        "dashboard/<slug:slug>/<int:tenant_id>/gugurt/distribution/add/",
        views.gugurt_distribution_create,
        name="gugurt_distribution_create",
    ),




    # Qurilish logistikasi va Prarablar modullari
    path("dashboard/<slug:slug>/<int:tenant_id>/qurilish/sites/", views.qurilish_sites_list, name="qurilish_sites_list"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qurilish/receipt/add/", views.material_receipt_create, name="material_receipt_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qurilish/consumption/add/", views.material_consumption_create, name="material_consumption_create"),


    path("dashboard/<slug:slug>/<int:tenant_id>/qurilish/", views.qurilish_pro_dashboard, name="qurilish_dashboard"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qurilish/sites/add/", views.qurilish_site_create, name="qurilish_site_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qurilish/materials/add/", views.qurilish_material_create, name="qurilish_material_create"),
    path("dashboard/<slug:slug>/<int:tenant_id>/qurilish/sites/<int:pk>/", views.qurilish_site_detail, name="qurilish_site_detail"),
]