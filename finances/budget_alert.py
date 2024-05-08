# budget_alerts.py
from django.core.mail import send_mail
from .models import Category
from users.models import User 
from services.models import Transaction # Assuming user details are stored in the 'users' app

def send_budget_alert(email, category_name):
    subject = 'Budget Exceeded Alert'
    message = f"Dear User,\n\nThe budget for category '{category_name}' has been exceeded."
    sender_email = 'ntpjc2vinayak@gmail.com'  # Update with your sender email
    recipient_list = [email]
    send_mail(subject, message, sender_email, recipient_list)

def monitor_budget():
    categories = Category.objects.all()
    for category in categories:
        transactions = Transaction.objects.filter(category=category)
        total_spending = sum(transaction.amount for transaction in transactions)
        if total_spending > category.budget:
            send_budget_alert(category.user.email, category.name)

