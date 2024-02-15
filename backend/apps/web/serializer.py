from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'quantity', 'retail_price', 'wholesale_price']

    def get_profit(self, obj):
        return obj.retail_price - obj.wholesale_price

    def to_representation(self, instance):
        # Call the superclass method to get the original representation
        ret = super(ProductSerializer, self).to_representation(instance)
        # Conditionally remove fields for non-staff users
        if not self.context.get('request').user.is_staff:
            ret.pop('wholesale_price', None)
            ret.pop('quantity', None)  # Ensure the quantity is not visible to non-staff users
        return ret


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(source='product_id')

    class Meta:
        model = OrderItem
        fields = ('id', 'quantity', 'purchase_price', 'product')


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(source='orderitem_order', many=True)
    user_username = serializers.CharField(source='user_id.username')

    class Meta:
        model = Order
        fields = ('id', 'data_placed', 'order_status', 'user_username', 'order_items')


class WatchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchList
        fields = ['product_id']


class UpdateOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_status']

    def validate_order_status(self, value):
        if self.instance.order_status == 'Canceled' and value == 'Completed':
            raise serializers.ValidationError("A canceled order cannot be marked as completed.")
        if self.instance.order_status == 'Completed' and value == 'Canceled':
            raise serializers.ValidationError("A completed order cannot be canceled.")
        return value


class TopSoldProductSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField(source='product_id__name')
    total_sold = serializers.IntegerField()

    def to_representation(self, instance):
        # Custom representation logic if needed
        return super().to_representation(instance)