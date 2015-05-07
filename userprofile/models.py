from datetime import date, timedelta
import logging
logger = logging.getLogger(__name__)

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

from registration.signals import user_registered

from groupaccount.models import GroupAccount
import base.emailserver as emailserver


def create_userprofile(sender, user, request, **kwargs):
    logger.debug('signal create_userprofile()')
    profile = UserProfile(user=user, displayname=user.username)
    if NotificationInterval.objects.get(name="Monthly"):
        profile.historyEmailInterval = NotificationInterval.objects.get(name="Monthly")
    profile.save()
    emailserver.send_welcome_email(user.username, user.email)

# create a new userprofile when a user registers
user_registered.connect(create_userprofile)


class NotificationInterval(models.Model):
    name = models.CharField(max_length=100, unique=True)
    days = models.IntegerField()

    def __str__(self):
        return str(self.name)


class UserProfile(models.Model):
    user = models.ForeignKey(User)
    displayname = models.CharField(max_length=15, validators=[RegexValidator(r"^\S.*\S$|^\S$|^$", "This field cannot start or end with spaces.")])
    firstname = models.CharField(max_length=100, blank=True)
    lastname = models.CharField(max_length=100, blank=True)
    group_accounts = models.ManyToManyField(GroupAccount, blank=True)
    showTableView = models.BooleanField(default=False)
    historyEmailInterval = models.ForeignKey(NotificationInterval, null=True)

    def __str__(self):
        return str(self.displayname)

    def get_show_table(self, do_show_table):
        if int(do_show_table) == 1 and self.showTableView:
            self.showTableView = False
            self.save()
        if int(do_show_table) == 2 and not self.showTableView:
            self.showTableView = True
            self.save()

    def send_transaction_history(self, force_send=False):
        if self.historyEmailInterval.days == 0 and not force_send:
            return # do not send anything when it is not forced and user set to 0 days
        date_end = date.today()
        date_start = date_end - timedelta(self.historyEmailInterval.days)
        import base.mailnotification as mailnotification
        transaction_table_html = mailnotification.create_transaction_history_table_html(self, date_start, date_end)
        transaction_real_table = mailnotification.create_transaction_real_history_table_html(self, date_start, date_end)

        if transaction_table_html == '' and transaction_real_table == '':
            return
        emailserver.send_transaction_history(self.user.username, self.user.email, transaction_table_html, transaction_real_table, date_start, date_end)

    @staticmethod
    def get_balance(group_account_id, user_profile_id):
        from transaction.models import Transaction
        from transaction.models import TransactionReal
        buyer_transactions = Transaction.objects.filter(group_account__id=group_account_id, buyer__id=user_profile_id)
        consumer_transactions = Transaction.objects.filter(group_account__id=group_account_id, consumers__id=user_profile_id)
        sender_real_transactions = TransactionReal.objects.filter(group_account__id=group_account_id, sender__id=user_profile_id)
        receiver_real_transactions = TransactionReal.objects.filter(group_account_id=group_account_id, receiver__id=user_profile_id)

        total_bought = 0.0
        total_consumed = 0.0
        total_sent = 0.0
        total_received = 0.0

        for transaction in buyer_transactions:
            total_bought += float(transaction.amount)

        for transaction in consumer_transactions:
            n_consumers = transaction.consumers.count()
            total_consumed += float(transaction.amount) / n_consumers

        for transaction in sender_real_transactions:
            total_sent += float(transaction.amount)

        for transaction in receiver_real_transactions:
            total_received += float(transaction.amount)

        balance = (total_bought + total_sent - total_consumed - total_received)
        return balance
