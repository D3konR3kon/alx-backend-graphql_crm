"""
Django-crontab job functions for CRM application heartbeat monitoring.
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
    
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
        import django
        django.setup()
    
    log_file = '/tmp/crm_heartbeat_log.txt'
    
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    heartbeat_msg = f"{timestamp} CRM is alive"

    graphql_status = test_graphql_endpoint()

    if graphql_status:
        log_message = f"{heartbeat_msg} - GraphQL endpoint responsive\n"
    else:
        log_message = f"{heartbeat_msg} - GraphQL endpoint unresponsive\n"

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