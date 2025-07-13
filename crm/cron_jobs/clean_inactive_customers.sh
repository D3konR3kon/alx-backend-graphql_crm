#!/bin/bash

# Customer cleanup script - removes inactive customers with no orders in the last year
# Usage: ./clean_inactive_customers.sh


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/customer_cleanup_log.txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')


cwd=$(pwd)


cd "$SCRIPT_DIR/.."


if [ -f "manage.py" ]; then
    DELETED_COUNT=$(python manage.py shell -c "
from django.utils import timezone
from datetime import timedelta
from myapp.models import Customer, Order

# Calculate date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders in the last year
inactive_customers = Customer.objects.exclude(
    id__in=Order.objects.filter(
        created_at__gte=one_year_ago
    ).values_list('customer_id', flat=True)
)

# Count and delete inactive customers
count = inactive_customers.count()
inactive_customers.delete()

print(count)
")
    
    echo "[$TIMESTAMP] Deleted $DELETED_COUNT inactive customers" >> "$LOG_FILE"
else

    echo "[$TIMESTAMP] ERROR: manage.py not found in current directory" >> "$LOG_FILE"
    exit 1
fi

exit 0