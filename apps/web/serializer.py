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
        # Remove 'wholesale_price' if the user is not an admin
        request = self.context.get('request')
        if not request.user.is_staff:
            ret.pop('wholesale_price', None)
        return ret


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')

    class Meta:
        model = OrderItem
        fields = ('product_name', 'quantity', 'purchase_price')


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
