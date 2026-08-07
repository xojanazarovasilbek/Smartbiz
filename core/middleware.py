from django.http import JsonResponse


class TenantSubscriptionMiddleware:
    """
    Har bir so'rovda foydalanuvchining tenant obunasi faolligini tekshiradi.
    Muddat tugasa (masalan 30 kun), 402 xato bilan kirishni to'xtatadi.
    Super admin / superuser bu tekshiruvdan chetlab o'tadi.

    settings.py dagi MIDDLEWARE royxatiga qoshish kerak:
        "core.middleware.TenantSubscriptionMiddleware",
    (AuthenticationMiddleware dan keyin turishi shart, chunki request.user kerak)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            is_super = user.is_superuser or getattr(user, "is_super_admin", False)

            if not is_super:
                tenant = getattr(user, "tenant", None)
                subscription = getattr(tenant, "subscription", None) if tenant else None

                if not subscription or not subscription.is_valid:
                    return JsonResponse(
                        {"error": "Obuna muddati tugagan. Iltimos tolovni yangilang."},
                        status=402,
                    )

        return self.get_response(request)