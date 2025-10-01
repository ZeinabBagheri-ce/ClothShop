from .cart import Cart


def cart_summary(request):
    cart = Cart(request)
    return {"cart_count": cart.total_quantity(), "cart_total": cart.total_price()}
