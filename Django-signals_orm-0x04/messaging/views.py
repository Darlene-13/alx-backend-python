from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required   # Decorator that forces users to be logged in before they can acess views
from django.contrib.auth import logout
from django.contrib import messages #Provides a way to send one time messages,,,eg success, info, warning....etc
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import requires_http_methods
from django.views.decorators.crsf import crsf_protect  # A decorator to enforce CSRF protection (Cross-Site Request Forgery).
from django.db import transaction   # Allows you to group several database operations as a transaction
from .models import Message, Notification, MessageHistory
import logging


logger = logging.getLogger(__name__)
@login_required
def delete_user_account(request):
    """
    View to handle user account deletion.
    """
    user = request.user

    if request.method == 'GET':
        # Show confirmation page with user's data summary
        context = get_user_data_summary(user)
        return render(request, 'messaging/delete_ccount.html', context)

    elif request.method == 'POST':
        return handle_user_deletion(request, user)
    
    def get_user_data_summary(user):
        """
        Get a summary of all the data that will be deleted with the user account"""

        # Count all related data
        sent_messages = Message.objects.filter(sender = user).count()
        received_messages = Message.objects.filter(receiver=user).count()
        notifications = Notification.objects.filter(user = user).count()
        message_histories = MessageHistory.objects.filter(user=user).count()

        return {
            'user': user,
            'sent_messages_count': sent_messages,
            'received_messages_count': received_messages,
            'notifications_count': notifications,
            'message_histories_count': message_histories,
            'total_data_points': sent_messages + received_messages + notifications + message_histories,

        }
    
@transaction.atomic
def handle_user_deletion(request, user):
    """
    Handle the actual user account deletion processs"""
    
    try:

        logger.info(f"User deletion initiated for the user: {user.username} (ID: {user.id})")

        #Get data summary before deletion for logging
        data_summary = get_user_data_summary(user)

        # Check if the user  is trying to delete their own account
        if request.user.id != user.id:
            messages.error(request, "You can only delete your own account")
            return redirect ('messaging: delete_account_confirm') #Otherwise redirect the user if they are actually deleting their own account
        
        # Store username for success message (since the usr object will be deleted)
        username = user.username

        # Delete the user and this should trigger the post delete signal to handle data clean up
        user.delete()

        # Log successful deletion

        logger.info(
            f"User '{username}' successfully deleted"
            f"Cleaned up: {data_summary['total_data_points']} related records"
        )

        #Log out the user since  their acccount no longer exists
        logout(request)

        # Add success message
        messages.success(
            request,
            f"Account '{username} has been successfully deleted."
            f" All your data ({data_summary['total_data_points']} records) has been removed"
        )

        # Check if this is an AJAX request
        if request.header.get('X-Request-With') == 'XMLHttpRequest':
            return JsonResponse({
                    'success': True,
                    'message': f"Account '{username}' has been successfully deleted",
                    'redirect_url': '/'
            })
        
        # Redirect the user to home login page
        return redirect ('login')
    
    except Exception as e:

        logger.error(f"Error deleting user {user.username}: {str(e)}")


        #Add error message
        messages.error(
            request,
            f" An error occurred while deleting your account: {str(e)}"
        )

        # Check if this is an AJAX Request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        
        # Redirect to the confirmation page
        return redirect ('messaging : delete_account_confirm')
    

@login_required
@requires_http_methods(["POST"])
@crsf_protect
def delete_user_ajax(request):
    #AJAX endpoint for account deletion

    try:
        user = request.user
        username = user.username

        # Get data summary before deletion
        data_summary = get_user_data_summary(user)

        # Delete the user
        user.delete()

        # logout the user
        logout(request)

        return JsonResponse({
            'success': True,
            'message': f"Account '{username} deleted successfully.",
            'data_cleaned': data_summary['total_data_points'],
            'redirect_url': '/'
        })
    except Exception as e:
        logger.error(f"AJAX useer deletion error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
@login_required
def user_data_summary(request):
    """
    View to show user's data summary without deletion
    Useful for showing what wuld be deleted"""

    user = request.useer
    context = get_user_data_summary(user)

    # Add recemnt messages for preview
    context['recent_sent_mesages'] = Message.objects.filter(sender=user).select_related('receiver')[:5]
    context['recent_received_messages'] = Message.objects.filter(receiver = user).select_related('sender')[:5]
    context['recent_notifications'] = Notification.objects.filter(user = user).select_related('message_sender')[:5]
    return render(request,'messaging/user_dta)summary.html',context)


