from django.db.models import F
from django.utils import timezone

from .models import Payment, Product, Tenant


def notifications(request):
    """
    Har bir sahifada navbar uchun ogohlantirishlar sonini hisoblaydi:
    kam qolgan mahsulotlar (POS/Qurilish) + tolov muddati otgan/bugungi
    tolovlar (CRM/Bogcha). Faqat tenant ichidagi sahifalarda ishlaydi
    (URL da tenant_id bolganda).
    """
    resolver = getattr(request, "resolver_match", None)
    if not resolver:
        return {}

    tenant_id = resolver.kwargs.get("tenant_id")
    if not tenant_id:
        return {}

    try:
        tenant = Tenant.objects.get(pk=tenant_id)
    except Tenant.DoesNotExist:
        return {}

    count = 0

    # Kam qolgan mahsulotlar (qoldiq <= minimal qoldiq)
    count += Product.objects.filter(
        tenant=tenant, is_active=True, quantity__lte=F("min_quantity")
    ).count()

    # Tolov muddati otgan yoki bugun tugaydigan tolovlar
    today = timezone.now().date()
    count += Payment.objects.filter(tenant=tenant, is_paid=False, due_date__lte=today).count()

    return {"notif_count": count}