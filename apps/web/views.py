from django.db.models import Count, Sum
from django.shortcuts import render
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate
from apps.web.exceptions import InvalidCredentialsException
from apps.web.serializer import *
from .models import *
from django.db import transaction
from .exceptions import NotEnoughInventoryException
from rest_framework.pagination import PageNumberPagination
from .permissions import IsAdminUserOrReadOnly
from django.db.models import F

User = get_user_model()


class UserRegistrationCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer


class LoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Proceed to login or generate a token
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        else:
            raise InvalidCredentialsException("Incorrect credentials, please try again.")


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(quantity__gt=0)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super(ProductListView, self).get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_queryset(self):
        if self.request.user.is_staff:
            return Product.objects.all()
        return Product.objects.exclude(quantity=0)


class ProductDetail(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_context(self):
        context = super(ProductListView, self).get_serializer_context()
        context.update({"request": self.request})
        return context


class OrderDetail(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def get_object(self):
        queryset = self.get_queryset()
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}
        obj = generics.get_object_or_404(queryset, **filter_kwargs)
        return obj


class PurchaseView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        items = request.data.get('items', [])  # Expected format: [{'product_id': 1, 'quantity': 2}, ...]
        order = Order.objects.create(user=request.user, order_status='Processing')
        try:
            for item in items:
                product = Product.objects.get(id=item['product_id'])
                if item['quantity'] > product.quantity:
                    raise NotEnoughInventoryException('Not enough stock for product_id {}'.format(item['product_id']))
                product.quantity -= item['quantity']
                product.save()
                OrderItem.objects.create(order=order, product=product, quantity=item['quantity'])
        except Product.DoesNotExist:
            order.delete()  # Rollback the order creation if any product does not exist
            return Response({'error': 'Product does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        except NotEnoughInventoryException as e:
            order.delete()  # Rollback the order creation if not enough inventory
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Order created successfully'}, status=status.HTTP_201_CREATED)


class CancelOrderView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            if order.order_status == 'Completed':
                return Response({'error': 'Completed orders cannot be canceled'}, status=status.HTTP_400_BAD_REQUEST)
            order.order_status = 'Canceled'
            order.save()
            for item in order.orderitem_set.all():
                item.product.quantity += item.quantity
                item.product.save()
            return Response({'message': 'Order canceled successfully'}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order does not exist'}, status=status.HTTP_404_NOT_FOUND)


class AddToWatchListView(generics.CreateAPIView):
    queryset = WatchList.objects.all()
    serializer_class = WatchListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user)


class RemoveFromWatchListView(generics.DestroyAPIView):
    queryset = WatchList.objects.all()
    serializer_class = WatchListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        product_id = self.kwargs.get('product_id')
        watchlist_item = generics.get_object_or_404(WatchList, user_id=self.request.user, product_id=product_id)
        return watchlist_item


class WatchListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(watched_users=self.request.user, quantity__gt=0)


class UserOrdersList(generics.ListAPIView):
    serializer_class = OrderSerializer  # Define this to include necessary fields

    def get_queryset(self):
        return Order.objects.filter(user_id=self.request.user).exclude(order_status='Canceled')


class TopFrequentlyPurchasedItemsList(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user
        return Product.objects.filter(
            orderitem_product__order_id__user_id=user,
            orderitem_product__order_id__order_status__in=['Processing', 'Completed']
        ).annotate(
            total_purchased=Count('orderitem_product')
        ).order_by('-total_purchased')[:3]



'''
Admin: Seller
'''


class SmallSetPagination(PageNumberPagination):
    page_size = 5


class OrderListView(generics.ListAPIView):
    queryset = Order.objects.all().order_by('-data_placed')
    serializer_class = OrderSerializer
    pagination_class = SmallSetPagination
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]

# order details refers to orderView in user block


class ProductCreateAPIView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save()


class UpdateOrderStatusView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = UpdateOrderStatusSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        order = serializer.instance
        new_status = serializer.validated_data.get('order_status')

        if order.order_status == 'Canceled' and new_status == 'Completed':
            raise ValidationError('Canceled orders cannot be completed.')
        elif order.order_status == 'Completed' and new_status == 'Canceled':
            raise ValidationError('Completed orders cannot be canceled.')

        if new_status.lower() == 'canceled':
            # Increment product stock
            for item in order.orderitem_set.all():
                item.product.quantity += item.quantity
                item.product.save()
        serializer.save()


class MostProfitableProductView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.annotate(profit=F('retail_price') - F('wholesale_price')).order_by('-profit')[:1]


class TopSoldProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        # Filter OrderItems by excluding canceled and processing orders, then annotate and order by sold quantity
        return OrderItem.objects.exclude(order__order_status__in=['Canceled', 'Processing']).values('product__id', 'product__name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:3]


class TotalItemsSoldView(APIView):
    def get(self, request, *args, **kwargs):
        total_items_sold = OrderItem.objects.exclude(order__order_status__in=['Canceled', 'Processing']).aggregate(total_sold=Sum('quantity'))['total_sold'] or 0
        return Response({"total_items_sold": total_items_sold})
