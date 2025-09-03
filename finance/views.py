from django.db import models
import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.contrib.auth.decorators import login_required
from .models import Expense, Budget, FinancialGoal
from django.utils import timezone
from collections import defaultdict

# Expense entry form
class ExpenseForm(forms.ModelForm):
	class Meta:
		model = Expense
		fields = ['amount', 'date', 'description']

# Budget setup form
class BudgetForm(forms.ModelForm):
	class Meta:
		model = Budget
		fields = ['amount', 'month']

# Daily limit form
class DailyLimitForm(forms.Form):
	amount = forms.DecimalField(max_digits=10, decimal_places=2, label='Set Daily Limit')

# Financial goal form
class FinancialGoalForm(forms.ModelForm):
	class Meta:
		model = FinancialGoal
		fields = ['name', 'target_amount', 'deadline']

def logout(request):
	auth_logout(request)
	return redirect('login')

def home(request):
	return render(request, 'finance/home.html')

def user_login(request):
	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			return redirect('dashboard')
	else:
		form = AuthenticationForm()
	return render(request, 'finance/login.html', {'form': form})

def register(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect('login')
	else:
		form = UserCreationForm()
	return render(request, 'finance/register.html', {'form': form})

@login_required
def add_expense(request):
	if request.method == 'POST':
		form = ExpenseForm(request.POST)
		if form.is_valid():
			expense = form.save(commit=False)
			expense.user = request.user
			expense.save()
			return redirect('dashboard')
		# If form is invalid, show the form with errors
		return render(request, 'finance/add_expense.html', {'form': form})
	else:
		form = ExpenseForm()
		return render(request, 'finance/add_expense.html', {'form': form})

@login_required
def set_budget(request):
	if request.method == 'POST':
		form = BudgetForm(request.POST)
		if form.is_valid():
			budget = form.save(commit=False)
			budget.user = request.user
			budget.save()
			return redirect('dashboard')
	else:
		form = BudgetForm()
	return render(request, 'finance/set_budget.html', {'form': form})

@login_required
def add_goal(request):
	if request.method == 'POST':
		form = FinancialGoalForm(request.POST)
		if form.is_valid():
			goal = form.save(commit=False)
			goal.user = request.user
			goal.save()
			return redirect('dashboard')
	else:
		form = FinancialGoalForm()
	return render(request, 'finance/add_goal.html', {'form': form})

@login_required
def dashboard(request):
	today = timezone.now().date()
	expenses_today = Expense.objects.filter(user=request.user, date=today)
	total_today = expenses_today.aggregate(models.Sum('amount'))['amount__sum'] or 0
	daily_limit = request.session.get('daily_limit', None)
	limit_exceeded = False
	show_balance = request.GET.get('show_balance', None)
	if show_balance == '1':
		show_balance = True
	else:
		show_balance = False
	show_expenses = request.GET.get('show_expenses', False)
	balance = None
	if daily_limit is not None:
		limit_exceeded = total_today > float(daily_limit)
		if show_balance:
			balance = float(daily_limit) - float(total_today)
	if request.method == 'POST':
		form = DailyLimitForm(request.POST)
		if form.is_valid():
			# Delete all expenses except today's for this user
			Expense.objects.filter(user=request.user).exclude(date=today).delete()
			request.session['daily_limit'] = float(form.cleaned_data['amount'])
			request.session['limit_set_date'] = str(today)
			daily_limit = float(form.cleaned_data['amount'])
			limit_exceeded = total_today > daily_limit
	else:
		form = DailyLimitForm(initial={'amount': daily_limit} if daily_limit else None)
	return render(request, 'finance/dashboard.html', {
		'form': form,
		'add_expense_url': 'add_expense',
		'limit_exceeded': limit_exceeded,
		'daily_limit': daily_limit,
		'balance': balance,
		'show_balance': show_balance,
		'show_expenses': show_expenses,
		'total_today': total_today,
		'expenses_today': expenses_today,
	})

@login_required
def analytics(request):
	daily_limit = request.session.get('daily_limit', None)
	limit_set_date = request.session.get('limit_set_date', None)
	if not limit_set_date:
		expenses = Expense.objects.filter(user=request.user)
	else:
		expenses = Expense.objects.filter(user=request.user, date__gte=limit_set_date)
	desc_totals = defaultdict(float)
	for e in expenses:
		desc_totals[e.description] += float(e.amount)
	chart_labels = list(desc_totals.keys())
	chart_data = list(desc_totals.values())
	date_totals = defaultdict(float)
	for e in expenses:
		date_totals[str(e.date)] += float(e.amount)
	line_labels = list(date_totals.keys())
	line_data = list(date_totals.values())
	total_spent = expenses.aggregate(models.Sum('amount'))['amount__sum'] or 0
	return render(request, 'finance/analytics.html', {
		'total_spent': total_spent,
		'chart_labels': json.dumps(chart_labels),
		'chart_data': json.dumps(chart_data),
		'line_labels': json.dumps(line_labels),
		'line_data': json.dumps(line_data),
	})
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# Logout view
from django import forms
from django.contrib.auth.decorators import login_required
from .models import Expense, Budget, FinancialGoal

# Expense entry form
class ExpenseForm(forms.ModelForm):
	class Meta:
		model = Expense
		fields = ['amount', 'date', 'description']

# Budget setup form
class BudgetForm(forms.ModelForm):
	class Meta:
		model = Budget
		fields = ['amount', 'month']

# Daily limit form
class DailyLimitForm(forms.Form):
	amount = forms.DecimalField(max_digits=10, decimal_places=2, label='Set Daily Limit')

# Financial goal form
class FinancialGoalForm(forms.ModelForm):
	class Meta:
		model = FinancialGoal
		fields = ['name', 'target_amount', 'deadline']

def logout(request):
	auth_logout(request)
	return redirect('login')

def home(request):
	return render(request, 'finance/home.html')

def user_login(request):
	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			return redirect('dashboard')
	else:
		form = AuthenticationForm()
	return render(request, 'finance/login.html', {'form': form})

def register(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect('login')
	else:
		form = UserCreationForm()
	return render(request, 'finance/register.html', {'form': form})
## Duplicate and incomplete add_expense view removed
@login_required
def set_budget(request):
	if request.method == 'POST':
		form = BudgetForm(request.POST)
@login_required
def add_goal(request):
	if request.method == 'POST':
		form = FinancialGoalForm(request.POST)

# Dashboard view

# Expense entry form
class ExpenseForm(forms.ModelForm):
	class Meta:
		model = Expense
		fields = ['amount', 'date', 'description']

@login_required

# Budget setup form
class BudgetForm(forms.ModelForm):
	class Meta:
		model = Budget
		fields = ['amount', 'month']

# Daily limit form
class DailyLimitForm(forms.Form):
	amount = forms.DecimalField(max_digits=10, decimal_places=2, label='Set Daily Limit')

@login_required
def dashboard(request):
	today = timezone.now().date()
	expenses_today = Expense.objects.filter(user=request.user, date=today)
	total_today = expenses_today.aggregate(models.Sum('amount'))['amount__sum'] or 0
	daily_limit = request.session.get('daily_limit', None)
	limit_exceeded = False
	show_balance = request.GET.get('show_balance', None)
	if show_balance == '1':
		show_balance = True
	else:
		show_balance = False
	show_expenses = request.GET.get('show_expenses', False)
	balance = None
	if daily_limit is not None:
		limit_exceeded = total_today > float(daily_limit)
		if show_balance:
			balance = float(daily_limit) - float(total_today)
	if request.method == 'POST':
		form = DailyLimitForm(request.POST)
		if form.is_valid():
			# Delete all expenses except today's for this user
			Expense.objects.filter(user=request.user).exclude(date=today).delete()
			request.session['daily_limit'] = float(form.cleaned_data['amount'])
			request.session['limit_set_date'] = str(today)
			daily_limit = float(form.cleaned_data['amount'])
			limit_exceeded = total_today > daily_limit
	else:
		form = DailyLimitForm(initial={'amount': daily_limit} if daily_limit else None)
	return render(request, 'finance/dashboard.html', {
		'form': form,
		'add_expense_url': 'add_expense',
		'limit_exceeded': limit_exceeded,
		'daily_limit': daily_limit,
		'balance': balance,
		'show_balance': show_balance,
		'show_expenses': show_expenses,
		'total_today': total_today,
		'expenses_today': expenses_today,
	})

@login_required

# Financial goal form
class FinancialGoalForm(forms.ModelForm):
	class Meta:
		model = FinancialGoal
		fields = ['name', 'target_amount', 'deadline']

@login_required

# Analytics view


@login_required
def analytics(request):
	# Find the latest daily limit set by the user (from session)
	daily_limit = request.session.get('daily_limit', None)
	# Find the date when the limit was last set (assume session start)
	limit_set_date = request.session.get('limit_set_date', None)
	if not limit_set_date:
		# fallback: show all expenses
		expenses = Expense.objects.filter(user=request.user)
	else:
		expenses = Expense.objects.filter(user=request.user, date__gte=limit_set_date)

	# Group expenses by description for pie chart
	from collections import defaultdict
	desc_totals = defaultdict(float)
	for e in expenses:
		desc_totals[e.description] += float(e.amount)

	# Prepare data for chart.js
	chart_labels = list(desc_totals.keys())
	chart_data = list(desc_totals.values())

	# For line chart: expenses by date after limit
	date_totals = defaultdict(float)
	for e in expenses:
		date_totals[str(e.date)] += float(e.amount)
	line_labels = list(date_totals.keys())
	line_data = list(date_totals.values())

	total_spent = expenses.aggregate(models.Sum('amount'))['amount__sum'] or 0
	return render(request, 'finance/analytics.html', {
		'total_spent': total_spent,
		'chart_labels': json.dumps(chart_labels),
		'chart_data': json.dumps(chart_data),
		'line_labels': json.dumps(line_labels),
		'line_data': json.dumps(line_data),
	})

# Create your views here.
