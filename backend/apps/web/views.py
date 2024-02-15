from django.db.models import Count, Sum
from django.shortcuts import render
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from apps.web.exceptions import *
from apps.web.serializer import *
from .models import *
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from django.db.models import F
from .permissions import IsAdminUserOrReadOnly

User = get_user_model()


class UserRegistrationCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny, ]


class LoginAPIView(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'is_staff': user.is_staff
            }, status=status.HTTP_200_OK)
        else:
            raise InvalidCredentialsException("Incorrect credentials, please try again.")


class UserProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(quantity__gt=0)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super(UserProductListView, self).get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_queryset(self):
        if self.request.user.is_staff:
            return Product.objects.all()
        return Product.objects.exclude(quantity=0)


class UserProductDetail(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        # Corrected to reference UserProductDetail instead of UserProductListView
        context = super(UserProductDetail, self).get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_queryset(self):
        if self.request.user.is_staff:
            return Product.objects.all()
        return Product.objects.exclude(quantity=0)


class UserOrdersList(generics.ListAPIView):
    serializer_class = OrderSerializer  # Define this to include necessary fields
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user_id=self.request.user)  # .exclude(order_status='Canceled')
        # return Order.objects.filter().exclude(order_status='Canceled')


class OrderDetail(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user_id=self.request.user)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        # Directly use 'pk' from self.kwargs as it matches the URL conf
        filter_kwargs = {self.lookup_field: self.kwargs.get('pk')}
        obj = generics.get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class PurchaseView(views.APIView):  # create order
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        items = request.data.get('items', [])  # Expected format: [{'product_id': 1, 'quantity': 2}, ...]
        order = Order.objects.create(user_id=self.request.user, order_status='Processing')
        try:
            for item in items:
                product = Product.objects.get(id=item['product_id'])
                if item['quantity'] > product.quantity:
                    raise NotEnoughInventoryException('Not enough stock for product_id {}'.format(item['product_id']))
                product.quantity -= item['quantity']
                product.save()
                OrderItem.objects.create(order_id=order, product_id=product, quantity=item['quantity'],
                                         purchase_price=product.retail_price, wholesale_price=product.wholesale_price)
        except Product.DoesNotExist:
            order.delete()  # Rollback the order creation if any product does not exist
            return Response({'error': 'Product does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        except NotEnoughInventoryException as e:
            order.delete()  # Rollback the order creation if not enough inventory
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Order created successfully'}, status=status.HTTP_201_CREATED)


class CancelOrderView(views.APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        try:
            order = Order.objects.get(id=order_id)
            # order = Order.objects.get(id=order_id, user_id_id=request.user.id)

            # Check if the request user is the one who placed the order or is a superuser
            if order.user_id_id != request.user.id and not request.user.is_superuser:
                return Response({'error': 'You do not have permission to cancel this order'},
                                status=status.HTTP_403_FORBIDDEN)

            # Check if the order is already completed or canceled
            if order.order_status.lower() == 'completed':
                return Response({'error': 'Completed orders cannot be canceled'}, status=status.HTTP_400_BAD_REQUEST)
            elif order.order_status.lower() == 'canceled':
                return Response({'error': 'Order has already been canceled'}, status=status.HTTP_400_BAD_REQUEST)

            order.order_status = 'Canceled'
            order.save()

            # Increment stock for each item in the order
            for item in order.orderitem_order.all():
                item.product_id.quantity += item.quantity
                item.product_id.save()

            return Response({'message': 'Order canceled successfully'}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order does not exist', 'order_id': order_id}, status=status.HTTP_404_NOT_FOUND)


class AddToWatchListView(generics.CreateAPIView):
    queryset = WatchList.objects.all()
    serializer_class = WatchListSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user)


class RemoveFromWatchListView(generics.DestroyAPIView):
    queryset = WatchList.objects.all()
    serializer_class = WatchListSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        product_id = self.kwargs.get('product_id')
        watchlist_item = generics.get_object_or_404(WatchList, user_id=self.request.user, product_id=product_id)
        return watchlist_item


class WatchListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        watchlist_product_ids = WatchList.objects.filter(user_id=self.request.user).values_list('product_id', flat=True)
        return Product.objects.filter(id__in=watchlist_product_ids, quantity__gt=0)


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


class TopRecentPurchasedItemsList(generics.ListAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(
            order_id__user_id=self.request.user
        ).exclude(
            order_id__order_status='Canceled'
        ).order_by('-order_id__data_placed', 'id')[:3]


'''
Admin: Seller
'''


class SmallSetPagination(PageNumberPagination):
    page_size = 5


class OrderListView(generics.ListAPIView):
    queryset = Order.objects.all().order_by('-data_placed')
    serializer_class = OrderSerializer
    pagination_class = SmallSetPagination
    permission_classes = [IsAdminUser]


# order details refers to orderView in user block


class ProductCreateAPIView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save()


class UpdateOrderStatusView(generics.UpdateAPIView):  # complete the order
    queryset = Order.objects.all()
    serializer_class = UpdateOrderStatusSerializer
    permission_classes = [IsAdminUser]

    def perform_update(self, serializer):
        order = serializer.instance
        new_status = serializer.validated_data.get('order_status')

        if order.order_status == 'Canceled' and new_status == 'Completed':
            raise ValidationException('Canceled orders cannot be completed.')
        elif order.order_status == 'Completed' and new_status == 'Canceled':
            raise ValidationException('Completed orders cannot be canceled.')

        if new_status == 'Canceled':
            # Increment product stock
            for item in order.orderitem_set.all():
                item.product.quantity += item.quantity
                item.product.save()
        serializer.save()


class MostProfitableProductView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Product.objects.annotate(profit=F('retail_price') - F('wholesale_price')).order_by('-profit')[:1]


class TopSoldProductsView(generics.ListAPIView):
    serializer_class = TopSoldProductSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return OrderItem.objects.exclude(order_id__order_status__in=['Canceled', 'Processing']) \
                   .values('product_id', 'product_id__name') \
                   .annotate(total_sold=Sum('quantity')) \
                   .order_by('-total_sold')[:3]


class TotalItemsSoldView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Aggregate total sold items for each product excluding 'Canceled' or 'Processing' orders
        total_items_sold_per_product = OrderItem.objects.exclude(
            order_id__order_status__in=['Canceled', 'Processing']
        ).values(
            'product_id', 'product_id__name'
        ).annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')

        return Response({"total_items_sold": list(total_items_sold_per_product)})


class ProductDetailView(generics.RetrieveUpdateAPIView):  # Edit product
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

    def put(self, request, *args, **kwargs):
        try:
            product_instance = self.get_object()
            serializer = self.get_serializer(product_instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)