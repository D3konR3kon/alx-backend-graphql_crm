#!/usr/bin/env python3

"""
Order Reminders Script
Queries GraphQL endpoint for pending orders within the last week and logs reminders.
"""

import os
import sys
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def main():

    GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
    LOG_FILE = "/tmp/order_reminders_log.txt"
    

    seven_days_ago = datetime.now() - timedelta(days=7)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:

        transport = RequestsHTTPTransport(url=GRAPHQL_ENDPOINT)
        client = Client(transport=transport, fetch_schema_from_transport=True)
        

        query = gql("""
            query {
                allOrders {
                    id
                    status
                    createdAt
                    customer {
                        id
                        email
                    }
                }
            }
        """)
        

        result = client.execute(query)
        

        pending_orders = []
        for order in result['allOrders']:
            order_date = datetime.fromisoformat(order['createdAt'].replace('Z', '+00:00'))
            

            if (order['status'] == 'pending' and 
                order_date >= seven_days_ago.replace(tzinfo=order_date.tzinfo)):
                pending_orders.append(order)
        
 
        with open(LOG_FILE, 'a') as log:
            log.write(f"[{timestamp}] Order reminders check started\n")
            
            if pending_orders:
                for order in pending_orders:
                    order_id = order['id']
                    customer_email = order['customer']['email']
                    log.write(f"[{timestamp}] Order ID: {order_id}, Customer Email: {customer_email}\n")
                
                log.write(f"[{timestamp}] Found {len(pending_orders)} pending orders requiring reminders\n")
            else:
                log.write(f"[{timestamp}] No pending orders found requiring reminders\n")
            
            log.write(f"[{timestamp}] Order reminders check completed\n")
        
   
        print("Order reminders processed!")
        
    except Exception as e:

        with open(LOG_FILE, 'a') as log:
            log.write(f"[{timestamp}] ERROR: {str(e)}\n")
        
        print(f"Error processing order reminders: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()