from decimal import Decimal

REMOTE_PROVINCES = {"سیستان و بلوچستان", "کهگیلویه و بویراحمد", "ایلام", "خراسان جنوبی"}


def calc_shipping(subtotal: Decimal, province_name: str) -> Decimal:
    if subtotal >= Decimal("1200000"):
        return Decimal("0")
    base = Decimal("45000")
    if province_name in REMOTE_PROVINCES:
        base = (base * Decimal("1.2")).quantize(Decimal("1."))
    return base
