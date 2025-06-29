import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from decimal import Decimal
from datetime import datetime
import re

from .models import Customer, Product, Order

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False, default_value=0)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True
    phone_pattern = r'^\+?1?\d{9,15}$|^\d{3}-\d{3}-\d{4}$'
    return bool(re.match(phone_pattern, phone))

def validate_customer_data(name, email, phone=None):
    """Validate customer data and return errors"""
    errors = []
    
    if not name or not name.strip():
        errors.append("Name is required")
    
    if not email:
        errors.append("Email is required")
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Invalid email format")
    
    if phone and not validate_phone(phone):
        errors.append("Invalid phone format. Use +1234567890 or 123-456-7890")
    
    return errors

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        validation_errors = validate_customer_data(
            input.name, input.email, input.get('phone')
        )

        if validation_errors:
            return CreateCustomer(errors=validation_errors)
        

        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(errors=["Email already exists"])
        
        try:
            customer = Customer.objects.create(
                name=input.name.strip(),
                email=input.email.lower().strip(),
                phone=input.get('phone', '').strip() if input.get('phone') else None
            )
            return CreateCustomer(
                customer=customer,
                message="Customer created successfully"
            )
        except Exception as e:
            return CreateCustomer(errors=[f"Failed to create customer: {str(e)}"])

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)
    
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        successful_customers = []
        all_errors = []
        
        with transaction.atomic():
            for i, customer_data in enumerate(input):
                try:
                    # Validate each customer
                    validation_errors = validate_customer_data(
                        customer_data.name, 
                        customer_data.email, 
                        customer_data.get('phone')
                    )
                    
                    if validation_errors:
                        all_errors.extend([f"Customer {i+1}: {error}" for error in validation_errors])
                        continue
                    

                    if Customer.objects.filter(email=customer_data.email).exists():
                        all_errors.append(f"Customer {i+1}: Email already exists")
                        continue
                    

                    customer = Customer.objects.create(
                        name=customer_data.name.strip(),
                        email=customer_data.email.lower().strip(),
                        phone=customer_data.get('phone', '').strip() if customer_data.get('phone') else None
                    )
                    successful_customers.append(customer)
                    
                except Exception as e:
                    all_errors.append(f"Customer {i+1}: {str(e)}")
        
        return BulkCreateCustomers(
            customers=successful_customers,
            errors=all_errors
        )

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    
    product = graphene.Field(ProductType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        errors = []

        if not input.name or not input.name.strip():
            errors.append("Product name is required")
        
        if input.price is None or input.price <= 0:
            errors.append("Price must be positive")
        
        if input.stock is not None and input.stock < 0:
            errors.append("Stock cannot be negative")
        
        if errors:
            return CreateProduct(errors=errors)
        
        try:
            product = Product.objects.create(
                name=input.name.strip(),
                price=Decimal(str(input.price)),
                stock=input.stock if input.stock is not None else 0
            )
            return CreateProduct(product=product)
        except Exception as e:
            return CreateProduct(errors=[f"Failed to create product: {str(e)}"])

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    
    order = graphene.Field(OrderType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        errors = []

        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            errors.append("Customer not found")
            return CreateOrder(errors=errors)
        
        # Validate products exist
        if not input.product_ids:
            errors.append("At least one product must be selected")
            return CreateOrder(errors=errors)
        
        products = Product.objects.filter(id__in=input.product_ids)
        if len(products) != len(input.product_ids):
            found_ids = set(str(p.id) for p in products)
            missing_ids = set(input.product_ids) - found_ids
            errors.append(f"Invalid product IDs: {', '.join(missing_ids)}")
            return CreateOrder(errors=errors)
        
        try:
            with transaction.atomic():

                total_amount = sum(product.price for product in products)
                

                order = Order.objects.create(
                    customer=customer,
                    total_amount=total_amount,
                    order_date=input.order_date or datetime.now()
                )
                
                order.products.set(products)
                
                return CreateOrder(order=order)
                
        except Exception as e:
            return CreateOrder(errors=[f"Failed to create order: {str(e)}"])

class Query(graphene.ObjectType):
    hello = graphene.String()
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)  
    orders = graphene.List(OrderType)
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    
    def resolve_hello(self, info):
        return "Hello, GraphQL!"
    
    def resolve_customers(self, info):
        return Customer.objects.all()
    
    def resolve_products(self, info):
        return Product.objects.all()
    
    def resolve_orders(self, info):
        return Order.objects.all()
    
    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None
    
    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()