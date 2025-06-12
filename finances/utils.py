import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

def send_budget_alert_email(user, category, overspent_amount):
    """
    Send a budget alert email to the user when they exceed their budget.
    
    Args:
        user: User object
        category: Category name
        overspent_amount: Amount by which the budget was exceeded
    """
    subject = 'Budget Alert: Overspending Detected'
    
    # Create email context
    context = {
        'username': user.username,
        'category': category,
        'overspent_amount': overspent_amount,
        'budget_period': 'last 30 days'
    }
    
    # Render email template
    html_message = render_to_string('finances/email/budget_alert.html', context)
    plain_message = render_to_string('finances/email/budget_alert.txt', context)
    
    # Send email using Django's email backend
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False
    )

def send_transaction_notification(user, transaction):
    """
    Send a notification email when a new transaction is created.
    
    Args:
        user: User object
        transaction: Transaction object
    """
    subject = f'New Transaction: {transaction.type.title()}'
    
    # Create email context
    context = {
        'username': user.username,
        'transaction': transaction,
        'amount': transaction.amount,
        'category': transaction.category,
        'date': transaction.date
    }
    
    # Render email template
    html_message = render_to_string('finances/email/transaction_notification.html', context)
    plain_message = render_to_string('finances/email/transaction_notification.txt', context)
    
    # Send email using Django's email backend
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False
    ) 