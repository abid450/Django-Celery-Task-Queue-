import logging
from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import datetime, timedelta
from .models import User, EmailVerification, VerificationLog

logger = logging.getLogger(__name__)


# ============= Core Email Tasks =============

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email(self, user_id, verification_code):
    """
    Send verification email to user (runs in background with Celery)
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = 'Verify Your Email Address'
        
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .code {{ font-size: 36px; font-weight: bold; color: #4CAF50; 
                         letter-spacing: 5px; text-align: center; padding: 20px; 
                         background: white; border-radius: 10px; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #4CAF50; 
                          color: white; text-decoration: none; border-radius: 5px; }}
                .footer {{ margin-top: 30px; text-align: center; font-size: 12px; color: #999; }}
                .warning {{ color: #ff9800; font-size: 12px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔐 Email Verification</h2>
                </div>
                <div class="content">
                    <p>Hello <strong>{user.username}</strong>,</p>
                    <p>Thank you for registering! Please verify your email address by entering the code below:</p>
                    
                    <div class="code">
                        {verification_code}
                    </div>
                    
                    <p>This code will expire in <strong>{settings.VERIFICATION_CODE_EXPIRY_MINUTES} minutes</strong>.</p>
                    
                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply.</p>
                    <p>&copy; 2024 Email Verification System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Hello {user.username},
        
        Thank you for registering! Your verification code is: {verification_code}
        
        This code will expire in {settings.VERIFICATION_CODE_EXPIRY_MINUTES} minutes.
        
        If you didn't create an account, please ignore this email.
        
        ---
        This is an automated message, please do not reply.
        """
        
        # Send email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        # Log successful email send
        VerificationLog.objects.create(
            user=user,
            action='send_verification',
            status='success',
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return {
            'status': 'success',
            'message': f'Verification email sent to {user.email}',
            'user_id': user_id
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'status': 'failed', 'error': 'User not found'}
        
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        
        # Log failure
        try:
            user = User.objects.get(id=user_id)
            VerificationLog.objects.create(
                user=user,
                action='send_verification',
                status='failed',
                error_message=str(e)
            )
        except:
            pass
        
        # Retry the task
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_welcome_email(self, user_id):
    """
    Send welcome email after successful verification
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = '🎉 Welcome to Our Platform!'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #2196F3; 
                          color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Welcome Aboard! 🎉</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>{user.username}</strong>,</p>
                    <p>Your email has been successfully verified!</p>
                    <p>Welcome to our platform. We're excited to have you on board.</p>
                    <p>You can now:</p>
                    <ul>
                        <li>Access all features</li>
                        <li>Update your profile</li>
                        <li>Connect with other users</li>
                    </ul>
                    <p>Best regards,<br>The Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Our Platform!
        
        Dear {user.username},
        
        Your email has been successfully verified!
        
        Welcome aboard!
        
        Best regards,
        The Team
        """
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        return {'status': 'success', 'message': f'Welcome email sent to {user.email}'}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'status': 'failed', 'error': 'User not found'}
        
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        raise self.retry(exc=e, countdown=30)


# ============= Cleanup Tasks =============

