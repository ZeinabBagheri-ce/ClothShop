from decimal import Decimal
from products.models import ProductVariation

CART_SESSION_ID = "cart"

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if cart is None:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def save(self):
        self.session.modified = True

    def add(self, variation_id: int, quantity: int = 1, replace: bool = False):
        vid = str(variation_id)
        if vid not in self.cart:
            self.cart[vid] = {"quantity": 0}
        self.cart[vid]["quantity"] = quantity if replace else self.cart[vid]["quantity"] + quantity
        if self.cart[vid]["quantity"] <= 0:
            self.remove(vid)
        self.save()

    def remove(self, variation_id):
        vid = str(variation_id)
        if vid in self.cart:
            del self.cart[vid]
            self.save()

    def clear(self):
        self.session[CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        ids = [int(vid) for vid in self.cart.keys()]
        variations = ProductVariation.objects.select_related("product", "color", "size").filter(id__in=ids)
        vmap = {v.id: v for v in variations}
        for vid, item in self.cart.items():
            v = vmap.get(int(vid))
            if not v:
                continue
            qty = int(item["quantity"])
            price = v.final_price
            yield {
                "variation": v,
                "product": v.product,
                "price": price,
                "quantity": qty,
                "total": price * qty,
            }

    def total_quantity(self):
        return sum(int(i["quantity"]) for i in self.cart.values())

    def total_price(self):
        total = Decimal("0")
        for row in self:
            total += row["total"]
        return total
