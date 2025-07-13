"""
Django-crontab job functions for CRM application heartbeat monitoring and stock management.
"""

import os
import sys
from datetime import datetime
from django.conf import settings

# Add the project directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def log_crm_heartbeat():
    """
    Log a heartbeat message to confirm CRM application health.
    Runs every 5 minutes via django-crontab.
    
    Logs format: DD/MM/YYYY-HH:MM:SS CRM is alive
    Also queries GraphQL hello field to verify endpoint responsiveness.
    """
    
    # Configure Django settings if not already configured
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
        import django
        django.setup()
    
    # Log file path
    log_file = '/tmp/crm_heartbeat_log.txt'
    
    # Format current timestamp as DD/MM/YYYY-HH:MM:SS
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    # Base heartbeat message
    heartbeat_msg = f"{timestamp} CRM is alive"
    
    # Test GraphQL endpoint responsiveness
    graphql_status = test_graphql_endpoint()
    
    # Prepare log message with GraphQL status
    if graphql_status:
        log_message = f"{heartbeat_msg} - GraphQL endpoint responsive\n"
    else:
        log_message = f"{heartbeat_msg} - GraphQL endpoint unresponsive\n"
    
    # Append to log file
    try:
        with open(log_file, 'a') as f:
            f.write(log_message)
    except Exception as e:
        # If logging fails, try to write to stderr
        sys.stderr.write(f"Failed to write heartbeat log: {str(e)}\n")

def test_graphql_endpoint():
    """
    Test GraphQL endpoint responsiveness by querying the hello field.
    Returns True if endpoint is responsive, False otherwise.
    """
    try:

        from gql import gql, Client
        from gql.transport.requests import RequestsHTTPTransport
        

        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            timeout=10  # 10 second timeout
        )
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
    
        query = gql("""
            query {
                hello
            }
        """)
        

        result = client.execute(query)
        
        if result and 'hello' in result:
            return True
        else:
            return False
            
    except Exception as e:

        error_msg = f"{datetime.now().strftime('%d/%m/%Y-%H:%M:%S')} GraphQL test error: {str(e)}\n"
        try:
            with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
                f.write(error_msg)
        except:
            pass  
        return False

def update_low_stock():
    """
    Update low stock products using GraphQL mutation.
    Runs every 12 hours via django-crontab.
    
    Executes UpdateLowStockProducts mutation and logs results.
    """
    

    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
        import django
        django.setup()
    

    log_file = '/tmp/low_stock_updates_log.txt'
    

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        from gql import gql, Client
        from gql.transport.requests import RequestsHTTPTransport
        
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            timeout=30  # 30 second timeout
        )
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
        mutation = gql("""
            mutation {
                updateLowStockProducts {
                    success
                    message
                    updatedCount
                    updatedProducts {
                        id
                        name
                        stock
                        sku
                    }
                }
            }
        """)
        
        result = client.execute(mutation)
        
        mutation_result = result['updateLowStockProducts']
        

        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] Low stock update job started\n")
            
            if mutation_result['success']:
                f.write(f"[{timestamp}] {mutation_result['message']}\n")
                f.write(f"[{timestamp}] Updated {mutation_result['updatedCount']} products\n")
                
                for product in mutation_result['updatedProducts']:
                    product_name = product['name']
                    new_stock = product['stock']
                    product_sku = product['sku']
                    f.write(f"[{timestamp}] Product: {product_name} (SKU: {product_sku}) - New stock: {new_stock}\n")
                    
            else:
                f.write(f"[{timestamp}] ERROR: {mutation_result['message']}\n")
            
            f.write(f"[{timestamp}] Low stock update job completed\n")
        
    except Exception as e:
        error_msg = f"[{timestamp}] CRITICAL ERROR: Failed to update low stock products - {str(e)}\n"
        try:
            with open(log_file, 'a') as f:
                f.write(error_msg)
        except:

            sys.stderr.write(error_msg)


def update_low_stock_direct():
    """
    Direct database version of low stock update without GraphQL.
    Use this as a fallback if GraphQL endpoint is unavailable.
    """

    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
        import django
        django.setup()
    
    from myapp.models import Product
    
    log_file = '/tmp/low_stock_updates_log.txt'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:

        low_stock_products = Product.objects.filter(stock__lt=10)
        
        updated_products = []
        

        for product in low_stock_products:
            old_stock = product.stock
            product.stock += 10
            product.save()
            updated_products.append(product)
        

        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] Low stock update job started (direct database)\n")
            f.write(f"[{timestamp}] Updated {len(updated_products)} products\n")
            
            for product in updated_products:
                f.write(f"[{timestamp}] Product: {product.name} (SKU: {product.sku}) - New stock: {product.stock}\n")
            
            f.write(f"[{timestamp}] Low stock update job completed\n")
            
    except Exception as e:
        error_msg = f"[{timestamp}] ERROR: Direct database update failed - {str(e)}\n"
        try:
            with open(log_file, 'a') as f:
                f.write(error_msg)
        except:
            sys.stderr.write(error_msg)


def log_crm_heartbeat_simple():
    """
    Simple version of heartbeat logging without GraphQL testing.
    Use this if GraphQL testing is not required.
    """
    log_file = '/tmp/crm_heartbeat_log.txt'
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    log_message = f"{timestamp} CRM is alive\n"
    
    try:
        with open(log_file, 'a') as f:
            f.write(log_message)
    except Exception as e:
        sys.stderr.write(f"Failed to write heartbeat log: {str(e)}\n")