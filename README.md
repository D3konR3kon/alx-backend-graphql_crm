# ALX Backend GraphQL CRM

A Django-based Customer Relationship Management (CRM) system with GraphQL API integration.

## Features

- **Customer Management**: Create and manage customer records with validation
- **Product Catalog**: Manage products with pricing and inventory
- **Order Processing**: Create orders linking customers and products
- **GraphQL API**: Full CRUD operations through GraphQL mutations and queries
- **Bulk Operations**: Support for bulk customer creation
- **Data Validation**: Comprehensive input validation and error handling

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone and setup the project**
```bash
git clone <your-repo-url>
cd alx-backend-graphql_crm
```

2. **Create virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install django graphene-django django-filter
```

4. **Run migrations**
```bash
python manage.py makemigrations crm
python manage.py migrate
```

5. **Start the server**
```bash
python manage.py runserver
```

6. **Access GraphQL interface**
Open http://127.0.0.1:8000/graphql/ in your browser

## API Usage

### Create a Customer
```graphql
mutation {
  createCustomer(input: {
    name: "John Doe",
    email: "john@example.com",
    phone: "+1234567890"
  }) {
    customer {
      id
      name
      email
    }
    message
    errors
  }
}
```

### Create a Product
```graphql
mutation {
  createProduct(input: {
    name: "Laptop",
    price: 999.99,
    stock: 10
  }) {
    product {
      id
      name
      price
    }
    errors
  }
}
```

### Create an Order
```graphql
mutation {
  createOrder(input: {
    customerId: "1",
    productIds: ["1", "2"]
  }) {
    order {
      id
      totalAmount
      customer {
        name
      }
      products {
        name
        price
      }
    }
    errors
  }
}
```

### Query Data
```graphql
query {
  customers {
    id
    name
    email
    orders {
      id
      totalAmount
    }
  }
}
```

## Project Structure

```
alx-backend-graphql_crm/
├── alx-backend-graphql_crm/
│   ├── settings.py
│   ├── urls.py
│   └── schema.py           # Main GraphQL schema
├── crm/
│   ├── models.py           # Customer, Product, Order models
│   ├── schema.py           # CRM GraphQL mutations and queries
│   └── ...
├── manage.py
└── requirements.txt
```

## Models

- **Customer**: Name, email (unique), phone (optional)
- **Product**: Name, price, stock quantity
- **Order**: Customer reference, multiple products, auto-calculated total

## Validation Features

- Email uniqueness and format validation
- Phone number format validation
- Price and stock validation
- Comprehensive error messages
- Transaction safety for bulk operations

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Superuser
```bash
python manage.py createsuperuser
```

### Admin Interface
Access Django admin at http://127.0.0.1:8000/admin/

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.