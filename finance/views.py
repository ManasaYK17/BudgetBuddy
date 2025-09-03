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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

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
			# Delete all past expenses for this user
			Expense.objects.filter(user=request.user).delete()
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
	# Ensure static/finance/analytics directory exists
	static_dir = os.path.join(os.getcwd(), 'static', 'finance', 'analytics')
	os.makedirs(static_dir, exist_ok=True)
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

	# Generate pie chart

	pie_path = os.path.join('finance', 'analytics', f'pie_{request.user.id}.png')
	pie_full_path = os.path.join(static_dir, f'pie_{request.user.id}.png')
	# Creative pie chart
	plt.figure(figsize=(5,5))
	if chart_data:
		colors = ['#4f5bd5', '#00b894', '#fdcb6e', '#e17055', '#0984e3', '#6c5ce7', '#fab1a0', '#636e72']
		explode = [0.05]*len(chart_data)
		wedges, texts, autotexts = plt.pie(chart_data, labels=chart_labels, autopct='%1.1f%%', colors=colors[:len(chart_data)], explode=explode, startangle=140, wedgeprops={'edgecolor':'#fff','linewidth':2})
		plt.setp(autotexts, size=13, weight='bold', color='#2a2f4a')
		plt.setp(texts, size=12)
		plt.title('Expenses by Description', fontsize=15, color='#4f5bd5', pad=18)
		plt.tight_layout()
		plt.savefig(pie_full_path, bbox_inches='tight', transparent=True)
	plt.close()

	# Creative line chart
	line_path = os.path.join('finance', 'analytics', f'line_{request.user.id}.png')
	line_full_path = os.path.join(static_dir, f'line_{request.user.id}.png')
	plt.figure(figsize=(7,4))
	if line_data:
		plt.plot(line_labels, line_data, marker='o', color='#00b894', linewidth=3, markersize=8)
		plt.title('Daily Expense Over Time', fontsize=15, color='#4f5bd5', pad=12)
		plt.xlabel('Date', fontsize=12)
		plt.ylabel('Amount', fontsize=12)
		plt.xticks(rotation=0, fontsize=11)
		plt.yticks(fontsize=11)
		plt.grid(True, linestyle='--', alpha=0.3)
		plt.tight_layout()
		plt.savefig(line_full_path, bbox_inches='tight', transparent=True)
	plt.close()

	return render(request, 'finance/analytics.html', {
		'total_spent': total_spent,
		'pie_chart_url': f'/static/{pie_path}',
		'line_chart_url': f'/static/{line_path}',
		'chart_labels': chart_labels,
		'chart_data': chart_data,
	})
