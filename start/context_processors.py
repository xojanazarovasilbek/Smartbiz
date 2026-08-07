from django.utils import timezone
from .models import Product, Payment


def notifications(request):
    """Har bir sahifada navbar uchun ogohlantirishlar sonini hisoblaydi."""
    tenant = getattr(request, "resolver_match", None)
    # Eng oson yol - request ichida tenant borligini view orqali emas,
    # url parametrlaridan olamiz:
    if not request.resolver_match:
        return {}

    kwargs = request.resolver_match.kwargs
    tenant_id = kwargs.get("tenant_id")
    if not tenant_id:
        return {}

    from .models import Tenant
    try:
        tenant = Tenant.objects.get(pk=tenant_id)
    except Tenant.DoesNotExist:
        return {}

    count = 0
    if hasattr(tenant, "products"):
        count += Product.objects.filter(tenant=tenant, is_active=True, quantity__lte=5).count()

    today = timezone.now().date()
    count += Payment.objects.filter(tenant=tenant, is_paid=False, due_date__lte=today).count()

    return {"notif_count": count}