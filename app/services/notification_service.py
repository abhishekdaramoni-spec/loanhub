from app.utils.extensions import db
from app.models.notification import Notification

class NotificationService:
    @staticmethod
    def notify(user_id, message_text):
        """
        Creates and stores a notification.
        """
        notif = Notification(user_id=user_id, message=message_text)
        db.session.add(notif)
        db.session.commit()
        return notif

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """
        Marks a notification as read after validating ownership.
        """
        notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notif:
            notif.is_read = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_unread_count(user_id):
        """
        Counts unread notifications.
        """
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def get_recent(user_id, limit=5):
        """
        Retrieves the latest notifications.
        """
        return Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(limit).all()
