from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Expense(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	date = models.DateField(default=timezone.now)
	description = models.CharField(max_length=255, blank=True)
	def __str__(self):
		return f"{self.user.username} - {self.amount} on {self.date}"

class Budget(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	month = models.DateField()
	def __str__(self):
		return f"{self.user.username} - {self.month}"

class FinancialGoal(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	name = models.CharField(max_length=100)
	target_amount = models.DecimalField(max_digits=10, decimal_places=2)
	current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	deadline = models.DateField()
	def __str__(self):
		return f"{self.user.username} - {self.name}"