@shared_task
def cleanup_expired_verifications():
    """
    Periodic task to clean up expired verifications
    """
    try:
        expired = EmailVerification.objects.filter(
            expired_at__lte=timezone.now(),
            status__in=['pending', 'failed']
        )
        
        count = expired.count()
        expired.update(status='expired')
        
        logger.info(f"Cleaned up {count} expired verifications")
        return {
            'status': 'success',
            'cleaned_up': count,
            'message': f'Successfully cleaned up {count} expired verifications'
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired verifications: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def cleanup_old_logs():
    """
    Clean up old verification logs (older than 30 days)
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = VerificationLog.objects.filter(created_at__lte=cutoff_date).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old logs")
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'message': f'Cleaned up {deleted_count} logs older than 30 days'
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= Report Tasks =============

@shared_task
def send_daily_report():
    """
    Send daily email report to admin
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        # Get statistics
        new_users = User.objects.filter(date_joined__range=(today_start, today_end)).count()
        verified_users = User.objects.filter(email_verified_at__range=(today_start, today_end)).count()
        total_users = User.objects.count()
        verified_total = User.objects.filter(is_email_verified=True).count()
        
        pending_verifications = EmailVerification.objects.filter(
            status='pending',
            is_used=False
        ).count()
        
        subject = f'📊 Daily Report - {today}'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .stats {{ background: #f4f4f4; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Daily Report - {today}</h2>
                </div>
                <div class="stats">
                    <h3>Today's Statistics</h3>
                    <p>📝 New Registrations: <span class="stat-number">{new_users}</span></p>
                    <p>✅ Email Verified Today: <span class="stat-number">{verified_users}</span></p>
                </div>
                <div class="stats">
                    <h3>Overall Statistics</h3>
                    <p>👥 Total Users: <span class="stat-number">{total_users}</span></p>
                    <p>🔐 Verified Users: <span class="stat-number">{verified_total}</span></p>
                    <p>⏳ Pending Verifications: <span class="stat-number">{pending_verifications}</span></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Daily Report - {today}
        =====================
        
        Today's Statistics:
        - New Registrations: {new_users}
        - Email Verified Today: {verified_users}
        
        Overall Statistics:
        - Total Users: {total_users}
        - Verified Users: {verified_total}
        - Pending Verifications: {pending_verifications}
        """
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Daily report sent for {today}")
        return {
            'status': 'success',
            'date': str(today),
            'stats': {
                'new_users': new_users,
                'verified_users': verified_users,
                'total_users': total_users,
                'verified_total': verified_total,
                'pending_verifications': pending_verifications
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to send daily report: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= Processing Tasks =============

@shared_task
def process_pending_emails():
    """
    Process and check pending email verifications
    """
    try:
        # Get pending verifications that are about to expire (within 5 minutes)
        warning_threshold = timezone.now() + timedelta(minutes=5)
        
        about_to_expire = EmailVerification.objects.filter(
            status='pending',
            is_used=False,
            expired_at__lte=warning_threshold,
            expired_at__gte=timezone.now()
        )
        
        expire_count = about_to_expire.count()
        
        # Get total pending
        total_pending = EmailVerification.objects.filter(
            status='pending',
            is_used=False
        ).count()
        
        logger.info(f"Pending verifications: {total_pending}, About to expire: {expire_count}")
        
        return {
            'status': 'success',
            'total_pending': total_pending,
            'about_to_expire': expire_count,
            'message': f'Found {total_pending} pending verifications'
        }
        
    except Exception as e:
        logger.error(f"Failed to process pending emails: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= Test/Debug Tasks =============

@shared_task
def test_email_task():
    """
    Simple test task to check if Celery is working
    """
    logger.info("Test task executed successfully!")
    return {
        'status': 'success',
        'message': 'Celery is working properly!',
        'timestamp': str(timezone.now())
    }


@shared_task
def send_test_email(email_address):
    """
    Send a test email to verify email configuration
    """
    try:
        subject = 'Celery Test Email'
        message = f"""
        Hello,
        
        This is a test email from Celery.
        If you received this, your Celery + Email configuration is working properly!
        
        Timestamp: {timezone.now()}
        
        Best regards,
        Celery Worker
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email_address],
            fail_silently=False,
        )
        
        logger.info(f"Test email sent to {email_address}")
        return {'status': 'success', 'message': f'Test email sent to {email_address}'}
        
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= Batch Processing Tasks =============

@shared_task
def send_bulk_verification_emails(user_ids, verification_codes):
    """
    Send verification emails to multiple users (batch processing)
    """
    results = {
        'success': [],
        'failed': [],
        'total': len(user_ids)
    }
    
    for i, user_id in enumerate(user_ids):
        try:
            result = send_verification_email.delay(user_id, verification_codes[i])
            results['success'].append({
                'user_id': user_id,
                'task_id': result.id
            })
        except Exception as e:
            results['failed'].append({
                'user_id': user_id,
                'error': str(e)
            })
    
    logger.info(f"Bulk email sent: {len(results['success'])} success, {len(results['failed'])} failed")
    return results


@shared_task
def cleanup_all_expired():
    """
    Comprehensive cleanup of all expired data
    """
    try:
        # Clean expired verifications
        expired_verifications = EmailVerification.objects.filter(
            expired_at__lte=timezone.now()
        )
        verifications_count = expired_verifications.count()
        expired_verifications.update(status='expired')
        
        # Clean old logs (90 days)
        cutoff_date = timezone.now() - timedelta(days=90)
        logs_count = VerificationLog.objects.filter(created_at__lte=cutoff_date).delete()[0]
        
        logger.info(f"Cleanup completed: {verifications_count} verifications, {logs_count} logs")
        
        return {
            'status': 'success',
            'expired_verifications': verifications_count,
            'deleted_logs': logs_count,
            'timestamp': str(timezone.now())
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}